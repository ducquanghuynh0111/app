let csrf = "";
let me = null;
let state = {};
let bulkCountState = null;
let zoneState = {config:null, live:null, demo:false};
let zoneShiftState = null;
const $ = (selector) => document.querySelector(selector);
const all = (selector) => Array.from(document.querySelectorAll(selector));
const esc = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const vnd = (n) => n == null ? "—" : Number(n).toLocaleString("vi-VN") + " ₫";
const qty = (n) => n == null ? "—" : Number(n).toLocaleString("vi-VN");
const dt = (s) => s ? new Date(s).toLocaleString("vi-VN") : "—";
const groupName = {beer:"Bia",liquor:"Rượu",soft_drink:"Nước ngọt",water:"Nước uống",tobacco:"Thuốc",rice_paper:"Bánh tráng",peanuts:"Đậu phộng",ingredient:"Nguyên liệu",sauce:"Nước chấm",spice:"Gia vị",dry_good:"Đồ khô",vegetable:"Rau",ice:"Đá",coal:"Than",other:"Khác"};
const zoneGroupName = {beer:"Bia",liquor:"Rượu",water:"Nước",rice_paper:"Bánh tráng",peanuts:"Đậu phộng",tobacco:"Thuốc"};
const saleableGroups = ["beer","liquor","soft_drink","water","tobacco","rice_paper","peanuts"];
const stockSections = [
  {key:"beer", label:"Bia", groups:["beer"], defaultGroup:"beer"},
  {key:"liquor", label:"Rượu", groups:["liquor"], defaultGroup:"liquor"},
  {key:"drinks", label:"Nước", groups:["soft_drink","water"], defaultGroup:"soft_drink"},
  {key:"extras", label:"Đồ ăn kèm", groups:["rice_paper","peanuts"], defaultGroup:"rice_paper"},
  {key:"tobacco", label:"Thuốc", groups:["tobacco"], defaultGroup:"tobacco"},
];
const stockSectionFor = (group) => stockSections.find((section) => section.groups.includes(group));
const stockContainer = (group) => group === "tobacco" ? "cây" : "thùng";
const orderedStockItems = (items) => [...items].sort((a,b) =>
  stockSections.indexOf(stockSectionFor(a.group ?? a.group_name)) - stockSections.indexOf(stockSectionFor(b.group ?? b.group_name)) ||
  a.name.localeCompare(b.name,"vi"));
const roleName = {owner:"Chủ quán",manager:"Quản lý",cashier:"Thu ngân",stock:"Kho/bếp",staff:"Nhân viên"};
const departmentName = {management:"Quản lý",service:"Phục vụ",kitchen:"Bếp",runner:"Tiếp thực",cashier:"Thu ngân",other:"Khác"};

function message(text, error=false) {
  const box = $("#message");
  box.textContent = text;
  box.className = error ? "error" : "";
  box.style.display = "block";
  clearTimeout(message.timer);
  message.timer = setTimeout(() => box.style.display = "none", 5000);
}

async function api(path, method="GET", data=null) {
  const options = {method, credentials:"same-origin", headers:{}};
  if (data !== null) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(data);
  }
  if (method !== "GET" && csrf) options.headers["X-CSRF-Token"] = csrf;
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Không thực hiện được");
  return result;
}

function showAuth(setup) {
  $("#auth").hidden = false;
  $("#workspace").hidden = true;
  $("#setup").hidden = !setup;
  $("#login").hidden = setup;
  $("#identity").innerHTML = "";
}

async function load() {
  const status = await api("/api/status");
  if (status.setup_required) return showAuth(true);
  try {
    const profile = await api("/api/me");
    me = profile.user;
    csrf = profile.csrf;
    $("#auth").hidden = true;
    $("#workspace").hidden = false;
    $("#identity").innerHTML = "<span>" + esc(me.name) + " · " + esc(roleName[me.role]) + "</span><button id='logout'>Thoát</button>";
    $("#logout").onclick = async () => {
      await api("/api/logout", "POST", {});
      csrf = "";
      me = null;
      showAuth(false);
    };
    all("nav button").forEach((button) => {
      const tab = button.dataset.tab;
      button.hidden = me.role === "staff" ? !["people","process"].includes(tab) : (
        (me.role === "cashier" && (tab === "inventory" || tab === "import")) ||
        (me.role === "stock" && tab === "cash") ||
        (["zones","statistics"].includes(tab) && !["owner","manager"].includes(me.role))
      );
    });
    all(".manager").forEach((el) => el.hidden = !["owner","manager"].includes(me.role));
    const managerOption = document.querySelector('select[name="role"] option[value="manager"]');
    if (managerOption) managerOption.hidden = me.role !== "owner";
    all(".incident-entry").forEach((el) => el.hidden = !["owner","manager","cashier"].includes(me.role));
    if (me.role === "staff") selectTab("process");
    await refresh();
  } catch (err) {
    showAuth(false);
  }
}

function selectTab(name) {
  const navigationButton = all("nav button").find((button) => button.dataset.tab === name);
  if (!navigationButton || navigationButton.disabled || navigationButton.hidden) return;
  all(".tab").forEach((tab) => tab.hidden = tab.id !== name);
  all("nav button").forEach((button) => button.classList.toggle("active", button.dataset.tab === name));
  if (name === "import" && me && ["owner","manager","stock"].includes(me.role)) {
    refreshCukcuk().catch((error) => message(error.message, true));
  }
  if (name === "zones" && me && ["owner","manager"].includes(me.role)) {
    const dayInput = $("#zone-shift-form input[name='day']");
    if (!dayInput.value) dayInput.value = businessDayLocal();
    loadZoneShift(dayInput.value).catch((error) => $("#zone-shift-status").textContent = error.message);
    if (zoneState.demo) renderZoneConfig(zoneState.config);
    else refreshZoneConfig().then(() => refreshZoneReview()).catch((error) => {
      $("#zone-review-status").textContent = error.message;
    });
  }
  if (name === "statistics" && me && ["owner","manager"].includes(me.role)) {
    loadStatisticsZones().catch((error) => { $("#zone-statistics-status").textContent = error.message; });
  }
  if (name === "inventory" && me && ["owner","manager","stock"].includes(me.role)) {
    const dateInput = document.querySelector('form[data-action="bulk-count-load"] input[name="day"]');
    dateInput.value = todayLocal();
    dateInput.min = todayLocal();
    dateInput.max = todayLocal();
    const form = document.querySelector('form[data-action="bulk-count-load"]');
    loadBulkCount(form.elements.day.value || todayLocal(), form.elements.phase.value).catch((error) => $("#bulk-count-status").textContent = error.message);
    const historyForm = $("#saleable-history-filter");
    if (!historyForm.elements.anchor.value) historyForm.elements.anchor.value = businessDayLocal();
    loadSaleableHistory(historyForm.elements.period.value,historyForm.elements.anchor.value)
      .catch((error) => $("#saleable-history-status").textContent = error.message);
  }
}

function todayLocal() {
  const d = new Date();
  return [d.getFullYear(),String(d.getMonth()+1).padStart(2,"0"),String(d.getDate()).padStart(2,"0")].join("-");
}

function businessDayLocal() {
  const d = new Date(Date.now()-5*60*60*1000);
  return [d.getFullYear(),String(d.getMonth()+1).padStart(2,"0"),String(d.getDate()).padStart(2,"0")].join("-");
}

function table(headers, rows) {
  if (!rows.length) return "<p class='muted'>-</p>";
  const head = headers.map((x) => "<th>" + esc(x) + "</th>").join("");
  const body = rows.map((row) => "<tr>" + row.map((x) => "<td>" + esc(x) + "</td>").join("") + "</tr>").join("");
  return "<div class='table-wrap'><table><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table></div>";
}

function selectOptions(selector, rows, label, empty=false) {
  all('[data-select="' + selector + '"]').forEach((select) => {
    const previous = select.value;
    select.innerHTML = (empty ? "<option value=''>Không chỉ định</option>" : "") +
      rows.map((r) => "<option value='" + esc(r.id) + "'>" + esc(label(r)) + "</option>").join("");
    if (rows.some((r) => String(r.id) === previous)) select.value = previous;
  });
}

function lateStatus(shift) {
  if (!shift.checked_in_at) return "Chưa chấm vào";
  const minutes = Math.round((new Date(shift.checked_in_at) - new Date(shift.starts_at)) / 60000);
  return minutes > 5 ? "Muộn " + minutes + " phút" : "Đúng giờ";
}

