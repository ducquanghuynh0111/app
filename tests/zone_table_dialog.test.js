const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname,"..","static","app.js"),"utf8");
const html = fs.readFileSync(path.join(__dirname,"..","static","index.html"),"utf8");
const css = fs.readFileSync(path.join(__dirname,"..","static","zone-layout.css"),"utf8");
const makeStart = source.indexOf("function makeZoneDemo()");
const makeEnd = source.indexOf("function zoneTableNumber(",makeStart);
const start = makeEnd;
const end = source.indexOf("function renderZoneConfig(",start);
assert(makeStart >= 0 && makeEnd > makeStart && end > start);
const demo = new Function(source.slice(makeStart,makeEnd)+"return makeZoneDemo;")()();
const dialog = {shown:false,showModal(){this.shown=true;}};
const title = {textContent:""};
const body = {innerHTML:""};
const elements = {
  "#zone-table-dialog":dialog,
  "#zone-table-dialog-title":title,
  "#zone-table-dialog-body":body,
};
const functions = new Function("zoneState","$","esc","qty","zoneGroupName",
  source.slice(start,end)+"return {zoneTableRow,showZoneTableDialog};")(
    {live:demo.live},(selector)=>elements[selector],String,String,
    {beer:"Bia",water:"Nước",rice_paper:"Bánh tráng",peanuts:"Đậu phộng",tobacco:"Thuốc"});

const tile = functions.zoneTableRow("1",demo.live.tables[0]);
assert.match(tile,/<button type='button' class='zone-table-row missing'/);
assert.match(tile,/data-table-number='1'/);
assert.doesNotMatch(tile,/<details/);
functions.showZoneTableDialog("1");
assert.equal(dialog.shown,true);
assert.equal(title.textContent,"Bàn 1");
assert.match(body.innerHTML,/Bia Tiger/);
assert.match(body.innerHTML,/24 lon/);
assert.match(body.innerHTML,/Thuốc con ngựa/);
assert.match(body.innerHTML,/Thiếu order: Bánh tráng, Đậu phộng/);
functions.showZoneTableDialog("99");
assert.match(body.innerHTML,/Bàn chưa mở trên CUKCUK/);
assert.match(body.innerHTML,/<strong>0<\/strong>/);
assert.match(html,/<dialog id="zone-table-dialog"/);
assert.match(css, /grid-template-columns: repeat\(3, minmax\(0, 1fr\)\)/);
assert.match(css, /repeat\(auto-fit, minmax\(105px, 1fr\)\)/);
console.log("Three-column zones and table dialog: OK");
