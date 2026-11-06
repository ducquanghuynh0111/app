const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname,"..","static","app.js"),"utf8");
const start = source.indexOf("function showClosedZoneStatistics(zoneId, report)");
const end = source.indexOf("function updateStatisticsView()",start);
assert(start >= 0 && end > start);
const panel = {innerHTML:"",dataset:{}};
const esc = (value) => String(value == null ? "" : value).replace(/[&<>"']/g,
  (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const show = new Function("$","esc","dt",source.slice(start,end)+"return showClosedZoneStatistics;")(
  () => panel,esc,(value) => value || "—");
show(1,{id:9,closed_invoices:[
  {invoice_id:"a",invoice_no:"H1",table:"2",zone_id:1,invoice_at:"2026-11-06T10:00:00",
   items:[{name:"Mì xào",quantity:"2",unit:"Phần"}],missing:[],note:"Lượt sáng"},
  {invoice_id:"b",invoice_no:"H2",table:"2",zone_id:1,invoice_at:"2026-11-06T20:00:00",
   items:[{name:"Bia Tiger",quantity:"1",unit:"Thùng"}],missing:["Đậu phộng"],note:"Lượt tối"},
  {invoice_id:"c",invoice_no:"H3",table:"3",zone_id:2,invoice_at:"2026-11-06T12:00:00",
   items:[{name:"Khác",quantity:"1",unit:"Phần"}],missing:[],note:""},
]});
assert.equal(panel.dataset.reportId,"9");
assert.match(panel.innerHTML,/2 hóa đơn đã thanh toán/);
assert.match(panel.innerHTML,/Mì xào/);
assert.match(panel.innerHTML,/Bia Tiger/);
assert.match(panel.innerHTML,/Lượt sáng/);
assert.match(panel.innerHTML,/Lượt tối/);
assert.match(panel.innerHTML,/Ghi chú bàn 2 · 2026-11-06T10:00:00 · hóa đơn H1/);
assert.match(panel.innerHTML,/Ghi chú bàn 2 · 2026-11-06T20:00:00 · hóa đơn H2/);
assert.doesNotMatch(panel.innerHTML,/H3/);
assert.equal((panel.innerHTML.match(/class='zone-closed-note'/g) || []).length,2);
console.log("Closed invoices per table and per-invoice notes: OK");