async function refresh() {
  state = await api("/api/dashboard");
  const cash = state.cash_shifts || [];
  const items = state.items || [];
  const counts = state.counts || [];
  const work = state.work_shifts || [];
  const incidents = state.incidents || [];
  const users = state.users || [];
  selectOptions("cash", cash.filter((s) => !s.locked_at), (s) => "#" + s.id + " " + s.label);
  selectOptions("item", items.filter((i) => !["ice","coal"].includes(i.group_name)), (i) => i.code + " — " + i.name);
  selectOptions("daily-use-item", items.filter((i) => ["ice","coal"].includes(i.group_name)), (i) => i.code + " — " + i.name);
  selectOptions("count", counts.filter((c) => c.status === "pending"), (c) => "#" + c.id + " " + c.name + " (lệch " + c.difference + ")");
  selectOptions("user", users, (u) => u.name + " (" + roleName[u.role] + ")");
  selectOptions("user-optional", users, (u) => u.name, true);
  selectOptions("work", work, (w) => "#" + w.id + " " + (w.display_name || me.name || "") + " · " + dt(w.starts_at));
  selectOptions("incident", incidents.filter((i) => i.status === "open"), (i) => "#" + i.id + " · " + i.bill_ref);
  $("#work-table").innerHTML = table(["Mã","Nhân viên","Bắt đầu","Kết thúc","Vào","Ra","Đánh giá giờ vào"],
    work.map((w) => [w.id, w.display_name || me.name, dt(w.starts_at), dt(w.ends_at), dt(w.checked_in_at), dt(w.checked_out_at), lateStatus(w)]));
  if (me.role === "staff") return;
  const open = cash.filter((s) => !s.locked_at).length;
  const cashDiff = cash.filter((s) => s.difference_cash !== null && s.difference_cash !== 0).length;
  const low = items.filter((i) => i.low && !["ice","coal"].includes(i.group_name));
  const pending = counts.filter((c) => c.status === "pending");
  $("#metrics").innerHTML = [
    ["Ca chưa khóa", open], ["Ca lệch tiền", cashDiff],
    ["Hàng dưới ngưỡng", low.length], ["Kiểm kê chờ duyệt", pending.length]
  ].map((m) => "<div class='metric'><strong>" + esc(m[1]) + "</strong><span>" + esc(m[0]) + "</span></div>").join("");
  const cashRows = cash.map((s) => [s.id, s.label, dt(s.opened_at), s.source,
    vnd(s.expected_cash), vnd(s.counted_cash), vnd(s.difference_cash),
    vnd(s.expected_bank), vnd(s.difference_bank), s.locked_at ? "Đã khóa" : "Mở"]);
  const cashHeaders = ["Mã","Ca","Mở","Nguồn","TM kỳ vọng","TM đếm","Lệch TM","CK kỳ vọng","Lệch CK","Trạng thái"];
  $("#cash-summary").innerHTML = table(cashHeaders, cashRows.slice(0, 5));
  $("#cash-table").innerHTML = table(cashHeaders, cashRows);
  $("#low-stock").innerHTML = table(["Mã","Hàng","Nhóm","Tồn","Tối thiểu"],
    low.map((i) => [i.code,i.name,groupName[i.group_name],qty(i.balance),qty(i.min_stock)]));
  $("#pending-counts").innerHTML = table(["Phiếu","Hàng","Sổ","Đếm","Chênh"],
    pending.map((c) => [c.id,c.name,qty(c.book_qty),qty(c.counted_qty),qty(c.difference)]));
  $("#items-table").innerHTML = table(["Mã","Hàng","Nhóm","Đơn vị","Tồn sổ","Đã bán thủ công","Hao hụt đã ghi","Lệch kiểm kê đã duyệt"],
    items.filter((i) => !["ice","coal"].includes(i.group_name)).map((i) => [i.code,i.name,groupName[i.group_name],i.unit,qty(i.balance),qty(i.sold),qty(i.waste),qty(i.count_adjustment)]));
  const stockHeaders = ["Mã","Hàng","Nhóm","Đơn vị","Tồn sổ kho","Tối thiểu","Cảnh báo"];
  const stockRows = (groups) => items.filter((i) => groups.includes(i.group_name)).map((i) =>
    [i.code,i.name,groupName[i.group_name],i.unit,qty(i.balance),qty(i.min_stock),i.low?"Cần nhập":""]);
  $("#dry-items").innerHTML = table(stockHeaders, stockRows(["dry_good","spice","sauce"]));
  $("#vegetable-items").innerHTML = table(stockHeaders, stockRows(["vegetable"]));
  $("#counts-table").innerHTML = table(["Phiếu","Hàng","Sổ","Đếm","Chênh","Trạng thái"],
    counts.map((c) => [c.id,c.name,qty(c.book_qty),qty(c.counted_qty),qty(c.difference),c.status]));
  $("#entries-table").innerHTML = table(["Mã","Ca","Loại","Kênh","Tiền","Lý do","Chứng từ"],
    (state.entries || []).map((e) => [e.id,e.shift_id,e.kind,e.method,vnd(e.amount),e.note,e.reference]));
  $("#incident-table").innerHTML = table(["Mã","Bill","Loại","Mô tả","Giá trị","Trạng thái"],
    incidents.map((i) => [i.id,i.bill_ref,i.category,i.description,vnd(i.amount),i.status]));
  $("#staff-metrics").innerHTML = table(["Nhân viên","Bộ phận","Ca phân","Ca đã vào","Đi muộn","Sự cố đang mở"],
    (state.staff_metrics || []).map((m) => [m.name,departmentName[m.department],m.scheduled,m.attended,m.late,m.open_incidents]));
  $("#audit-table").innerHTML = table(["Thời gian","Người","Thao tác","Đối tượng","Mã","Chi tiết"],
    (state.audit || []).map((a) => [dt(a.created_at),a.actor_name,a.action,a.entity,a.entity_id,a.detail]));
}

function formData(form) {
  const obj = {};
  new FormData(form).forEach((value, key) => { if (key !== "file") obj[key] = value; });
  ["starts_at","ends_at"].forEach((key) => {
    if (obj[key]) obj[key] = new Date(obj[key]).toISOString();
  });
  return obj;
}

function parseCsv(text) {
  const rows = [];
  let row = [], field = "", quoted = false;
  text = text.replace(/^\uFEFF/, "");
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i+1] === '"') { field += '"'; i++; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field.replace(/\r$/, "")); rows.push(row); row = []; field = ""; }
    else field += c;
  }
  if (quoted) throw new Error("Dấu nháy CSV chưa đóng");
  if (field || row.length) { row.push(field.replace(/\r$/, "")); rows.push(row); }
  const headers = rows.shift();
  const expected = ["source_row_id","item_code","quantity","amount","method"];
  if (!headers || expected.some((h) => !headers.includes(h))) throw new Error("CSV thiếu cột: " + expected.join(", "));
  return rows.filter((r) => r.some((v) => v.trim())).map((r, index) => {
    if (r.length !== headers.length) throw new Error("Dòng " + (index + 2) + " sai số cột");
    return Object.fromEntries(headers.map((h, i) => [h, r[i].trim()]));
  });
}

async function submit(form) {
  const action = form.dataset.action;
  const data = formData(form);
  if (action === "bulk-count-load") return loadBulkCount(data.day, data.phase);
  if (action === "quick-item") {
    await api("/api/items", "POST", {...data, min_stock:0,
      ...(data.group_name === "liquor" ? {unit:"Chai"} : {})});
    form.reset();
    form.elements.group_name.dispatchEvent(new Event("change"));
    form.hidden = true;
    await refresh();
    await loadBulkCount(todayLocal(), document.querySelector('form[data-action="bulk-count-load"]').elements.phase.value);
    return message("Đã thêm mặt hàng vào bảng kiểm kê.");
  }
  if (["zone-create","zone-rename","zone-table"].includes(action)) {
    if (zoneState.demo) throw new Error("Dữ liệu mẫu chỉ để xem; hãy trở về dữ liệu thật để sửa.");
    if (action === "zone-create") {
      data.tables = Array.from(form.querySelectorAll("[data-new-table]")).map((input) => input.value.trim()).filter(Boolean);
    }
    await api(action === "zone-create" ? "/api/zones" :
      action === "zone-rename" ? "/api/zones/rename" : "/api/zone-tables", "POST", data);
    await refreshZoneConfig();
    if (zoneState.live) await refreshZoneReview();
    message("Đã lưu khu và bàn.");
    return;
  }
  if (action === "daily-report") return refreshDailyStock(data.day);
  if (action === "item-table-usage") return refreshItemTableUsage(data.day);
  if (action === "daily-usage-report") return refreshDailyUsage(data.from, data.to);
  if (action === "cukcuk-filter") {
    await refreshCukcuk(data.from, data.to);
    return;
  }
  if (action === "setup") {
    await api("/api/setup", "POST", data);
    message("Đã tạo tài khoản chủ quán. Hãy đăng nhập.");
    return showAuth(false);
  }
  if (action === "login") {
    await api("/api/login", "POST", data);
    await load();
    return message("Đã đăng nhập");
  }
  let path = "";
  if (action === "open-shift") path = "/api/cash-shifts";
  if (action === "update-shift") path = "/api/cash-shifts/" + data.shift_id + "/update";
  if (action === "close-shift") path = "/api/cash-shifts/" + data.shift_id + "/close";
  if (action === "cash-entry") path = "/api/cash-entries";
  if (action === "item") path = "/api/items";
  if (action === "stock-move") path = "/api/stock-moves";
  if (action === "stock-count") path = "/api/stock-counts";
  if (action === "approve-count") path = "/api/stock-counts/" + data.count_id + "/approve";
  if (action === "user") path = "/api/users";
  if (action === "kiosk-pin") path = "/api/kiosk/pins";
  if (action === "daily-count") path = "/api/daily-stock-counts";
  if (action === "daily-usage") path = "/api/daily-usage";
  if (action === "recipe") path = "/api/recipes";
  if (action === "work-shift") path = "/api/work-shifts";
  if (action === "attendance") path = "/api/work-shifts/" + data.work_shift_id + "/" + data.event;
  if (action === "incident") path = "/api/incidents";
  if (action === "resolve-incident") path = "/api/incidents/" + data.incident_id + "/resolve";
  if (action === "sales-import") {
    const file = form.querySelector('input[type="file"]').files[0];
    if (!file) throw new Error("Chọn file CSV");
    data.rows = parseCsv(await file.text());
    if (!data.rows.length) throw new Error("CSV không có dòng dữ liệu");
    path = "/api/sales-import";
  }
  if (!path) throw new Error("Thao tác không hợp lệ");
  const result = await api(path, "POST", data);
  form.reset();
  await refresh();
  if (action === "daily-count") await refreshDailyStock(data.day);
  if (action === "daily-usage") await refreshDailyUsage();
  message(action === "sales-import" ? "Đã nhập " + result.inserted + " dòng; bỏ qua " + result.skipped + " dòng trùng." : "Đã lưu thành công");
}

