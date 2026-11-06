const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const app = fs.readFileSync(path.join(__dirname,"..","static","app.js"),"utf8");
const html = fs.readFileSync(path.join(__dirname,"..","static","index.html"),"utf8");
assert.equal(html.includes("Bàn đang gọi hàng"),false);
assert.equal(app.includes("refreshTableMerchandise"),false);
const start = app.indexOf("async function loadSaleableHistory(");
const end = app.indexOf('$("#saleable-history-filter").addEventListener',start);
assert(start >= 0 && end > start);
const status = {textContent:""};
const days = {innerHTML:""};
const $ = (selector) => selector === "#saleable-history-status" ? status : days;
const day = {day:"2026-11-06",status:"ok",source:"sync",invoice_count:2,
  rows:[
    {group:"beer",name:"Tiger",opening:"24",incoming:"24",sold:"2",closing:"46",variance:"0"},
    {group:"liquor",name:"Rượu táo mèo",opening:"12",incoming:"0",sold:"1",closing:"11",variance:"0"},
    {group:"water",name:"Nước suối",opening:"24",incoming:"0",sold:"1",closing:"23",variance:"0"},
    {group:"rice_paper",name:"Bánh tráng",opening:"10",incoming:"0",sold:"2",closing:"8",variance:"0"},
    {group:"tobacco",name:"Thuốc con ngựa",opening:"10",incoming:"0",sold:"1",closing:"9",variance:"0"},
  ]};
let requested = "";
let response = {from:"2026-11-06",to:"2026-11-06",period:"day",days:[day]};
const api = async (url) => {
  requested = url;
  return response;
};
const load = new Function("$","api","qty","groupName","table","esc",
  app.slice(start,end)+"return loadSaleableHistory;")($,api,String,{beer:"Bia"},
  () => "<table></table>",String);
load("day","2026-11-06").then(async () => {
  assert.match(requested,/\/api\/saleable-history\?/);
  assert.equal(/<details[^>]* open>/.test(days.innerHTML),false);
  assert.equal(html.includes('<details class="card saleable-section-card saleable-history-panel">'),true);
  assert.match(days.innerHTML,/06\/11\/2026/);
  for (const group of ["beer","liquor","water","extras","tobacco"]) {
    assert.equal(days.innerHTML.includes("history-group-"+group),true);
  }
  assert.equal((days.innerHTML.match(/<details class='saleable-history-group/g) || []).length,5);
  assert.equal((days.innerHTML.match(/<summary>/g) || []).length,6);
  response = {from:"2026-11-02",to:"2026-11-08",period:"week",days:[day,{...day,day:"2026-11-07"}]};
  await load("week","2026-11-06");
  assert.equal((days.innerHTML.match(/<details class='saleable-history-day/g) || []).length,2);
  assert.equal(/<details[^>]* open>/.test(days.innerHTML),false);
  console.log("Saleable history day and week accordions: OK");
}).catch((error) => {console.error(error);process.exitCode = 1;});
