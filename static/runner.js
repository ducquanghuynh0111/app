const keyInput = document.querySelector("#device-key");
const connection = document.querySelector("#connection");
const queueElement = document.querySelector("#queue");
let deviceKey = "";
let eventCursor = -1;
let queue = [];
let timer = null;
let refreshing = false;

function speak(message) {
  if (!("speechSynthesis" in window)) {
    connection.textContent = "Trình duyệt này không hỗ trợ đọc giọng nói.";
    return;
  }
  const utterance = new SpeechSynthesisUtterance(message);
  utterance.lang = "vi-VN";
  utterance.rate = 1;
  const voice = speechSynthesis.getVoices().find((v) => v.lang.toLowerCase().startsWith("vi"));
  if (voice) utterance.voice = voice;
  speechSynthesis.speak(utterance);
}

function dishText(item) {
  return (item.table_name ? "Bàn " + item.table_name : "Order " + item.order_no) + ", " +
    item.quantity + " phần " + item.item_name;
}

function render() {
  const now = Date.now();
  queueElement.replaceChildren();
  document.querySelector("#count").textContent = queue.length + " món đang chờ";
  for (const item of queue) {
    const minutes = Math.max(0, Math.floor((now - Date.parse(item.first_seen_at)) / 60000));
    const lateMinutes = Number(document.body.dataset.lateMinutes || 15);
    const card = document.createElement("article");
    card.className = "dish" + (minutes >= lateMinutes ? " late" : "");
    const content = document.createElement("div");
    const title = document.createElement("h2");
    title.textContent = item.quantity + " × " + item.item_name;
    const table = document.createElement("p");
    table.textContent = item.table_name ? "Bàn " + item.table_name : "Order " + item.order_no;
    const meta = document.createElement("p");
    meta.className = "meta";
    meta.textContent = "Chờ " + minutes + " phút" + (minutes >= lateMinutes ? " · QUÁ HẠN" : "");
    content.append(title, table, meta);
    card.append(content);
    if (document.body.dataset.completionMode !== "kds") {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = "Đã phục vụ";
      button.addEventListener("click", () => serve(item.detail_id, button));
      card.append(button);
    }
    queueElement.append(card);
  }
}

async function refresh() {
  if (!deviceKey || refreshing) return;
  refreshing = true;
  try {
    const response = await fetch("/api/runner/queue?after=" + eventCursor, {headers:{"X-Runner-Key":deviceKey},cache:"no-store"});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Không kết nối được");
    queue = data.items;
    document.body.dataset.lateMinutes = data.late_minutes;
    document.body.dataset.completionMode = data.completion_mode;
    render();
    if (eventCursor === -1) eventCursor = data.latest_event_id;
    else for (const event of data.events) {
      eventCursor = event.id;
      if (event.kind === "late") speak("Nhắc món quá hạn. " + dishText(event) + ". Vui lòng kiểm tra bếp.");
      else if (event.kind === "total") speak((event.added_quantity && event.added_quantity !== event.quantity ?
        "Có thêm " + event.added_quantity + " phần " + event.item_name + ". " : "") +
        "Tổng chưa ra " + event.quantity + " phần " + event.item_name + ".");
      else if (event.kind === "ready") speak("Đã ra " + event.quantity + " phần " + event.item_name + "." + (event.remaining_text ? " " + event.remaining_text + "." : ""));
      else if (event.kind === "added") speak("Bổ sung món. " + (event.table_name ? "Bàn " + event.table_name : "Order " + event.order_no) + ", thêm " + event.quantity + " phần " + event.item_name + ".");
      else if (event.kind === "reduced") speak("Món thay đổi. " + dishText(event) + " còn chờ.");
      else speak("Có món mới. " + dishText(event));
    }
    if (data.monitor && data.monitor.last_error) connection.textContent = "Lỗi đồng bộ CUKCUK: " + data.monitor.last_error;
    else if (data.monitor && data.monitor.last_success_at) {
      const age = Math.floor((Date.now() - Date.parse(data.monitor.last_success_at)) / 1000);
      connection.textContent = age > 120 ? "Đồng bộ đã dừng hơn 2 phút" : "Đang theo dõi order · cập nhật " + age + " giây trước";
    } else connection.textContent = "Chờ chương trình theo dõi CUKCUK khởi động";
    return true;
  } catch (error) { connection.textContent = error.message; return false; }
  finally { refreshing = false; }
}

async function serve(detailId, button) {
  button.disabled = true;
  try {
    const response = await fetch("/api/runner/serve", {method:"POST",
      headers:{"Content-Type":"application/json","X-Runner-Key":deviceKey},
      body:JSON.stringify({detail_id:detailId})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Không ghi nhận được");
    await refresh();
  } catch (error) { connection.textContent = error.message; button.disabled = false; }
}

document.querySelector("#enable").addEventListener("click", async () => {
  deviceKey = keyInput.value.trim();
  if (!deviceKey) { connection.textContent = "Nhập khóa thiết bị"; return; }
  if (!await refresh()) return;
  if (timer) clearInterval(timer);
  timer = setInterval(refresh, 5000);
  speak("Đã bật nhắc món. Có " + queue.length + " món đang chờ.");
  keyInput.value = "";
});
document.querySelector("#test-voice").addEventListener("click", () => speak("Kiểm tra giọng nói tiếng Việt. Bàn một, một phần món thử."));
document.querySelector("#read-queue").addEventListener("click", () => {
  if (!deviceKey) { connection.textContent = "Bật loa và kết nối trước"; return; }
  if (!queue.length) return speak("Hiện không có món đang chờ.");
  queue.slice(0, 30).forEach((item) => speak(dishText(item)));
});