async function refreshDailyStock(day) {
  const report = await api("/api/daily-stock-report?day=" + encodeURIComponent(day));
  const rows = report.rows.filter((r) => saleableGroups.includes(r.group));
  const resultQty = (value) => value == null ? "-" : qty(value);
  $("#daily-stock-status").textContent =
    (rows.length && !rows[0].synced ? "Chưa đồng bộ đủ hóa đơn cho ngày kinh doanh này và sáng hôm sau; chưa thể kết luận chênh lệch. " : "") +
    (rows.some((r) => !r.has_previous_closing) ? "Chưa có tồn cuối hôm trước: tồn đầu mặc định 0. " : "") +
    (rows.some((r) => r.incoming == null || r.closing == null) ? "Dòng thiếu số nhập hoặc tồn cuối sẽ hiện dấu -; nhập 0 nếu đã kiểm và xác nhận không có hàng. " : "") +
    (rows.some((r) => r.unit_unknown) ? "Có món CUKCUK chưa rõ đơn vị bán; chưa tính chênh lệch cho món đó. " : "") +
    (day === todayLocal() && ["owner","manager"].includes(me.role) ? "Ô nền xanh có thể nhấp để sửa." : "");
  const renderStockRow = (r) => {
    const n = r.variance == null ? null : Number(r.variance);
    const level = n == null ? "" : n === 0 ? "stock-green" : Math.abs(n) > 24 ? "stock-red" : "stock-orange";
    const editable = day === todayLocal() && ["owner","manager"].includes(me.role);
    const stockCell = (value, field) => "<td>"+(editable ? inlineNumber(value, field, r.id, day) : esc(resultQty(value)))+"</td>";
    return "<tr class='"+level+"'><td>"+esc(r.name)+"</td>"+
      stockCell(r.opening,"previous_closing")+stockCell(r.incoming,"incoming")+
      [r.opening == null || r.incoming == null ? "-" : stockQty(Number(r.opening)+Number(r.incoming)),
        r.synced ? resultQty(r.sold) : "-",resultQty(r.expected),resultQty(r.closing),resultQty(r.shortage_or_damage),resultQty(r.variance)].map((x)=>"<td>"+esc(x)+"</td>").join("")+"</tr>";
  };
  const groupedRows = stockSections.map((section) => {
    const items = orderedStockItems(rows.filter((row) => section.groups.includes(row.group)));
    return items.length ? "<tr class='stock-section-row'><th colspan='9'>"+esc(section.label)+"</th></tr>"+items.map(renderStockRow).join("") : "";
  }).join("");
  $("#daily-stock-table").innerHTML = rows.length ? "<div class='table-wrap'><table><thead><tr><th>Hàng</th><th>Tồn hôm trước</th><th>Nhập hôm nay</th><th>Sau nhập</th><th>Đã bán</th><th>Tồn dự kiến</th><th>Thực tế cuối ngày</th><th>Thiếu/hỏng</th><th>Chênh lệch</th></tr></thead><tbody>" + groupedRows + "</tbody></table></div>" : "<p>Chưa có mặt hàng.</p>";
  const headers = ["Mã", "Hàng", "Đầu", "Nhập/trả", "Hao hụt/biếu", "Đã bán", "Định mức món", "Dự kiến", "Cuối", "Chênh"];
  const render = (subset) => table(headers, subset.map((r) => [r.code, r.name, qty(r.opening), qty(r.received), qty(r.waste_gift),
    qty(r.sold), r.recipe_defined ? qty(r.recipe_used) : "—", qty(r.expected), qty(r.closing), qty(r.variance)]));
  $("#dry-stock-table").innerHTML = render(report.rows.filter((r) => ["dry_good","spice","sauce"].includes(r.group)));
  $("#vegetable-stock-table").innerHTML = render(report.rows.filter((r) => r.group === "vegetable"));
}

async function loadSaleableHistory(period, anchor) {
  $("#saleable-history-status").textContent = "Đang đọc lịch sử đã lưu…";
  const report = await api("/api/saleable-history?period="+encodeURIComponent(period)+"&anchor="+encodeURIComponent(anchor));
  const labels = {no_data:"Chưa có dữ liệu",unsynced:"Chưa đồng bộ đủ hóa đơn",
    unit_unknown:"Thiếu đơn vị bán",difference:"Có chênh lệch",incomplete:"Chưa đủ số kiểm",ok:"Khớp"};
  const shown = (value) => value == null ? "-" : qty(value);
  const sections = [
    {key:"beer",label:"Bia",groups:["beer"]},
    {key:"liquor",label:"Rượu",groups:["liquor"]},
    {key:"water",label:"Nước",groups:["water","soft_drink"]},
    {key:"extras",label:"Đồ ăn kèm",groups:["rice_paper","peanuts"]},
    {key:"tobacco",label:"Thuốc",groups:["tobacco"]},
  ];
  $("#saleable-history-status").textContent = "Từ "+report.from+" đến "+report.to+
    " · đọc dữ liệu đã lưu, không tự gọi CUKCUK. Số bán chỉ tính khi đủ hóa đơn và đơn vị.";
  $("#saleable-history-days").innerHTML = report.days.map((day) => {
    const contents = day.rows.length ? sections.map((section) => {
      const products = day.rows.filter((row) => section.groups.includes(row.group));
      if (!products.length) return "";
      const rows = products.map((row) => [row.name,shown(row.opening),shown(row.incoming),
        shown(row.sold),shown(row.closing),shown(row.variance)]);
      return "<details class='saleable-history-group history-group-"+section.key+"'><summary>"+
        section.label+" <small>"+products.length+" mặt hàng</small></summary>"+
        table(["Mặt hàng","Tồn hôm trước","Nhập hôm nay","Đã bán","Tồn cuối","Chênh lệch"],rows)+"</details>";
    }).join("") :
      "<p class='muted'>Chưa có số kiểm hoặc hóa đơn đã thanh toán cho ngày này.</p>";
    const note = day.status === "unit_unknown" ? "<p class='muted'>Có mặt hàng chưa rõ đơn vị bán. Đồng bộ lại hóa đơn sau khi cập nhật phần mềm để lấy đơn vị từ CUKCUK.</p>" :
      day.status === "unsynced" ? "<p class='muted'>Cần đồng bộ hóa đơn của ngày này và sáng hôm sau trước khi đối chiếu.</p>" : "";
    const groupCount = sections.filter((section) => day.rows.some((row) => section.groups.includes(row.group))).length;
    return "<details class='saleable-history-day history-"+esc(day.status)+"'>"+
      "<summary><strong>"+esc(day.day.split("-").reverse().join("/"))+"</strong>"+
      "<span class='saleable-day-meta'>"+groupCount+" nhóm · "+day.rows.length+" mặt hàng</span>"+
      "<span class='saleable-day-status'>"+esc(labels[day.status] || "-")+"</span></summary>"+
      "<div class='saleable-history-detail'>"+note+contents+"</div></details>";
  }).join("");
}

$("#saleable-history-filter").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  loadSaleableHistory(form.elements.period.value,form.elements.anchor.value)
    .catch((error) => $("#saleable-history-status").textContent = error.message);
});

const stockQty = (value) => value == null ? "0" : qty(value);
const inlineNumber = (value, field, itemId, day) => "<input class='inline-number' type='number' min='"+(field === "carton_size" ? "1" : "0")+"' max='"+(field === "carton_size" ? "1000" : "1000000000")+"' step='1' readonly data-edit-field='"+field+"' data-item-id='"+esc(itemId)+"' data-day='"+esc(day)+"' data-value='"+esc(value ?? "")+"' value='"+esc(value ?? "")+"' placeholder='Chưa nhập' title='Nhấp để sửa'>";

