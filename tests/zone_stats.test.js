const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname,"..","static","app.js"),"utf8");
function section(start,end) {
  const a = source.indexOf(start);
  const b = source.indexOf(end,a+start.length);
  assert(a >= 0 && b > a);
  return source.slice(a,b);
}
const makeZoneDemo = new Function(section("function makeZoneDemo()", "function zoneTableNumber" )+"return makeZoneDemo;")();
const demo = makeZoneDemo();
const panel = {innerHTML:""};
const showZoneStatistics = new Function("zoneState","$","esc","zoneGroupName",
  section("function showZoneStatistics(zoneId)","function showClosedZoneStatistics(zoneId, report)")+"return showZoneStatistics;")(
    {live:demo.live}, () => panel, String,
    {water:"Nước",rice_paper:"Bánh tráng",peanuts:"Đậu phộng",tobacco:"Thuốc"});
showZoneStatistics(90001);
assert.match(panel.innerHTML,/<details class='zone-stat-category zone-stat-beer'><summary>Bia<\/summary>/);
assert.match(panel.innerHTML,/<details class='zone-stat-category zone-stat-water'><summary>Nước<\/summary>/);
assert.match(panel.innerHTML,/<details class='zone-stat-category zone-stat-rice_paper'><summary>Bánh tráng<\/summary>/);
assert.match(panel.innerHTML,/<details class='zone-stat-category zone-stat-peanuts'><summary>Đậu phộng<\/summary>/);
assert.match(panel.innerHTML,/<details class='zone-stat-category zone-stat-tobacco'><summary>Thuốc<\/summary>/);
assert.doesNotMatch(panel.innerHTML,/<details class='zone-stat-category[^']*' open>/);
assert.match(panel.innerHTML,/Bia Tiger<\/span><strong>1 thùng 2 lon/);
assert.match(panel.innerHTML,/Bia Heineken<\/span><strong>2 lon/);
assert.match(panel.innerHTML,/Nước suối<\/span><strong>2 chai/);
assert.match(panel.innerHTML,/Thuốc con ngựa<\/span><strong>1 gói/);
assert.doesNotMatch(panel.innerHTML,/>29</);
assert.equal(demo.live.tables.find((row) => row.table === "Bàn 16").quantities.beer,"4");
demo.live.tables[0].product_items.push({code:"NS",name:"Nước suối",group:"water",quantity:"24",unit:"Chai",units_per_carton:24,unit_status:"known"});
demo.live.tables[0].product_items.push({code:"PEPSI",name:"Pepsi",group:"soft_drink",quantity:"2",unit:"Lon",units_per_carton:24,unit_status:"known"});
demo.live.tables[2].product_items.push({code:"TNN",name:"Thuốc con ngựa",group:"tobacco",quantity:"9",unit:"Gói",units_per_carton:10,unit_status:"known"});
showZoneStatistics(90001);
assert.match(panel.innerHTML,/Nước suối<\/span><strong>1 thùng 2 chai/);
assert.match(panel.innerHTML,/Pepsi<\/span><strong>2 lon/);
assert.match(panel.innerHTML,/Thuốc con ngựa<\/span><strong>1 cây/);
const html = fs.readFileSync(path.join(__dirname,"..","static","index.html"),"utf8");
assert.match(html,/<section id="statistics" class="tab" hidden>/);
assert.match(html,/<select name="zone_id" required>/);
assert.doesNotMatch(source,/data-zone-stats='/);
console.log("Separate zone statistics and product breakdown: OK");
