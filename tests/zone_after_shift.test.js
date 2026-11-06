const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const app = fs.readFileSync(path.join(__dirname,"..","static","app.js"),"utf8");
const html = fs.readFileSync(path.join(__dirname,"..","static","index.html"),"utf8");
const start = app.indexOf("function zoneAfterShiftHtml(");
const end = app.indexOf('$("#zone-shift-form").addEventListener',start);
assert.equal(start >= 0 && end > start,true);
assert.equal(html.includes('id="zone-shift-result"'),false);

const state = {day:"2026-11-06",report:{zones:[
  {zone_id:1,items:[
    {group:"beer",name:"Tiger",quantity:24,unit:"lon",packs:"1 thùng"},
    {group:"water",name:"Nước suối",quantity:2,unit:"chai",packs:"2 chai"},
    {group:"rice_paper",name:"Bánh tráng",quantity:1,unit:"phần",packs:null},
    {group:"tobacco",name:"Thuốc con ngựa",quantity:1,unit:"gói",packs:"1 gói"},
  ],tobacco_balance:[]},
  {zone_id:2,items:[],tobacco_balance:[]},
],warnings:[
  {zone_id:1,invoice_id:"A",table:"1",missing:["bia"]},
  {zone_id:2,invoice_id:"B",table:"2",missing:["bánh tráng"]},
]},allocations:[{zone_id:1,item_code:"TNN",issued:12,returned:1,ending:null}]};
const table = (_headers,rows) => "<table>"+rows.map((row) => "<tr>"+row.join("|")+"</tr>").join("")+"</table>";
const render = new Function("zoneShiftState","businessDayLocal","table","esc",
  app.slice(start,end)+"return zoneAfterShiftHtml;")(state,()=>"2026-11-06",table,String);
const card = render(1);
for (const group of ["beer","water","extras","tobacco"]) {
  assert.equal(card.includes("history-group-"+group),true);
}
assert.equal(card.includes("history-group-liquor"),false);
assert.equal(card.includes("Bàn 1"),true);
assert.equal(card.includes("Bàn 2"),false);
assert.equal((card.match(/class='zone-tobacco-return-form'/g) || []).length,2);
assert.match(card,/<dt>Đã lấy<\/dt><dd>12 gói<\/dd>/);
assert.match(card,/<dt>Đã trả kho<\/dt><dd>1 gói<\/dd>/);
assert.equal((card.match(/class='zone-tobacco-metrics'/g) || []).length,2);
const controlStart = app.indexOf("function zoneTobaccoControlHtml(");
const control = new Function("zoneShiftState","zoneState","businessDayLocal","esc",
  app.slice(controlStart,start)+"return zoneTobaccoControlHtml;")(
  state,{live:{tables:[{zone_id:1,product_items:[{group:"tobacco",code:"TNN",quantity:11,unit_status:"known"}]}]}},
  ()=>"2026-11-06",String);
const pills = control({id:1,name:"Nhân viên A"});
assert.equal((pills.match(/data-zone-tobacco-change='1'/g) || []).length,2);
assert.equal((pills.match(/data-zone-tobacco-change='-1'/g) || []).length,2);
assert.equal(pills.includes("Đã lấy 12 gói"),true);
assert.equal(pills.includes("zone-tobacco-alert"),true);
assert.equal(pills.includes("Nhân viên A"),true);
console.log("Zone after-shift cards and grouped items: OK");