const normalizeStockSearch = (value) => String(value || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d");

function filterBulkCountRows() {
  const term = normalizeStockSearch($("#bulk-count-search").value.trim());
  const items = new Map((bulkCountState?.items || []).map((item) => [item.id, item]));
  const rows = all("#bulk-count-inputs [data-bulk-row]");
  let visible = 0;
  rows.forEach((row) => {
    const item = items.get(Number(row.dataset.bulkRow));
    row.hidden = !item || !normalizeStockSearch(item.name + " " + item.code).includes(term);
    if (!row.hidden) visible++;
  });
  all("#bulk-count-inputs [data-stock-section]").forEach((section) => {
    const hasMatch = rows.some((row) => row.dataset.section === section.dataset.stockSection && !row.hidden);
    section.hidden = Boolean(term) && !hasMatch;
    if (term && hasMatch) section.open = true;
  });
  $("#bulk-count-visible-count").textContent = visible + "/" + rows.length + " mặt hàng";
}

async function loadBulkCount(day, phase) {
  if (day !== todayLocal()) throw new Error("Chỉ được nhập và kiểm hàng cho ngày hiện tại");
  const report = await api("/api/daily-stock-batch?day=" + encodeURIComponent(day) + "&phase=" + encodeURIComponent(phase));
  if (document.querySelector('form[data-action="bulk-count-load"]').elements.phase.value !== phase) return;
  bulkCountState = {day, phase, items: report.items, reviewed: null};
  $("#bulk-count-confirm").hidden = true;
  const canEditCounts = ["owner","manager"].includes(me.role);
  $("#bulk-count-entry").hidden = !report.items.length && !canEditCounts;
  updateBulkActions(phase);
  $("#bulk-count-status").textContent = !report.items.length ? "Chưa có mặt hàng." :
    (phase === "opening" ? "Nhập số thùng/cây và số lon, chai hoặc gói lẻ nhận hôm nay. Tồn đầu ngày = tồn cuối hôm trước + số vừa nhập." :
      "Nhập số thùng/cây nguyên và số lon, chai hoặc gói lẻ còn thực tế cuối ngày.") + " Để trống mặt hàng chưa kiểm; nhập 0 nếu đã kiểm và không còn hàng. Chỉ các dòng có số mới được lưu." +
    (report.legacy_count ? " Có số kiểm cũ chưa theo quy cách thùng/cây; hãy nhập lại trước khi lưu." : "") +
    (canEditCounts ? " Ô nền xanh có thể nhấp để sửa." : " Chỉ quản lý hoặc chủ quán được nhập số kho.");
  const renderRow = (item, section) => "<tr data-bulk-row='" + esc(item.id) + "' data-section='"+esc(section.key)+"'><td>" + esc(item.name) +
    "</td><td>" + (canEditCounts ? inlineNumber(item.previous_closing ?? "0","previous_closing",item.id,day) : esc(stockQty(item.previous_closing))) +
    "</td><td>" + (canEditCounts ? inlineNumber(item.units_per_carton ?? (item.group_name === "tobacco" ? 10 : 24),"carton_size",item.id,day) : esc(item.units_per_carton ?? (item.group_name === "tobacco" ? 10 : 24)))+" "+esc(item.unit)+"/"+stockContainer(item.group_name) +
    "</td><td><input type='number' min='0' step='1' " + (canEditCounts ? "" : "disabled ") + "data-bulk-item='" + esc(item.id) +
    "' value='" + esc(item.cartons == null ? "" : item.cartons) + "' placeholder='Chưa nhập'></td>" +
    "<td><input type='number' min='0' step='1' " + (canEditCounts ? "" : "disabled ") + "data-bulk-loose='" + esc(item.id) +
      "' value='" + esc(item.loose_units == null ? "" : item.loose_units) + "' placeholder='Chưa nhập' aria-label='"+esc(item.name)+" số lẻ'></td></tr>";
  const sections = stockSections.map((section) => {
    const items = orderedStockItems(report.items.filter((item) => section.groups.includes(item.group_name)));
    return "<details class='bulk-stock-group history-group-"+(section.key === "drinks" ? "water" : section.key)+"' data-stock-section='"+esc(section.key)+"'><summary><span>"+esc(section.label)+"</span><small>"+items.length+" mặt hàng</small></summary>"+
      "<div class='bulk-stock-group-content'>"+
      (canEditCounts ? "<div class='bulk-stock-group-actions'><button type='button' data-add-group='"+esc(section.defaultGroup)+"'>Thêm mới</button></div>" : "")+
      "<div class='bulk-count-scroll'><table><thead><tr><th>Hàng</th><th>Tồn hôm trước</th><th>Quy cách</th><th>Số thùng/cây</th><th>Số lẻ</th></tr></thead><tbody>"+
      items.map((item) => renderRow(item, section)).join("")+"</tbody></table></div></div></details>";
  });
  $("#bulk-count-inputs").innerHTML = sections.join("");
  filterBulkCountRows();
}

function updateBulkActions(phase) {
  const opening = phase === "opening";
  const canEditCounts = ["owner","manager"].includes(me.role);
  $("#bulk-count-opening").hidden = !opening || !canEditCounts;
  $("#bulk-count-closing").hidden = opening || !canEditCounts;
  if (!opening) $("#quick-item-form").hidden = true;
}

function reviewBulkCount() {
  if (!bulkCountState || !bulkCountState.items.length) throw new Error("Hãy lấy danh sách mặt hàng trước");
  const inputs = all("[data-bulk-item]");
  if (inputs.length !== bulkCountState.items.length || inputs.some((input) => input.value.trim() && !input.checkValidity())) {
    throw new Error("Số thùng/cây không hợp lệ");
  }
  const values = new Map(inputs.map((input) => [Number(input.dataset.bulkItem), input.value]));
  const looseInputs = all("[data-bulk-loose]");
  const expectedLoose = inputs.length;
  if (looseInputs.length !== expectedLoose || looseInputs.some((input) => input.value.trim() && !input.checkValidity())) {
    throw new Error("Số đơn vị lẻ không hợp lệ");
  }
  const looseValues = new Map(looseInputs.map((input) => [Number(input.dataset.bulkLoose), input.value]));
  const selected = bulkCountState.items.filter((item) => {
    const cartons = values.get(item.id).trim();
    const loose = (looseValues.get(item.id) || "").trim();
    if (!cartons && !loose) return false;
    return item.cartons == null || Number(cartons || 0) !== Number(item.cartons) ||
      Number(loose || 0) !== Number(item.loose_units || 0);
  });
  if (!selected.length) throw new Error("Hãy nhập hoặc sửa ít nhất một mặt hàng");
  if (selected.some((item) => Number(looseValues.get(item.id) || 0) >= item.units_per_carton)) {
    throw new Error("Số đơn vị lẻ phải nhỏ hơn quy cách mỗi thùng/cây");
  }
  if (selected.some((item) => (Number(values.get(item.id) || 0) > 0 || Number(looseValues.get(item.id) || 0) > 0) && !item.units_per_carton))
    throw new Error("Mặt hàng có số lượng lớn hơn 0 cần khai báo quy cách mỗi thùng/cây");
  bulkCountState.reviewed = selected.map((item) => ({item_id: item.id, cartons: values.get(item.id) || "0",
    loose_units: looseValues.get(item.id) || "0"}));
  $("#bulk-count-preview").innerHTML = table(["Hàng",bulkCountState.phase === "closing" ? "Số kiểm thực tế" : "Số nhập","Quy đổi"],
    selected.map((item) => [item.name,qty(values.get(item.id) || 0)+" "+stockContainer(item.group_name) +
      " + " + qty(looseValues.get(item.id)) + " " + item.unit + " lẻ",
      qty(Number(values.get(item.id) || 0)*item.units_per_carton + Number(looseValues.get(item.id) || 0))+" "+item.unit]));
  $("#bulk-count-entry").hidden = true;
  $("#bulk-count-confirm").hidden = false;
}

async function refreshDailyUsage(from, to) {
  const form = document.querySelector('form[data-action="daily-usage-report"]');
  const localDay = (d) => [d.getFullYear(), String(d.getMonth()+1).padStart(2,"0"), String(d.getDate()).padStart(2,"0")].join("-");
  const today = new Date();
  from = from || form.elements.from.value || localDay(new Date(today.getFullYear(),today.getMonth(),today.getDate()-29));
  to = to || form.elements.to.value || localDay(today);
  form.elements.from.value = from;
  form.elements.to.value = to;
  const report = await api("/api/daily-usage?from=" + encodeURIComponent(from) + "&to=" + encodeURIComponent(to));
  $("#daily-usage-table").innerHTML = table(["Ngày","Mã","Hàng","Nhóm","Đã dùng","Đơn vị","Ghi chú"],
    report.rows.map((r) => [r.day,r.code,r.name,groupName[r.group_name],qty(r.quantity),r.unit,r.note]));
}

async function refreshItemTableUsage(day) {
  const report = await api("/api/item-table-usage?day=" + encodeURIComponent(day));
  $("#item-table-usage-status").textContent = report.synced ?
    "Đã đồng bộ đủ ngày và sáng hôm sau. Số liệu là lượng trên hóa đơn đã thu, không chứng minh món đã dùng hết." :
    "Chưa đồng bộ đủ hóa đơn ngày này và sáng hôm sau; báo cáo có thể thiếu bàn hoặc số lượng.";
  $("#item-table-usage").innerHTML = report.items.length ? report.items.map((item) =>
    "<details class='usage-item'><summary>" + esc(item.name) + " (" + esc(item.code) + ") · " +
    esc(qty(item.billed_quantity)) + " " + esc(item.unit) + " đã tính tiền</summary>" +
    table(["Bàn","Đã gọi","Trả/hủy","Đã tính tiền"], item.tables.map((row) =>
      [row.table,row.ordered_quantity == null ? "-" : qty(row.ordered_quantity),row.returned_quantity == null ? "-" : qty(row.returned_quantity),qty(row.billed_quantity)])) + "</details>").join("") :
    "<p class='muted'>Chưa có hóa đơn đã thu cho các mặt hàng này.</p>";
}

function makeZoneDemo() {
  const config = {
    zones:[{id:90001,name:"Nhân viên mẫu A",active:1},{id:90002,name:"Nhân viên mẫu B",active:1}],
    tables:[
      {table_name:"16",zone_id:90001},{table_name:"2",zone_id:90001},{table_name:"1",zone_id:90001},
      {table_name:"4",zone_id:90002},{table_name:"3",zone_id:90002},
    ], assignments:[],observations:[],
  };
  const table = (number, zoneId, quantities, beerItems, missing, note, otherItems=[]) => ({
    table:"Bàn "+number, zone_id:zoneId, zone_name:config.zones.find((zone) => zone.id === zoneId).name,
    mapping_status:"mapped", quantities:{beer:"0",water:"0",soft_drink:"0",rice_paper:"0",peanuts:"0",tobacco:"0",...quantities},
    beer_items:beerItems, product_items:[...beerItems.map((item) => ({...item,group:"beer"})),...otherItems],
    missing_order_groups:missing, demo_note:note,
  });
  const live = {as_of:new Date().toISOString(),active_orders:5,tables:[
    table(1,90001,{beer:"24",tobacco:"1"},[{code:"BT",name:"Bia Tiger",quantity:"24",unit:"Lon",units_per_carton:24,unit_status:"known"}],
      ["rice_paper","peanuts"],"1 thùng Tiger (24 lon), 1 gói thuốc con ngựa; chưa gọi món kèm",
      [{code:"TNN",name:"Thuốc con ngựa",group:"tobacco",quantity:"1",unit:"Gói",units_per_carton:10,unit_status:"known"}]),
    table(2,90001,{rice_paper:"1",peanuts:"1"},[],["beer"],"Đã gọi món kèm nhưng chưa gọi bia"),
    table(16,90001,{beer:"4",water:"2",rice_paper:"1",peanuts:"1"},
      [{code:"BT",name:"Bia Tiger",quantity:"2",unit:"Lon",units_per_carton:24,unit_status:"known"},{code:"BIHE",name:"Bia Heineken",quantity:"2",unit:"Lon",units_per_carton:24,unit_status:"known"}],
      [],"Hai loại bia gọi theo lon, có đủ món kèm",
      [{code:"NS",name:"Nước suối",group:"water",quantity:"2",unit:"Chai",units_per_carton:24,unit_status:"known"}]),
    table(3,90002,{beer:"2"},[{code:"BT",name:"Bia Tiger",quantity:"2",unit:"Lon",units_per_carton:24,unit_status:"known"}],
      ["rice_paper","peanuts"],"Có bia nhưng chưa gọi bánh tráng và đậu phộng"),
    table(4,90002,{beer:"20",water:"1",soft_drink:"2",rice_paper:"1",peanuts:"1"},
      [{code:"HUCH",name:"Bia Huda chai",quantity:"20",unit:"Chai",units_per_carton:20,unit_status:"known"}],[],
      "1 thùng Huda chai (20 chai), nước và món kèm đã gọi",
      [{code:"NS",name:"Nước suối",group:"water",quantity:"1",unit:"Chai",units_per_carton:24,unit_status:"known"},
       {code:"PEPSI",name:"Pepsi",group:"water",quantity:"2",unit:"Lon",units_per_carton:24,unit_status:"known"}]),
  ]};
  return {config,live};
}

function zoneTableNumber(value) {
  const match = String(value).trim().match(/^(?:bàn\s*)?(\d+)$/i);
  return match ? (match[1].replace(/^0+/, "") || null) : null;
}

function sortZoneTableNumbers(a, b) {
  return String(a).localeCompare(String(b), "vi", {numeric:true});
}

function zoneTableRow(number, liveRow) {
  const missing = liveRow?.mapping_status === "mapped" && liveRow.missing_order_groups.length > 0;
  const note = missing ? "Thiếu order "+liveRow.missing_order_groups.map((group) => zoneGroupName[group]).join(", ") :
    !liveRow ? "Chưa mở" : liveRow.mapping_status !== "mapped" ? "Chưa đủ dữ liệu" : "Đủ order";
  return "<button type='button' class='zone-table-row "+(missing ? "missing" : "")+"' data-table-number='"+
    esc(number)+"' title='"+esc(note)+"' aria-label='Xem món của Bàn "+esc(number)+"; "+esc(note)+"'>"+
    "<strong>Bàn "+esc(number)+"</strong><span class='zone-table-state'>"+
    esc(missing ? "Thiếu order" : note)+"</span></button>";
}

function showZoneTableDialog(number) {
  const row = (zoneState.live?.tables || []).find((item) =>
    (zoneTableNumber(item.table) || String(item.table)) === (zoneTableNumber(number) || String(number)));
  const groups = [
    {label:"Bia", keys:["beer"]},
    {label:"Nước", keys:["water","soft_drink"]},
    {label:"Bánh tráng", keys:["rice_paper"]},
    {label:"Đậu phộng", keys:["peanuts"]},
    {label:"Thuốc", keys:["tobacco"]},
  ];
  const quantities = row?.quantities || {};
  const products = row?.product_items || (row?.beer_items || []).map((item) => ({...item,group:"beer"}));
  $("#zone-table-dialog-title").textContent = "Bàn "+number;
  $("#zone-table-dialog-body").innerHTML = "<p class='muted'>"+
    (row ? "Số đã order trên CUKCUK" : "Bàn chưa mở trên CUKCUK")+"</p>"+
    (row?.missing_order_groups?.length ? "<p class='zone-dialog-warning'>Thiếu order: "+
      esc(row.missing_order_groups.map((group) => zoneGroupName[group] || group).join(", "))+"</p>" : "")+
    (row?.demo_note ? "<p class='zone-demo-note'>Tình huống mẫu: "+esc(row.demo_note)+"</p>" : "")+
    groups.map((group) => {
      const listed = products.filter((item) => group.keys.includes(item.group));
      const total = group.keys.reduce((sum,key) => sum+Number(quantities[key] || 0),0);
      const details = listed.length ? listed.map((item) => "<div class='zone-dialog-item'><span>"+esc(item.name)+"</span><strong>"+
        (item.unit_status === "known" ? esc(qty(item.quantity))+" "+esc(String(item.unit || "").toLowerCase()) :
          "Chưa rõ quy cách")+"</strong></div>").join("") :
        total > 0 ? "<div class='zone-dialog-item'><span>Chưa có chi tiết món</span><strong>"+
          total.toLocaleString("vi-VN")+"</strong></div>" :
          "<div class='zone-dialog-item'><span>Chưa gọi</span><strong>0</strong></div>";
      return "<section class='zone-dialog-section'><h3>"+group.label+" <span>"+
        (row ? total.toLocaleString("vi-VN") : "0")+"</span></h3>"+details+"</section>";
    }).join("");
  $("#zone-table-dialog").showModal();
}

function renderZoneConfig(config) {
  const openEdits = new Set(all("#zone-list [data-zone-edit-panel]:not([hidden])").map((node) => node.dataset.zoneEditPanel));
  const openShiftZones = new Set(all("#zone-list details[data-after-shift-zone][open]").map((node) => node.dataset.afterShiftZone));
  const zones = config.zones.filter((zone) => zone.active);
  const live = zoneState.live ? zoneState.live.tables : [];
  const liveByNumber = new Map(live.map((row) => [zoneTableNumber(row.table),row]));
  $("#zone-list").innerHTML = zones.length ? zones.map((zone) => {
    const owned = config.tables.filter((row) => row.zone_id === zone.id)
      .sort((a,b) => sortZoneTableNumbers(a.table_name,b.table_name));
    const tableRows = owned.length ? owned.map((row) =>
      zoneTableRow(row.table_name,liveByNumber.get(zoneTableNumber(row.table_name)))).join("") :
      "<p class='muted'>Chưa thêm bàn</p>";
    const edits = owned.map((row) => "<div class='zone-table-edit'><form data-action='zone-table'>"+
      "<input type='hidden' name='zone_id' value='"+esc(zone.id)+"'><input type='hidden' name='old_table_name' value='"+esc(row.table_name)+"'>"+
      "<label>Số bàn<input name='table_name' type='number' min='1' step='1' required value='"+esc(row.table_name)+"'></label><button>Lưu</button></form>"+
      "<button type='button' class='secondary' data-remove-table='"+esc(row.table_name)+"'>Bỏ bàn</button></div>").join("");
    return "<article class='zone-card'>"+(zoneState.demo ?
      "<div class='zone-name-toggle'>"+esc(zone.name)+" <small>Dữ liệu mẫu</small></div>" :
      "<button type='button' class='zone-name-toggle' data-edit-zone='"+esc(zone.id)+"'>"+esc(zone.name)+" <small>✎ Sửa</small></button>")+
      (zoneState.demo ? "" : "<div class='zone-edit' data-zone-edit-panel='"+esc(zone.id)+"' "+(openEdits.has(String(zone.id)) ? "" : "hidden")+">"+
      "<form data-action='zone-rename'><input type='hidden' name='zone_id' value='"+esc(zone.id)+"'><label>Tên nhân viên"+
      "<input name='name' maxlength='60' required value='"+esc(zone.name)+"'></label><button>Lưu tên</button></form>"+
      edits+"<form data-action='zone-table'><input type='hidden' name='zone_id' value='"+esc(zone.id)+"'>"+
      "<label>Thêm số bàn<input name='table_name' type='number' min='1' step='1' required placeholder='Ví dụ: 101'></label><button>+ Thêm bàn</button></form></div>")+
      "<div class='zone-table-list'>"+tableRows+"</div>"+
      (zoneState.demo ? "" : zoneTobaccoControlHtml(zone))+
      (zoneState.demo ? "" : zoneAfterShiftHtml(zone.id))+"</article>";
  }).join("") : "<p class='muted'>Chưa có khu. Bấm Thêm khu để bắt đầu.</p>";
  all("#zone-list details[data-after-shift-zone]").forEach((node) => { node.open = openShiftZones.has(node.dataset.afterShiftZone); });
  const unassigned = live.filter((row) => !row.zone_id)
    .sort((a,b) => sortZoneTableNumbers(zoneTableNumber(a.table) || a.table,zoneTableNumber(b.table) || b.table));
  $("#zone-unassigned").hidden = !unassigned.length;
  $("#zone-unassigned").innerHTML = unassigned.length ? "<h2>Bàn đang mở chưa gán khu</h2><div class='zone-table-list'>"+
    unassigned.map((row) => zoneTableRow(zoneTableNumber(row.table) || row.table,row)).join("")+"</div>" : "";
}

async function refreshZoneConfig() {
  const config = await api("/api/zones");
  if (zoneState.demo) return;
  zoneState.config = config;
  renderZoneConfig(zoneState.config);
}

async function refreshZoneReview() {
  if (zoneState.demo) return;
  $("#zone-review-status").textContent = "Đang tải bàn đang mở từ CUKCUK…";
  const report = await api("/api/zone-review");
  if (zoneState.demo) return;
  zoneState.live = report;
  $("#zone-review-status").textContent = "Bàn đang mở · cập nhật "+dt(report.as_of)+". Màu đỏ là thiếu order bia hoặc bánh tráng/đậu phộng.";
  if (zoneState.config) renderZoneConfig(zoneState.config);
}

$("#zone-refresh-orders").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  try { await refreshZoneReview(); }
  catch (error) { message(error.message,true); }
  finally { button.disabled = false; }
});

async function loadStatisticsZones() {
  const config = zoneState.demo ? zoneState.config : await api("/api/zones");
  if (!zoneState.demo) zoneState.config = config;
  const select = $("#zone-statistics-form select[name='zone_id']");
  const previous = select.value;
  const zones = config.zones.filter((zone) => zone.active);
  select.innerHTML = "<option value=''>Chọn nhân viên/khu</option>"+
    zones.map((zone) => "<option value='"+esc(zone.id)+"'>"+esc(zone.name)+"</option>").join("");
  if (zones.some((zone) => String(zone.id) === previous)) select.value = previous;
  $("#zone-statistics-result").innerHTML = "";
  $("#zone-statistics-status").textContent = zones.length ?
    "Chọn khu rồi bấm Xem thống kê." : "Chưa có khu để thống kê.";
}

function showZoneStatistics(zoneId) {
  const panel = $("#zone-statistics-result");
  const rows = (zoneState.live?.tables || []).filter((row) => row.zone_id === zoneId);
  const sections = [
    {group:"beer",label:"Bia",groups:["beer"]},
    {group:"water",label:"Nước",groups:["water","soft_drink"]},
    {group:"rice_paper",label:"Bánh tráng",groups:["rice_paper"]},
    {group:"peanuts",label:"Đậu phộng",groups:["peanuts"]},
    {group:"tobacco",label:"Thuốc",groups:["tobacco"]},
  ];
  const categoryHtml = sections.map((section) => {
    const byCode = new Map();
    let unknown = false;
    rows.forEach((row) => {
      const products = row.product_items || (row.beer_items || []).map((item) => ({...item,group:"beer"}));
      products.filter((item) => section.groups.includes(item.group)).forEach((item) => {
        if (item.unit_status !== "known" || !Number.isFinite(Number(item.quantity))) {
          unknown = true;
          return;
        }
        const key = item.code || item.name+":"+item.unit;
        const current = byCode.get(key) || {...item,quantity:0};
        current.quantity += Number(item.quantity);
        byCode.set(key,current);
      });
    });
    const details = [...byCode.values()].sort((a,b) => a.name.localeCompare(b.name,"vi")).map((item) => {
      const size = Number(item.units_per_carton);
      const unit = String(item.unit || "đơn vị").toLowerCase();
      const pack = section.group === "tobacco" ? "cây" : "thùng";
      const whole = size > 0 ? Math.floor(item.quantity/size) : 0;
      const loose = size > 0 ? item.quantity%size : item.quantity;
      const amount = ["rice_paper","peanuts"].includes(section.group) ?
        item.quantity.toLocaleString("vi-VN")+" "+unit : size > 0 ?
        [whole ? whole+" "+pack : "", loose ? loose.toLocaleString("vi-VN")+" "+unit : ""]
          .filter(Boolean).join(" ") || "0 "+unit :
        item.quantity.toLocaleString("vi-VN")+" "+unit+" · chưa khai quy cách "+pack;
      return "<div><span>"+esc(item.name)+"</span><strong>"+esc(amount)+"</strong></div>";
    }).join("");
    const fallbackQuantity = rows.reduce((sum,row) => sum+Number(row.quantities[section.group] || 0),0);
    const fallback = !details && fallbackQuantity ? "<div><span>Tổng số đã order</span><strong>"+
      fallbackQuantity.toLocaleString("vi-VN")+"</strong></div>" : "";
    return "<details class='zone-stat-category zone-stat-"+section.group+"'><summary>"+section.label+"</summary>"+
      "<div class='zone-stat-product-list'>"+(details || fallback || "<p>Chưa có order "+section.label.toLowerCase()+"</p>")+
      (unknown ? "<p>Có món chưa rõ đơn vị; cần kiểm tra trước khi đối chiếu.</p>" : "")+"</div></details>";
  }).join("");
  panel.innerHTML = "<p class='muted'>Theo order của "+rows.length+" bàn đang mở tại lần tải gần nhất.</p><div class='zone-stat-list'>"+
    categoryHtml+"</div>";
}

function showClosedZoneStatistics(zoneId, report) {
  const panel = $("#zone-statistics-result");
  panel.dataset.reportId = String(report.id);
  const invoices = (report.closed_invoices || []).filter((entry) => Number(entry.zone_id) === zoneId)
    .sort((a,b) => Number(a.table)-Number(b.table) ||
      String(a.invoice_at || a.ordered_at || "").localeCompare(String(b.invoice_at || b.ordered_at || "")));
  if (!report.closed_invoices) {
    panel.innerHTML = "<p class='muted'>Báo cáo cũ chưa lưu chi tiết hóa đơn theo bàn. Bấm tính lại báo cáo sau ca trong mục Khu & rà soát.</p>";
    return;
  }
  panel.innerHTML = "<p class='muted'>"+invoices.length+" hóa đơn đã thanh toán · danh sách món cuối cùng trên hóa đơn CUKCUK. Một bàn có thể có nhiều lượt khách.</p>"+
    (invoices.length ? "<div class='zone-closed-invoices'>"+invoices.map((entry) =>
      "<details class='zone-closed-invoice'><summary><strong>Bàn "+esc(entry.table)+"</strong><span>HĐ "+
      esc(entry.invoice_no || entry.invoice_id)+" · Giờ hóa đơn "+esc(dt(entry.invoice_at || entry.ordered_at))+" · "+
      entry.items.length+" món</span></summary>"+
      "<div class='zone-closed-invoice-body'><div class='zone-closed-items'>"+
      (entry.items.length ? entry.items.map((item) => "<div><span>"+esc(item.name)+"</span><strong>"+
        esc(item.quantity)+" "+esc(item.unit)+"</strong></div>").join("") : "<p>Hóa đơn không có dòng món.</p>")+
      "</div>"+(entry.missing.length ? "<p class='zone-closed-warning'>Chưa có order: "+esc(entry.missing.join(", "))+"</p>" : "")+
      "<form class='zone-closed-note' data-invoice-id='"+esc(entry.invoice_id)+"'><label>Ghi chú bàn "+esc(entry.table)+
      " · "+esc(dt(entry.invoice_at || entry.ordered_at))+" · hóa đơn "+esc(entry.invoice_no || entry.invoice_id)+
      "<input name='note' maxlength='500' value='"+
      esc(entry.note || "")+"' placeholder='Ghi chú lượt khách này'></label><button type='submit' class='secondary'>Lưu ghi chú</button></form>"+
      "</div></details>").join("")+"</div>" : "<p>Chưa có hóa đơn đã thanh toán trong khu này.</p>");
}

function updateStatisticsView() {
  const form = $("#zone-statistics-form");
  const closed = form.elements.view.value === "closed";
  form.querySelector(".zone-statistics-day").hidden = !closed;
  form.elements.day.required = closed;
  if (closed && !form.elements.day.value) form.elements.day.value = businessDayLocal();
  $("#zone-statistics-result").innerHTML = "";
  $("#zone-statistics-status").textContent = "Chọn khu rồi bấm Xem thống kê.";
}
$("#zone-statistics-form select[name='view']").addEventListener("change", updateStatisticsView);

$("#zone-statistics-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const zoneId = Number(event.target.elements.zone_id.value);
  if (!zoneId) return;
  const button = event.target.querySelector("button");
  button.disabled = true;
  const closed = event.target.elements.view.value === "closed";
  $("#zone-statistics-status").textContent = closed ? "Đang lấy báo cáo bàn đã đóng…" : "Đang lấy order bàn đang mở…";
  try {
    if (closed) {
      if (zoneState.demo) throw new Error("Hãy tắt dữ liệu mẫu để xem hóa đơn đã đóng.");
      const day = event.target.elements.day.value;
      let result = await api("/api/zone-shift-report?day="+encodeURIComponent(day));
      if (!result.report?.closed_invoices) result = await api("/api/zone-shift-report","POST",{day});
      showClosedZoneStatistics(zoneId,result.report);
      $("#zone-statistics-status").textContent = "Báo cáo ngày "+day+" · tính lúc "+dt(result.report.generated_at)+".";
    } else {
      if (!zoneState.demo) await refreshZoneReview();
      showZoneStatistics(zoneId);
      $("#zone-statistics-status").textContent = "Đã cập nhật "+dt(zoneState.live?.as_of)+".";
    }
  } catch (error) { $("#zone-statistics-status").textContent = error.message; }
  finally { button.disabled = false; }
});

$("#zone-statistics-form select[name='zone_id']").addEventListener("change", () => {
  $("#zone-statistics-result").innerHTML = "";
  $("#zone-statistics-status").textContent = "Bấm Xem thống kê để lấy số mới cho khu đã chọn.";
});

$("#zone-statistics-result").addEventListener("submit", async (event) => {
  const form = event.target;
  if (!form.matches(".zone-closed-note")) return;
  event.preventDefault();
  try {
    const result = await api("/api/zone-shift-note","POST",{
      report_id:Number($("#zone-statistics-result").dataset.reportId),
      invoice_id:form.dataset.invoiceId,note:form.elements.note.value});
    showClosedZoneStatistics(Number($("#zone-statistics-form").elements.zone_id.value),result.report);
    message("Đã lưu ghi chú.");
  } catch (error) { message(error.message,true); }
});

async function loadZoneShift(day) {
  zoneShiftState = await api("/api/zone-shift-report?day="+encodeURIComponent(day));
  renderZoneShift();
}

function renderZoneShift() {
  const report = zoneShiftState?.report;
  $("#zone-shift-status").textContent = report ?
    "Đã tính "+dt(report.generated_at)+" · "+report.invoice_count+" hóa đơn. Xem trong từng khu." :
    "Chưa tính số sau ca cho ngày này; vẫn có thể nhập thuốc cấp theo khu.";
  if (zoneState.config && !zoneState.demo) renderZoneConfig(zoneState.config);
}

function zoneTobaccoControlHtml(zone) {
  const selectedDay = zoneShiftState?.day || businessDayLocal();
  const today = !!zoneShiftState && selectedDay === businessDayLocal();
  const liveRows = (zoneState.live?.tables || []).filter((row) => row.zone_id === zone.id);
  const names = {TNN:"Thuốc con ngựa",TM:"Thuốc con mèo"};
  const lines = ["TNN","TM"].map((code) => {
    const saved = zoneShiftState?.allocations?.find((item) => item.zone_id === zone.id && item.item_code === code);
    const issued = Number(saved?.issued || 0);
    const orderedLive = zoneState.live ? liveRows.reduce((total,row) => total+
      (row.product_items || []).filter((item) => item.group === "tobacco" &&
        String(item.code || "").toUpperCase() === code && item.unit_status === "known")
        .reduce((sum,item) => sum+Number(item.quantity || 0),0),0) : null;
    const red = today && orderedLive != null && issued > orderedLive;
    const status = !today ? "Ngày đã qua" : orderedLive == null ? "Chưa tải order bàn đang mở" :
      red ? "Đã lấy nhiều hơn số order ở bàn đang mở · cần kiểm tra" : "Order ở bàn đang mở: "+orderedLive+" gói";
    return "<div class='zone-tobacco-line "+(red ? "zone-tobacco-alert" : "")+"'>"+
      "<span title='"+names[code]+"'>"+(code === "TNN" ? "Con ngựa" : "Con mèo")+"</span>"+
      "<button type='button' data-zone-tobacco-change='-1' data-code='"+code+"' data-zone-id='"+zone.id+"' "+
        (today && issued > 0 ? "" : "disabled")+" aria-label='"+names[code]+": sửa giảm 1 gói'>−</button>"+
      "<strong aria-label='Đã lấy "+issued+" gói'>"+issued+"</strong>"+
      "<button type='button' data-zone-tobacco-change='1' data-code='"+code+"' data-zone-id='"+zone.id+"' "+
        (today ? "" : "disabled")+" aria-label='"+names[code]+": ghi thêm 1 gói'>+</button>"+
      "<small>"+status+"</small></div>";
  }).join("");
  return "<section class='zone-tobacco-control'><h3>Thuốc cấp · "+esc(zone.name)+"</h3>"+
    "<p class='muted'>Đã lấy (gói). Bấm − để sửa lần nhập sai; cảnh báo so với order bàn đang mở.</p>"+
    lines+"</section>";
}

function zoneAfterShiftHtml(zoneId) {
  const report = zoneShiftState?.report;
  const zone = report?.zones.find((item) => item.zone_id === zoneId);
  const warnings = (report?.warnings || []).filter((item) => item.zone_id === zoneId);
  const products = zone?.items || [];
  const sections = [
    {key:"beer",label:"Bia",groups:["beer"]},
    {key:"liquor",label:"Rượu",groups:["liquor"]},
    {key:"water",label:"Nước",groups:["water","soft_drink"]},
    {key:"extras",label:"Đồ ăn kèm",groups:["rice_paper","peanuts"]},
    {key:"tobacco",label:"Thuốc",groups:["tobacco"]},
  ];
  const productSummary = report ? "<h4>Đã order trong ngày</h4>"+
    (sections.map((section) => {
      const items = products.filter((item) => section.groups.includes(item.group));
      if (!items.length) return "";
      return "<section class='saleable-history-group history-group-"+section.key+"'><h4>"+
        section.label+" <small>"+items.length+" mặt hàng</small></h4>"+
        table(["Mặt hàng","Số lượng","Quy đổi"],items.map((item) =>
          [item.name,item.quantity+" "+item.unit,item.packs || "-"]))+"</section>";
    }).join("") || "<p class='muted'>Không có mặt hàng nào đã order trong khu.</p>")+
    "<h4>Bàn cần xem lại</h4>"+(warnings.length ? warnings.map((warning) =>
      "<form class='zone-warning-note' data-invoice-id='"+esc(warning.invoice_id)+"'><strong>Bàn "+
      esc(warning.table)+" · HĐ "+esc(warning.invoice_no || warning.invoice_id)+"</strong> · Thiếu order: "+
      esc(warning.missing.join(", ") || "-")+(warning.uncertain ? " · Có món chưa rõ đơn vị" : "")+
      "<label>Ghi chú xác minh<input name='note' maxlength='500' value='"+esc(warning.note || "")+
      "' placeholder='Ví dụ: khách không dùng món kèm'></label><button class='secondary'>Lưu ghi chú</button></form>").join("") :
      "<p class='muted'>Không có hóa đơn cần xem lại trong khu.</p>") :
    "<p class='muted'>Chưa tính số order sau ca cho ngày này.</p>";
  const allocations = ["TNN","TM"].map((code) => {
    const saved = zoneShiftState?.allocations?.find((item) => item.zone_id === zoneId && item.item_code === code);
    const balance = zone?.tobacco_balance?.find((item) => item.code === code);
    const issued = saved?.issued == null ? null : Number(saved.issued);
    const ordered = balance?.ordered == null ? null : Number(balance.ordered);
    const returned = saved?.returned == null ? null : Number(saved.returned);
    const gap = issued == null || ordered == null || returned == null ? null : issued-ordered-returned;
    return "<div class='zone-tobacco-summary "+(gap != null && gap !== 0 ? "zone-tobacco-alert" : "")+"'>"+
      "<strong>"+(code === "TNN" ? "Thuốc con ngựa" : "Thuốc con mèo")+"</strong>"+
      "<dl class='zone-tobacco-metrics'>"+
      "<div><dt>Đã lấy</dt><dd>"+(issued == null ? "-" : issued)+" gói</dd></div>"+
      "<div><dt>Đã order</dt><dd>"+(ordered == null ? "-" : ordered)+" gói</dd></div>"+
      "<div><dt>Đã trả kho</dt><dd>"+(returned == null ? "-" : returned)+" gói</dd></div>"+
      "<div><dt>Chênh lệch</dt><dd>"+(gap == null ? "-" : gap)+" gói</dd></div></dl>"+
      "<form class='zone-tobacco-return-form' data-zone-id='"+zoneId+"' data-code='"+code+"'>"+
      "<label>Gói trả về kho<input type='number' name='returned' min='0' step='1' value='"+
      (returned == null ? "" : returned)+"' required></label><button class='secondary'>Lưu số trả</button></form>"+
      "<small>Chênh là số đã lấy trừ số order và số trả kho; cần xác minh trước khi kết luận thất thoát.</small>"+
      "</div>";
  }).join("");
  return "<details class='zone-shift-zone' data-after-shift-zone='"+zoneId+"'><summary>Thuốc cấp khu và số sau ca"+
    (report ? " · "+warnings.length+" hóa đơn cần xem" : "")+"</summary>"+
    "<p class='muted'>Ngày "+esc(zoneShiftState?.day || businessDayLocal())+" · số gói đã lấy được ghi bằng nút + trong thẻ khu</p>"+
    allocations+productSummary+"<p class='muted'>Thiếu order chỉ là dấu hiệu cần xác minh, không tự kết luận nhân viên vi phạm.</p></details>";
}

$("#zone-shift-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (zoneState.demo) return message("Hãy tắt dữ liệu mẫu trước khi tính báo cáo",true);
  const button = event.target.querySelector("button");
  button.disabled = true;
  $("#zone-shift-status").textContent = "Đang lấy hóa đơn CUKCUK và tính số theo khu…";
  try {
    zoneShiftState = await api("/api/zone-shift-report","POST",{day:event.target.elements.day.value});
    renderZoneShift();
  } catch (error) { $("#zone-shift-status").textContent = error.message; }
  finally { button.disabled = false; }
});

$("#zone-shift-form input[name='day']").addEventListener("change", (event) => {
  loadZoneShift(event.target.value).catch((error) => $("#zone-shift-status").textContent = error.message);
});

$("#zone-list").addEventListener("submit", async (event) => {
  const form = event.target;
  if (form.matches(".zone-tobacco-return-form")) {
    event.preventDefault();
    try {
      zoneShiftState = await api("/api/zone-tobacco-allocation","POST",{
        day:zoneShiftState.day,zone_id:Number(form.dataset.zoneId),item_code:form.dataset.code,
        returned:Number(form.elements.returned.value)});
      renderZoneShift(); message("Đã lưu số thuốc trả kho.");
    } catch (error) { message(error.message,true); }
  } else if (form.matches(".zone-warning-note")) {
    event.preventDefault();
    try {
      zoneShiftState = await api("/api/zone-shift-note","POST",{
        report_id:zoneShiftState.report.id,invoice_id:form.dataset.invoiceId,note:form.elements.note.value});
      renderZoneShift(); message("Đã lưu ghi chú.");
    } catch (error) { message(error.message,true); }
  }
});

async function refreshCukcuk(from, to) {
  const today = new Date();
  const form = document.querySelector('form[data-action="cukcuk-filter"]');
  const localDay = (d) => [d.getFullYear(), String(d.getMonth() + 1).padStart(2, "0"), String(d.getDate()).padStart(2, "0")].join("-");
  if (!from) from = form.elements.from.value || localDay(new Date(today.getFullYear(), today.getMonth(), 1));
  if (!to) to = form.elements.to.value || localDay(today);
  form.elements.from.value = from;
  form.elements.to.value = to;
  const report = await api("/api/cukcuk-summary?from=" + encodeURIComponent(from) + "&to=" + encodeURIComponent(to));
  $("#cukcuk-sync-status").textContent = report.synced ? "Đã đồng bộ đủ ngày trong kỳ." : "Thiếu dữ liệu đồng bộ cho một hoặc nhiều ngày trong kỳ; các số dưới đây chưa đầy đủ.";
  const total = report.totals;
  $("#cukcuk-totals").innerHTML = table(["Hóa đơn đã thu", "Doanh thu", "Tiền mặt", "Thẻ", "Khác/chưa phân loại", "Mã chưa ghép kho"],
    [[total.invoices, vnd(total.gross), vnd(total.cash), vnd(total.card), vnd(total.other), report.unmapped]]);
  $("#cukcuk-beer").innerHTML = table(["Mã", "Tên", "Nhóm", "Số bán", "Đơn vị"],
    report.beer_tobacco.map((r) => [r.code, r.name, groupName[r.group], qty(r.quantity), r.unit]));
  $("#cukcuk-products").innerHTML = table(["Mã", "Tên", "Số bán", "Doanh số", "Ghép kho"],
    report.products.slice(0, 30).map((r) => [r.code, r.name, qty(r.quantity), vnd(r.amount), r.mapped ? "Có" : "Chưa"]));
  $("#cukcuk-days").innerHTML = table(["Ngày", "Hóa đơn", "Doanh thu"],
    report.days.map((r) => [r.date, r.invoices, vnd(r.total)]));
  $("#cukcuk-months").innerHTML = table(["Tháng", "Hóa đơn", "Doanh thu"],
    report.months.map((r) => [r.month, r.invoices, vnd(r.total)]));
  $("#cukcuk-monthly-items").innerHTML = table(["Tháng", "Mã", "Món", "Số bán"],
    report.monthly_items.map((r) => [r.month, r.code, r.name, qty(r.quantity)]));
}

document.addEventListener("submit", async (event) => {
  const form = event.target.closest("form[data-action]");
  if (!form) return;
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  try { await submit(form); }
  catch (err) { message(err.message || "Có lỗi", true); }
  finally { button.disabled = false; }
});
all("nav button").forEach((button) => button.addEventListener("click", () => selectTab(button.dataset.tab)));
const reviewBulkCountClick = () => {
  try { reviewBulkCount(); } catch (error) { message(error.message, true); }
};
$("#bulk-count-opening").addEventListener("click", reviewBulkCountClick);
$("#bulk-count-closing").addEventListener("click", reviewBulkCountClick);
$("#bulk-count-edit").addEventListener("click", () => {
  $("#bulk-count-confirm").hidden = true;
  $("#bulk-count-entry").hidden = false;
  bulkCountState.reviewed = null;
});
$("#bulk-count-save").addEventListener("click", async (event) => {
  if (!bulkCountState || !bulkCountState.reviewed) return;
  event.target.disabled = true;
  try {
    const result = await api("/api/daily-stock-batch", "POST", {
      day: bulkCountState.day, phase: bulkCountState.phase, items: bulkCountState.reviewed});
    message("Đã hoàn tất " + result.count + " mặt hàng.");
    await loadBulkCount(bulkCountState.day, bulkCountState.phase);
    $("#daily-stock-status").textContent = "Đã lưu số kiểm. Bấm Tính kết quả để xem số liệu mới.";
    $("#daily-stock-table").innerHTML = "";
  } catch (error) { message(error.message, true); }
  finally { event.target.disabled = false; }
});
all("[data-inventory-tab]").forEach((button) => button.addEventListener("click", () => {
  if (button.disabled) return;
  const selected = button.dataset.inventoryTab;
  all("[data-inventory-tab]").forEach((tab) => tab.setAttribute("aria-selected", String(tab === button)));
  all("[data-inventory-panel]").forEach((panel) => panel.hidden = panel.dataset.inventoryPanel !== selected);
  $("#shared-stock-admin").hidden = selected === "saleable";
  if (selected === "daily-use") refreshDailyUsage().catch((error) => message(error.message, true));
  if (selected === "saleable") {
    const form = document.querySelector('form[data-action="bulk-count-load"]');
    loadBulkCount(form.elements.day.value || todayLocal(),form.elements.phase.value).catch((error) => $("#bulk-count-status").textContent = error.message);
    const historyForm = $("#saleable-history-filter");
    loadSaleableHistory(historyForm.elements.period.value,historyForm.elements.anchor.value || businessDayLocal())
      .catch((error) => $("#saleable-history-status").textContent = error.message);
  }
}));
 const bulkDayInput = document.querySelector('form[data-action="bulk-count-load"] input[name="day"]');
 $("#bulk-count-search").addEventListener("input", filterBulkCountRows);
 $("#calculate-daily-stock").addEventListener("click", async (event) => {
   event.target.disabled = true;
   $("#daily-stock-table").innerHTML = "";
   try {
     const tables = await api("/api/table-merchandise");
     if (tables.active_orders > 0) {
       $("#daily-stock-status").textContent = "Còn " + tables.active_orders + " bàn/đơn đang mở. Đã lưu số kiểm nhưng chưa tính chênh lệch cuối ngày.";
       return;
     }
     await refreshDailyStock(bulkDayInput.value);
   } catch (error) {
     $("#daily-stock-status").textContent = "Chưa xác minh được bàn đang mở hoặc dữ liệu CUKCUK: " + error.message;
   } finally { event.target.disabled = false; }
 });
bulkDayInput.value = todayLocal();
bulkDayInput.min = todayLocal();
bulkDayInput.max = todayLocal();
document.querySelector('form[data-action="bulk-count-load"] select[name="phase"]').addEventListener("change", (event) => {
  updateBulkActions(event.target.value);
  loadBulkCount(bulkDayInput.value,event.target.value).catch((error) => $("#bulk-count-status").textContent = error.message);
});
 $("#bulk-count-inputs").addEventListener("click", (event) => {
   const button = event.target.closest("[data-add-group]");
   if (!button) return;
   const form = $("#quick-item-form");
   form.hidden = false;
   form.elements.group_name.value = button.dataset.addGroup;
   form.elements.group_name.dispatchEvent(new Event("change"));
   form.scrollIntoView({block:"nearest"});
   form.elements.code.focus();
 });
document.querySelector('#quick-item-form select[name="group_name"]').addEventListener("change", (event) => {
   const group = event.target.value;
   const form = event.target.form;
   form.elements.unit.value = group === "liquor" || group === "water" ? "Chai" :
     ["tobacco","rice_paper","peanuts"].includes(group) ? "Gói" : "Lon";
   form.elements.units_per_carton.value = group === "liquor" ? "12" : group === "tobacco" ? "10" : "24";
   $("#quick-item-carton-label span").textContent = group === "tobacco" ? "Số gói/cây" : "Số đơn vị/thùng";
});
for (const selector of ["#bulk-count-inputs", "#daily-stock-table"]) {
  const area = $(selector);
  area.addEventListener("focusin", (event) => {
    const input = event.target.closest("[data-edit-field]");
    if (input) input.readOnly = false;
  });
  area.addEventListener("keydown", (event) => {
    const input = event.target.closest("[data-edit-field]");
    if (!input) return;
    if (event.key === "Enter") { event.preventDefault(); input.blur(); }
    if (event.key === "Escape") {
      event.preventDefault();
      input.dataset.cancelEdit = "1";
      input.blur();
    }
  });
  area.addEventListener("focusout", async (event) => {
    const input = event.target.closest("[data-edit-field]");
    if (!input) return;
    const valid = input.checkValidity();
    input.readOnly = true;
    const oldValue = input.dataset.value;
    if (input.dataset.cancelEdit || input.value === oldValue) {
      input.value = oldValue;
      delete input.dataset.cancelEdit;
      return;
    }
    if (!input.value || !valid) {
      input.value = oldValue;
      return message("Nhập số nguyên hợp lệ", true);
    }
    input.disabled = true;
    try {
      if (input.dataset.editField === "carton_size") {
        await api("/api/items/"+input.dataset.itemId+"/carton-size", "POST", {units_per_carton:Number(input.value)});
      } else {
        await api("/api/daily-stock-inline", "POST", {day:input.dataset.day,item_id:Number(input.dataset.itemId),field:input.dataset.editField,quantity:input.value});
      }
      const form = document.querySelector('form[data-action="bulk-count-load"]');
      await loadBulkCount(form.elements.day.value,form.elements.phase.value);
       $("#daily-stock-status").textContent = "Đã sửa số liệu. Bấm Tính kết quả để cập nhật báo cáo.";
       $("#daily-stock-table").innerHTML = "";
      message("Đã cập nhật số liệu.");
    } catch (error) { input.value = oldValue; input.disabled = false; message(error.message,true); }
  });
}
$("#zone-demo").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    if (!zoneState.demo) {
      const demo = makeZoneDemo();
      zoneState.demo = true;
      zoneState.config = demo.config;
      zoneState.live = demo.live;
      button.textContent = "Về dữ liệu thật";
      $("#zone-add").hidden = true;
      $("#zone-review-status").textContent = "DỮ LIỆU MẪU · 5 bàn, 2 nhân viên. Không lưu vào ứng dụng hay CUKCUK. Bấm từng bàn để xem số order mẫu.";
      $("#zone-review-status").classList.add("zone-demo-status");
      renderZoneConfig(zoneState.config);
    } else {
      zoneState.demo = false;
      zoneState.config = null;
      zoneState.live = null;
      button.textContent = "Xem dữ liệu mẫu";
      $("#zone-add").hidden = false;
      $("#zone-review-status").classList.remove("zone-demo-status");
      $("#zone-review-status").textContent = "Đang tải dữ liệu thật…";
      $("#zone-list").innerHTML = "";
      $("#zone-unassigned").hidden = true;
      await refreshZoneConfig();
      await refreshZoneReview();
    }
  } catch (error) { $("#zone-review-status").textContent = error.message; }
  finally { button.disabled = false; }
});
$("#zone-add").addEventListener("click", () => {
  if (zoneState.demo) return;
  if ($("#zone-draft")) { $("#zone-draft input[name='name']").focus(); return; }
  $("#zone-list").insertAdjacentHTML("afterbegin", "<article class='zone-card' id='zone-draft'><form data-action='zone-create'>"+
    "<h2>Khu mới</h2><label>Tên nhân viên<input name='name' maxlength='60' required placeholder='Tên người phụ trách'></label>"+
    "<div id='zone-draft-tables'><label>Số bàn<input data-new-table type='number' min='1' step='1' placeholder='Ví dụ: 101'></label></div>"+
    "<div class='zone-draft-actions'><button type='button' class='secondary' data-add-zone-table>+ Thêm bàn</button>"+
    "<button>Lưu khu</button><button type='button' class='secondary' data-cancel-zone>Hủy</button></div></form></article>");
  $("#zone-draft input[name='name']").focus();
});
$("#zone-table-dialog-close").addEventListener("click", () => $("#zone-table-dialog").close());
$("#zones").addEventListener("click", async (event) => {
  const tableButton = event.target.closest("[data-table-number]");
  if (tableButton) { showZoneTableDialog(tableButton.dataset.tableNumber); return; }
  const button = event.target.closest("[data-add-zone-table],[data-cancel-zone],[data-remove-table],[data-edit-zone],[data-zone-tobacco-change]");
  if (!button) return;
  if (button.hasAttribute("data-zone-tobacco-change")) {
    button.disabled = true;
    try {
      zoneShiftState = await api(Number(button.dataset.zoneTobaccoChange) > 0 ?
        "/api/zone-tobacco-issue" : "/api/zone-tobacco-unissue","POST",{
        day:zoneShiftState.day,zone_id:Number(button.dataset.zoneId),item_code:button.dataset.code});
      renderZoneShift();
    } catch (error) { button.disabled = false; message(error.message,true); }
    return;
  }
  if (button.hasAttribute("data-edit-zone")) {
    const panel = $("[data-zone-edit-panel='"+button.dataset.editZone+"']");
    panel.hidden = !panel.hidden;
    return;
  }
  if (button.hasAttribute("data-add-zone-table")) {
    $("#zone-draft-tables").insertAdjacentHTML("beforeend", "<label>Số bàn<input data-new-table type='number' min='1' step='1' placeholder='Số bàn'></label>");
    $("#zone-draft-tables label:last-child input").focus();
    return;
  }
  if (button.hasAttribute("data-cancel-zone")) { $("#zone-draft").remove(); return; }
  if (!window.confirm("Bỏ bàn này khỏi khu?")) return;
  button.disabled = true;
  try {
    await api("/api/zone-tables/remove","POST",{table_name:button.dataset.removeTable});
    await refreshZoneConfig();
    if (zoneState.live) await refreshZoneReview();
    message("Đã bỏ bàn khỏi khu.");
  } catch (error) { button.disabled = false; message(error.message,true); }
});
document.querySelector('form[data-action="sales-import"] input[type="file"]').addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) { $("#csv-preview").innerHTML = ""; return; }
  try {
    const rows = parseCsv(await file.text());
    $("#csv-preview").innerHTML = "<h2>Xem trước " + rows.length + " dòng</h2>" +
      table(["Mã dòng","Mã hàng","Số lượng","Doanh thu","Kênh"],
        rows.slice(0, 5).map((r) => [r.source_row_id,r.item_code,r.quantity,r.amount,r.method]));
  } catch (err) {
    $("#csv-preview").innerHTML = "";
    message(err.message, true);
  }
});
$("#sample-csv").addEventListener("click", (event) => {
  event.preventDefault();
  const csv = "source_row_id,item_code,quantity,amount,method\nBILL-001-L1,BIA-001,2,50000,cash\n";
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob(["\uFEFF" + csv], {type:"text/csv;charset=utf-8"}));
  link.download = "mau-ban-hang.csv";
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
});
load().catch((err) => message(err.message, true));
