"""Build the single-file HTML almanac: outputs/almanac_2026.html.

The iOS Weather sunset panel, translated to the house skin (white, Computer
Modern, sober) and made daily: stats card, full-year band chart, and the
"Sunrise and Sunset Averages" list at one row per day instead of per month,
switchable between the four clock conventions and all 25 locations. Fully
offline: data and the matplotlib Computer Modern TTFs are embedded.

  SOLAR_OUT=/some/dir python3 build_almanac.py
"""

import os, json, base64, datetime as dt
import matplotlib
from locations_g20 import LOCATIONS, ORDER
from daily import YEAR, SPA_CUT, DAYS, compute_all
from solar import solar_events

HERE = os.path.dirname(os.path.abspath(__file__))

OUT = os.environ.get("SOLAR_OUT", "/mnt/user-data/outputs")
FONTDIR = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")


def font_b64(name):
    with open(os.path.join(FONTDIR, name), "rb") as f:
        return base64.b64encode(f.read()).decode()


def build_data():
    data = compute_all()
    cities = {}
    for code in ORDER:
        c, r = LOCATIONS[code], data[code]
        days = []
        for i in range(len(DAYS)):
            days.append([int(round(r["dawn_utc"][i])), int(round(r["rise_utc"][i])),
                         int(round(r["set_utc"][i])), int(round(r["dusk_utc"][i])),
                         int(round(r["off_civ"][i]))])
        cities[code] = dict(name=c["name"], lat=c["lat"], lon=c["lon"],
                            tz=c["tz"], us=c["us"], group=c["group"],
                            role=c["role"], airport=c.get("airport", ""),
                            std=int(round(c["std"] * 60)), days=days)
    # per-day declination + equation of time (lat/lon independent), for the
    # picker map's terminator
    sun = []
    for d in DAYS:
        _, _, _, decl, eq = solar_events(d, 0.0, 0.0)
        sun.append([round(decl, 3), round(eq, 2)])
    return dict(year=YEAR, spaCutIdx=(SPA_CUT - dt.date(YEAR, 1, 1)).days,
                order=ORDER, cities=cities, sun=sun)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sonset Almanac</title>
<style>
@font-face{font-family:'CMURoman';src:url(data:font/ttf;base64,@@CMR@@) format('truetype')}
@font-face{font-family:'CMUBold';src:url(data:font/ttf;base64,@@CMB@@) format('truetype')}
@font-face{font-family:'CMUSans';src:url(data:font/ttf;base64,@@CMS@@) format('truetype')}
:root{--ink:#1b3a6b;--cut:#a03020;--grey:#666;--hair:#d8d8d8}
*{box-sizing:border-box}
body{margin:0;background:#fff;color:#1a1a1a;
     font-family:'CMURoman',Georgia,serif;font-size:15px;line-height:1.35}
.wrap{max-width:600px;margin:0 auto;padding:20px 16px 70px}
h1{font-family:'CMUBold',Georgia,serif;font-weight:normal;font-size:24px;margin:0 0 2px}
.sub{color:var(--grey);font-size:13px;margin:0 0 14px}
.controls{border-top:1px solid #333;border-bottom:1px solid var(--hair);padding:10px 0 12px;margin-bottom:14px}
select{font-family:'CMURoman',Georgia,serif;font-size:15px;padding:3px 6px;border:1px solid #999;
       border-radius:3px;background:#fff;color:#1a1a1a;max-width:100%}
.seg{display:flex;gap:0;margin-top:10px;border:1px solid #333;border-radius:3px;overflow:hidden;width:fit-content;max-width:100%}
.seg button{font-family:'CMUSans',Verdana,sans-serif;font-size:12px;padding:6px 10px;border:none;
            background:#fff;color:#1a1a1a;cursor:pointer;border-right:1px solid #333}
.seg button:last-child{border-right:none}
.seg button.on{background:var(--ink);color:#fff}
.vsub{color:var(--grey);font-size:12.5px;margin-top:6px}
.note{border:1px solid var(--hair);border-left:3px solid var(--grey);padding:6px 10px;margin:0 0 14px;
      font-size:13px;color:#333;display:none}
.mapbox{position:relative;margin-top:10px}
.mapbox svg{border:1px solid #333}
.mapcap{color:var(--grey);font-size:12px;margin-top:4px}
.help{display:inline-block;position:relative;margin-left:7px;width:15px;height:15px;
      line-height:15px;text-align:center;border:1px solid #999;border-radius:50%;
      font-size:11px;color:#666;cursor:help;font-family:'CMUSans',Verdana,sans-serif}
.help .helpbox{display:none;position:absolute;bottom:20px;right:-8px;width:300px;
      background:#fff;border:1px solid #888;border-radius:3px;padding:7px 10px;
      font-size:12.5px;line-height:1.45;color:#1a1a1a;z-index:4;text-align:left;
      font-family:'CMURoman',Georgia,serif;cursor:default}
.help:hover .helpbox{display:block}
.help.star{border:none;border-radius:0;width:auto;height:auto;line-height:inherit;
           font-size:15px;vertical-align:super;margin-left:3px;
           font-family:'CMURoman',Georgia,serif}
.bigcard{margin:2px 0 10px}
.bigtime{font-family:'CMUBold',Georgia,serif;font-size:40px;line-height:1.05}
.bigsub{color:var(--grey);font-size:13.5px;margin-top:2px}
.daynav{margin:0 0 10px}
.daynav button{font-family:'CMUSans',Verdana,sans-serif;font-size:12px;padding:3px 10px;margin-right:6px;
               border:1px solid #999;border-radius:3px;background:#fff;cursor:pointer}
.daynav button:hover{background:#f2f2f2}
.daynav button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.daynav button.on:hover{background:var(--ink)}
.speed{margin-left:8px}
table.stats{width:100%;border-collapse:collapse;margin:10px 0 18px}
table.stats td{padding:6px 2px;border-top:1px solid var(--hair);font-size:14.5px}
table.stats td:last-child{text-align:right;font-family:'CMURoman',Georgia,serif}
table.stats tr:first-child td{border-top:1px solid #333}
.shadectl{margin:10px 0 0;color:var(--grey);font-size:12.5px}
.shadectl button{font-family:'CMUSans',Verdana,sans-serif;font-size:11.5px;padding:2px 9px;
                 margin-left:6px;border:1px solid #999;border-radius:3px;background:#fff;cursor:pointer}
.shadectl button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.chartbox{margin:6px 0 4px;position:relative}
svg{display:block;width:100%;height:auto}
.tip{position:absolute;display:none;background:#fff;border:1px solid #888;border-radius:3px;
     padding:5px 9px;font-size:12.5px;line-height:1.5;pointer-events:none;
     white-space:nowrap;z-index:3}
.tip b{font-family:'CMUBold',Georgia,serif;font-weight:normal}
.extremes{color:var(--grey);font-size:12.5px;margin:6px 0 22px}
h2{font-family:'CMUBold',Georgia,serif;font-weight:normal;font-size:18px;margin:18px 0 2px}
.listhead{color:var(--grey);font-size:12.5px;margin:0 0 8px}
.mrow{position:sticky;top:0;background:#fff;border-bottom:1px solid #333;
      font-family:'CMUBold',Georgia,serif;padding:7px 2px 3px;font-size:15px;z-index:2;
      cursor:pointer;display:flex;align-items:baseline;gap:12px;
      -webkit-user-select:none;user-select:none}
.mrow:hover{background:#f6f6f6}
.mrow .mavg{display:none;color:var(--grey);font-size:12.5px;
            font-family:'CMURoman',Georgia,serif}
.mrow.closed .mavg{display:inline}
.mrow .mchev{width:14px;color:#666;font-size:11px;flex:none}
.mbody.closed{display:none}
.dg{font-family:Georgia,serif}
.ampbox{position:relative;margin:6px 0 4px}
.latctl{display:flex;align-items:center;gap:12px;margin:10px 0 2px;flex-wrap:wrap}
.latctl .seg{border:1px solid #333;border-radius:3px;overflow:hidden;display:inline-flex}
.latctl .seg button{font-family:'CMUSans',Verdana,sans-serif;font-size:11.5px;
  padding:4px 9px;border:none;border-right:1px solid #333;background:#fff;cursor:pointer}
.latctl .seg button:last-child{border-right:none}
.latctl .seg button.on{background:var(--ink);color:#fff}
.latctl input[type=range]{flex:1;min-width:140px;accent-color:#1b3a6b}
#latread{font-variant-numeric:tabular-nums;font-size:14px}
.latline{font-size:14.5px;margin:4px 0 2px}
.drow{display:grid;grid-template-columns:46px 46px 1fr 46px;gap:8px;align-items:center;
      padding:2.5px 2px;border-bottom:1px solid #efefef;font-size:13px;cursor:pointer}
.drow:hover{background:#f6f6f6}
.drow.sel{background:#eef1f6}
.drow .d{color:#333;font-variant-numeric:tabular-nums}
.drow .t{font-variant-numeric:tabular-nums}
.track{position:relative;height:7px;background:#f1f1f1;border-radius:2px}
.track .tw,.track .day{position:absolute;top:0;height:100%;border-radius:2px}
.track .tw{background:#cdd7e4}
.track .day{background:var(--ink)}
.track .tick{position:absolute;top:-1px;width:1px;height:9px;background:#d0d0d0}
.cutrow{padding:5px 2px;border-bottom:1px solid #efefef;font-size:12.5px;color:var(--cut)}
.cutrow.grey{color:var(--grey)}
.foot{margin-top:26px;border-top:1px solid #333;padding-top:8px;color:var(--grey);font-size:12px}
</style>
</head>
<body>
<div class="wrap">
  <h1>Sonset Almanac</h1>
  <p class="sub">Variance between time of sunset over the year, @@YEAR@@</p>

  <div class="controls">
    <label>Location:
      <select id="city"></select>
    </label>
    <div class="mapbox" id="map"></div>
    <div class="mapcap"><span id="mapcap"></span><span class="help">?<span
      class="helpbox">The hover card shows the location as code: name; its
      latitude and longitude (city centre, degrees); and a pole scale, which
      is latitude on a linear scale with the equator at 0, the North Pole at
      +1, the South Pole at &#8722;1 (latitude / 90). The map itself is drawn
      at the selected city's sunset instant on the selected date: sunset line
      through the selected dot, dimmed band to civil dusk, full night beyond.
      </span></span></div>
    <div class="shadectl">map:<span id="maptheme"></span></div>
    <div class="seg" id="seg"></div>
    <div class="vsub" id="vsub"></div>
  </div>

  <div class="note" id="scenNote">The Sunshine Protection Act is US federal law;
    it moves no clock here. This view is identical to the civil clock.</div>

  <div class="bigcard">
    <div class="daynav">
      <button id="prevD">&#8592; day</button><button id="nextD">day &#8594;</button><button id="todayD">today</button>
      <button id="playD">play</button><span class="speed" id="speed"><button data-s="1" class="on">1x</button><button data-s="2">2x</button><button data-s="5">5x</button></span>
    </div>
    <div class="bigtime" id="bigTime"></div>
    <div class="bigsub" id="bigSub"></div>
  </div>

  <table class="stats" id="stats"></table>

  <div class="shadectl">shading:<span id="shade"></span></div>
  <div class="chartbox" id="chart"></div>
  <div class="extremes" id="extremes"></div>

  <h2>Sunrise and sunset, daily<span class="help star">*<span class="helpbox">
    Dates in this list are MM/DD.</span></span></h2>
  <p class="listhead" id="listhead"></p>
  <div id="list"></div>

  <h2>Daylight swing vs latitude</h2>
  <p class="listhead">Annual amplitude of daylight length (longest minus
     shortest day) against absolute latitude, all @@NLOC@@ locations. Longitude has
     no say in the swing; it only slides the clock underneath (the
     Kolkata-Mumbai spread). Click a point to switch location.</p>
  <div class="ampbox" id="amp"></div>
  <div class="extremes" id="ampcap"></div>

  <h2>Any latitude</h2>
  <p class="listhead">The same shaded year chart at an arbitrary latitude, on
     local mean solar time (no zone, no DST, sun highest at 12:00 minus the
     equation of time). Slide to explore; polar day and night appear beyond
     the circles.</p>
  <div class="latctl">
    <span class="seg small" id="latmode"><button data-lm="deg" class="on">|&#966;| degrees</button><button data-lm="pole">pole scale</button></span>
    <input type="range" id="latslider">
    <span id="latread"></span><span class="help">?<span class="helpbox">
      Two slider modes: absolute latitude in degrees (0&#8211;90, northern
      hemisphere), or the pole scale, latitude / 90, running &#8722;1 (South
      Pole) through 0 (equator) to +1 (North Pole), linear. The readout shows
      pole value first, exact degrees in parentheses. The chart uses local
      mean solar time, so it is pure astronomy: no time zone, no DST, no
      longitude. Closest major city is nearest by signed latitude among the
      @@NLOC@@ locations in this almanac.</span></span>
  </div>
  <div class="latline" id="latline"></div>
  <div class="chartbox" id="latchart"></div>

  <div class="foot" id="foot"></div>
</div>
<script>
const DATA = @@DATA@@;
const LAND = "@@LAND@@";
const LIGHTS = @@LIGHTS@@;
const N = DATA.cities[DATA.order[0]].days.length;
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const DOW = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
const MLEN = [31,28,31,30,31,30,31,31,30,31,30,31];
const VARIANTS = [
  {id:"std",  label:"standard",     sub:"Standard time, DST ignored: pure astronomy plus a constant."},
  {id:"civ",  label:"civil",        sub:"The wall clock as lived, DST and whatnot included; cuts are marked."},
  {id:"spaA", label:"SPA as-lived", sub:"Scenario: Sunshine Protection Act enacted before 1 Nov @@YEAR@@; the November fall-back never happens. US locations only."},
  {id:"spaS", label:"SPA steady",   sub:"Scenario: permanent DST all year, the steady state from 2027 on. US locations only."}];

const dayDate = i => new Date(Date.UTC(DATA.year,0,1+i));
const fmtDate = i => { const d=dayDate(i); return DOW[d.getUTCDay()]+" "+d.getUTCDate()+" "+MONTHS[d.getUTCMonth()]; };
const shortDate = i => { const d=dayDate(i); return d.getUTCDate()+" "+MONTHS[d.getUTCMonth()]; };
const mmdd = i => { const d=dayDate(i); return pad(d.getUTCMonth()+1)+"/"+pad(d.getUTCDate()); };
const pad = n => (n<10?"0":"")+n;
const fmt = m => { m=((Math.round(m)%1440)+1440)%1440; return pad(Math.floor(m/60))+":"+pad(m%60); };
const fmtDur = m => Math.floor(m/60)+" h "+pad(Math.round(m%60))+" min";
const fmtOff = m => { const s=m<0?"-":"+", a=Math.abs(m); return "UTC"+s+Math.floor(a/60)+(a%60? ":"+pad(a%60):""); };

function offFor(c,i,v){
  const civ=c.days[i][4];
  if(v==="std") return c.std;
  if(v==="civ"||!c.us) return civ;
  if(v==="spaS") return c.std+60;
  return i>=DATA.spaCutIdx ? c.std+60 : civ;
}
const ev = (c,i,v,k) => c.days[i][k]+offFor(c,i,v);   // k: 0 dawn 1 rise 2 set 3 dusk

let state = {city:"SEA", variant:"civ", day:0, speed:1, shade:"none",
             mapTheme:"atlas"};

// map themes: day water/land, dusk overlay, night water/land, lights, terminator
const THEMES={
 atlas:     {dayW:"#204a5e",dayL:"#eae9e5",stroke:null,     duskF:"#0a161d",duskO:0.38,
             nightW:"#0e2430",nightL:"#1d1d1d",lights:"#ffd98c",lightsO:0.9,
             term:"#ffffff",termO:0.55},
 ink:       {dayW:"#ffffff",dayL:"#d8d8d8",stroke:"#555555",duskF:"#000000",duskO:0.22,
             nightW:"#5a5a5a",nightL:"#262626",lights:"#ffffff",lightsO:0.95,
             term:"#000000",termO:0.4},
 marble:    {dayW:"#31709f",dayL:"#7a9a63",stroke:null,     duskF:"#041018",duskO:0.42,
             nightW:"#050f1a",nightL:"#0b0b0b",lights:"#ffd98c",lightsO:1.0,
             term:"#ffffff",termO:0.5},
 parchment: {dayW:"#e7dcc2",dayL:"#c9b283",stroke:"#8a6f47",duskF:"#2e2213",duskO:0.30,
             nightW:"#4a3b24",nightL:"#2f2415",lights:"#ffcf70",lightsO:0.95,
             term:"#5c4426",termO:0.6},
 neon:      {dayW:"#101828",dayL:"#1b2a4a",stroke:"#3fe0d0",duskF:"#000000",duskO:0.45,
             nightW:"#04060f",nightL:"#0a0e1c",lights:"#ff5fd7",lightsO:1.0,
             term:"#3fe0d0",termO:0.8},
 contrast:  {dayW:"#ffffff",dayL:"#f4f4f4",stroke:"#111111",duskF:"#000000",duskO:0.35,
             nightW:"#000000",nightL:"#000000",lights:"#ffffff",lightsO:1.0,
             term:"#888888",termO:0.8}};
(function(){ const t=new Date();
  let i=Math.round((Date.UTC(t.getFullYear(),t.getMonth(),t.getDate())-Date.UTC(DATA.year,0,1))/86400000);
  state.day=Math.max(0,Math.min(N-1,i)); })();

function cuts(c,v){
  const out=[];
  for(let i=1;i<N;i++){
    const a=offFor(c,i-1,v), b=offFor(c,i,v);
    if(a!==b) out.push({i:i, jump:(b-a)/60});
  }
  return out;
}

// ---- day/night picker map -------------------------------------------------
// Terminator: solve sin(decl)sin(phi)+cos(decl)cos(phi)cos(lon-lss)=cos(z)
// per longitude column; z=90.833 is the package's sunset horizon (the line
// passes through the selected city at its sunset), z=96 is civil dusk.
// The map is drawn at the UTC instant of the selected city's sunset on the
// selected day, so changing the date (or city) moves the curve.
// Night region = spherical cap of radius 180-z around the antisolar point.
// The cap edge is parameterized directly (bearing sweep from the cap centre),
// which avoids per-longitude branch ambiguity entirely. Longitudes are
// unwrapped by continuity; the plotted copies at 0 and +-360 cover the seam.
function capPts(z,i,t){
  const su=DATA.sun[i], d=su[0]*Math.PI/180, eq=su[1];
  const lss=(720-t-eq)/4;
  const lat0=-d, lon0=lss+180;                     // antisolar point
  const r=(180-z)*Math.PI/180;
  const pts=[]; let prev=null, off=0;
  for(let tt=0;tt<=360;tt+=1.5){
    const th=tt*Math.PI/180;
    const sphi=Math.sin(lat0)*Math.cos(r)+Math.cos(lat0)*Math.sin(r)*Math.cos(th);
    const phi=Math.asin(Math.max(-1,Math.min(1,sphi)));
    const dlon=Math.atan2(Math.sin(th)*Math.sin(r)*Math.cos(lat0),
                          Math.cos(r)-Math.sin(lat0)*sphi);
    let lam=lon0+dlon*180/Math.PI;
    if(prev!==null){
      while(lam+off-prev>180)off-=360;
      while(lam+off-prev<-180)off+=360;
    }
    lam+=off; prev=lam;
    pts.push([lam,-phi*180/Math.PI]);
  }
  return pts;
}
const sub=(pts,dx)=>"M"+pts.map(p=>(p[0]+dx).toFixed(1)+" "+p[1].toFixed(1)).join("L");
function nightPath(z,i,t){
  const decl=DATA.sun[i][0], r=180-z, pts=capPts(z,i,t);
  if(r+Math.abs(decl)>=90){
    // cap swallows the winter pole: curve is a wave spanning 360 deg of
    // longitude; sort by longitude and close along that pole's map edge
    const w=pts.slice().sort((a,b)=>a[0]-b[0]);
    const edge=decl>=0?61:-76;
    const lo=w[0][0];
    // duplicate the wave one period to the left and right so [-180,180] is
    // covered wherever the unwrapped span happens to sit
    const w3=w.map(p=>[p[0]-360,p[1]]).concat(w.map(p=>[p[0],p[1]]),
                                              w.map(p=>[p[0]+360,p[1]]));
    let path="M"+w3.map(p=>p[0].toFixed(1)+" "+p[1].toFixed(1)).join("L");
    path+="L"+(lo+720).toFixed(1)+" "+edge+"L"+(lo-360).toFixed(1)+" "+edge+"Z";
    return path;
  }
  // detached deep-night blob (near the equinoxes for the civil-dusk cap):
  // closed polygon, drawn at three longitude offsets to cover the seam
  return sub(pts,0)+"Z "+sub(pts,-360)+"Z "+sub(pts,360)+"Z";
}
function termStroke(i,t){
  const pts=capPts(90.833,i,t);
  return sub(pts,0)+sub(pts,-360)+sub(pts,360);
}

function renderMap(){
  const c=DATA.cities[state.city], i=state.day, t=c.days[i][2];  // sunset, UTC min
  let s='<svg viewBox="-180 -75 360 135" xmlns="http://www.w3.org/2000/svg">';
  s+='<defs><clipPath id="cpDusk"><path id="cpDuskP" d="'+nightPath(90.833,i,t)+'"/></clipPath>';
  s+='<clipPath id="cpNight"><path id="cpNightP" d="'+nightPath(96,i,t)+'"/></clipPath></defs>';
  const T=THEMES[state.mapTheme]||THEMES.atlas;
  const strokeAttr=T.stroke?(' stroke="'+T.stroke+'" stroke-width="0.25"'):"";
  s+='<rect x="-180" y="-75" width="360" height="135" fill="'+T.dayW+'"/>';
  s+='<path d="'+LAND+'" fill="'+T.dayL+'" fill-rule="evenodd"'+strokeAttr+'/>';
  s+='<g clip-path="url(#cpDusk)"><rect x="-180" y="-75" width="360" height="135" fill="'+T.duskF+'" opacity="'+T.duskO+'"/></g>';
  s+='<g clip-path="url(#cpNight)">';
  s+='<rect x="-180" y="-75" width="360" height="135" fill="'+T.nightW+'"/>';
  s+='<path d="'+LAND+'" fill="'+T.nightL+'" fill-rule="evenodd"/>';
  s+=LIGHTS.map(l=>'<circle cx="'+l[0]+'" cy="'+(-l[1])+'" r="0.55" fill="'+T.lights+'" opacity="'+T.lightsO+'"/>').join("");
  s+='</g>';
  s+='<path id="termLine" d="'+termStroke(i,t)+'" fill="none" stroke="'+T.term+'" stroke-opacity="'+T.termO+'" stroke-width="0.5"/>';
  for(const code of DATA.order){
    const cc=DATA.cities[code], sel=code===state.city;
    s+='<circle cx="'+cc.lon+'" cy="'+(-cc.lat)+'" r="'+(sel?3:1.9)+
       '" fill="'+(sel?"#fff":"#1b3a6b")+'" stroke="'+(sel?"#1b3a6b":"#fff")+
       '" stroke-width="'+(sel?1.2:0.55)+'"/>';
  }
  s+='</svg>';
  const box=document.getElementById("map");
  box.innerHTML=s+'<div class="tip" id="mtip"></div>';
  const svg=box.firstChild, mtip=document.getElementById("mtip");
  const near=e=>{
    const r=svg.getBoundingClientRect();
    const x=(e.clientX-r.left)/r.width*360-180, y=(e.clientY-r.top)/r.height*135-75;
    let best=null,bd=49;
    for(const code of DATA.order){
      const cc=DATA.cities[code];
      const d=(cc.lon-x)*(cc.lon-x)+(-cc.lat-y)*(-cc.lat-y);
      if(d<bd){bd=d;best=code;}
    }
    return best;
  };
  svg.addEventListener("mousemove",e=>{
    const code=near(e);
    svg.style.cursor=code?"pointer":"default";
    if(!code){mtip.style.display="none";return;}
    const cc=DATA.cities[code];
    const ns=cc.lat>=0?"N":"S", ew=cc.lon>0?"E":"W";
    const pole=cc.lat/90;
    mtip.innerHTML="<b>"+code+": "+cc.name+"</b><br>"+
      Math.abs(cc.lat).toFixed(2)+'<span class="dg">&#176;</span> '+ns+", "+
      Math.abs(cc.lon).toFixed(2)+'<span class="dg">&#176;</span> '+ew+"<br>"+
      "pole scale "+(pole>=0?"+":"&#8722;")+Math.abs(pole).toFixed(3);
    mtip.style.display="block";
    const br=box.getBoundingClientRect();
    let tx=e.clientX-br.left+12, ty=e.clientY-br.top+12;
    if(tx+mtip.offsetWidth>br.width-4)tx=e.clientX-br.left-mtip.offsetWidth-12;
    mtip.style.left=tx+"px"; mtip.style.top=ty+"px";
  });
  svg.addEventListener("mouseleave",()=>{mtip.style.display="none";});
  svg.addEventListener("click",e=>{
    const code=near(e);
    if(code&&code!==state.city){
      state.city=code;
      document.getElementById("city").value=code;
      renderAll();
    }
  });
  document.getElementById("mapcap").textContent=mapCaption(c,i);
}

function mapCaption(c,i){
  return "Day and night at the moment of "+c.name+"'s sunset, "+fmtDate(i)+" "+
    DATA.year+" · dimmed band runs to civil dusk · night lights are "+
    "Natural Earth populated places · click a dot to switch location";
}

// day-only updates: move the chart marker and re-aim the terminator without
// rebuilding either SVG, so playback stays cheap
function updateChartSel(){
  const l=document.getElementById("selLine"), d=document.getElementById("selDot");
  if(!l||!d)return;
  const c=DATA.cities[state.city], x=chX(state.day);
  l.setAttribute("x1",x); l.setAttribute("x2",x);
  d.setAttribute("cx",x);
  d.setAttribute("cy",chY(ev(c,state.day,state.variant,2)));
}
function updateMapDay(){
  const p=document.getElementById("cpDuskP");
  if(!p){renderMap();return;}
  const c=DATA.cities[state.city], i=state.day, t=c.days[i][2];
  p.setAttribute("d",nightPath(90.833,i,t));
  document.getElementById("cpNightP").setAttribute("d",nightPath(96,i,t));
  document.getElementById("termLine").setAttribute("d",termStroke(i,t));
  document.getElementById("mapcap").textContent=mapCaption(c,i);
}

function refresh(){
  renderDay();
  updateChartSel();
  updateMapDay();
  markSel();
}

// ---- daylight-swing vs latitude (the amplitude correlation) --------------
let ampCache=null;
function ampData(){
  if(ampCache)return ampCache;
  const pts=DATA.order.map(code=>{
    const c=DATA.cities[code];
    let mx=-1e9,mn=1e9;
    for(let i=0;i<N;i++){
      const dl=c.days[i][2]-c.days[i][1];
      if(dl>mx)mx=dl; if(dl<mn)mn=dl;
    }
    return {code, phi:Math.abs(c.lat), A:(mx-mn)/60, south:c.lat<0};
  });
  const xs=pts.map(p=>Math.tan(p.phi*Math.PI/180)), ys=pts.map(p=>p.A);
  const n=xs.length, sx=xs.reduce((a,b)=>a+b,0), sy=ys.reduce((a,b)=>a+b,0);
  const sxx=xs.reduce((a,b)=>a+b*b,0),
        sxy=xs.reduce((a,b,i)=>a+b*ys[i],0);
  const b=(n*sxy-sx*sy)/(n*sxx-sx*sx), a=(sy-b*sx)/n, yb=sy/n;
  const ssr=ys.reduce((s,y,i)=>s+Math.pow(y-(a+b*xs[i]),2),0);
  const sst=ys.reduce((s,y)=>s+Math.pow(y-yb,2),0);
  ampCache={pts,a,b,r2:1-ssr/sst};
  return ampCache;
}
const A_exact=phi=>(4/15)*(180/Math.PI)*
  Math.asin(Math.tan(phi*Math.PI/180)*Math.tan(23.44*Math.PI/180));
function renderAmp(){
  const {pts,a,b,r2}=ampData();
  const W=560,H=300,ml=42,mr=14,mt=10,mb=34,iw=W-ml-mr,ih=H-mt-mb;
  const XMAX=60,YMAX=14;
  const X=p=>ml+iw*p/XMAX, Y=A=>mt+ih*(1-A/YMAX);
  let s='<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg">';
  for(let g=0;g<=XMAX;g+=10){
    s+='<line x1="'+X(g)+'" x2="'+X(g)+'" y1="'+mt+'" y2="'+(H-mb)+'" stroke="#ececec"/>';
    s+='<text x="'+X(g)+'" y="'+(H-mb+14)+'" text-anchor="middle" font-size="9" fill="#666" font-family="CMUSans,Verdana,sans-serif">'+g+'</text>';
  }
  for(let g=0;g<=YMAX;g+=2){
    s+='<line y1="'+Y(g)+'" y2="'+Y(g)+'" x1="'+ml+'" x2="'+(W-mr)+'" stroke="#ececec"/>';
    s+='<text x="'+(ml-6)+'" y="'+(Y(g)+3)+'" text-anchor="end" font-size="9" fill="#666" font-family="CMUSans,Verdana,sans-serif">'+g+'</text>';
  }
  const curve=(f,dash)=>{
    let p="",started=false;
    for(let phi=0;phi<=59.9;phi+=0.5){
      const A=f(phi);
      if(A>YMAX||isNaN(A)){if(started)break;else continue;}
      p+=(started?"L":"M")+X(phi).toFixed(1)+" "+Y(A).toFixed(1); started=true;
    }
    return '<path d="'+p+'" fill="none" stroke="'+(dash?"#999":"#333")+
           '" stroke-width="1.2"'+(dash?' stroke-dasharray="5 4"':'')+'/>';
  };
  s+=curve(A_exact,false);
  s+=curve(phi=>a+b*Math.tan(phi*Math.PI/180),true);
  for(const p of pts){
    const sel=p.code===state.city;
    s+='<circle data-code="'+p.code+'" cx="'+X(p.phi)+'" cy="'+Y(p.A)+
       '" r="'+(sel?5:3.4)+'" fill="'+(p.south?"#fff":"#1b3a6b")+
       '" stroke="'+(sel?"#a03020":"#1b3a6b")+'" stroke-width="'+(sel?1.6:1)+
       '" style="cursor:pointer"/>';
    if(sel)s+='<text x="'+(X(p.phi)+8)+'" y="'+(Y(p.A)-6)+'" font-size="10" fill="#1a1a1a">'+
              p.code+" "+p.A.toFixed(2)+' h</text>';
  }
  s+='<rect x="'+ml+'" y="'+mt+'" width="'+iw+'" height="'+ih+'" fill="none" stroke="#333"/>';
  s+='</svg>';
  const box=document.getElementById("amp");
  box.innerHTML=s+'<div class="tip" id="atip"></div>';
  const svg=box.firstChild, atip=document.getElementById("atip");
  svg.querySelectorAll("circle").forEach(el=>{
    el.addEventListener("click",()=>{
      state.city=el.dataset.code;
      document.getElementById("city").value=state.city;
      renderAll();
    });
    el.addEventListener("mouseenter",e=>{
      const p=pts.find(q=>q.code===el.dataset.code);
      atip.innerHTML="<b>"+DATA.cities[p.code].name+" ("+p.code+")</b><br>"+
        "|<i>&#966;</i>| "+p.phi.toFixed(2)+'<span class="dg">&#176;</span> &#183; swing '+
        p.A.toFixed(2)+" h";
      atip.style.display="block";
      const br=box.getBoundingClientRect(), r=el.getBoundingClientRect();
      let tx=r.left-br.left+12, ty=r.top-br.top-34;
      if(tx+180>br.width)tx-=190;
      atip.style.left=tx+"px"; atip.style.top=Math.max(0,ty)+"px";
    });
    el.addEventListener("mouseleave",()=>{atip.style.display="none";});
  });
  document.getElementById("ampcap").innerHTML=
    'solid: exact, <i>A</i> = (4/15) arcsin(tan <i>&#966;</i> tan <i>&#949;</i>), '+
    '<i>&#949;</i> = 23.44<span class="dg">&#176;</span> &#183; dashed: OLS on tan <i>&#966;</i>, '+
    '<i>A</i> = '+a.toFixed(2)+" + "+b.toFixed(2)+' tan <i>&#966;</i> h, '+
    'r<sup>2</sup> = '+r2.toFixed(4)+', equator intercept '+a.toFixed(2)+
    ' h (the raw-latitude line’s was −1.36 h) &#183; open points: southern '+
    'hemisphere at |<i>&#966;</i>| &#183; computed from the minute-rounded '+
    'times embedded here; fig_amplitude_vs_latitude_g20.png uses exact minutes';
}

// playback: step one day per tick, wrap at New Year; 1x = 4 days/s
let playTimer=null;
function setPlay(on){
  const b=document.getElementById("playD");
  if(playTimer){clearInterval(playTimer); playTimer=null;}
  if(on){
    playTimer=setInterval(()=>{state.day=(state.day+1)%N; refresh();},
                          250/state.speed);
    b.textContent="pause"; b.classList.add("on");
  } else {
    b.textContent="play"; b.classList.remove("on");
  }
}

// ---- arbitrary-latitude explorer -----------------------------------------
// Mean-solar clock: LMT here is UTC at lon 0, hour angle H = (m + eq)/4 - 180.
let latState={mode:"deg", phi:47.6062};
function latRiseSet(phi){
  const out=[];
  const p=phi*Math.PI/180;
  for(let i=0;i<N;i++){
    const decl=DATA.sun[i][0]*Math.PI/180, eq=DATA.sun[i][1];
    const noon=720-eq;
    const row={};
    for(const [key,z] of [["r",90.833],["t",96]]){
      const cosH=Math.cos(z*Math.PI/180)/(Math.cos(p)*Math.cos(decl))
                 -Math.tan(p)*Math.tan(decl);
      if(cosH>1){row[key]=null;}                    // polar night at this zenith
      else if(cosH<-1){row[key]="all";}             // midnight sun
      else{
        const H=Math.acos(cosH)*180/Math.PI*4;
        row[key]=[noon-H, noon+H];
      }
    }
    out.push(row);
  }
  return out;
}
function shadeLatURL(phi){
  const rows=192, cv=document.createElement("canvas");
  cv.width=N; cv.height=rows;
  const ctx=cv.getContext("2d"), img=ctx.createImageData(N,rows);
  const p=phi*Math.PI/180;
  for(let x=0;x<N;x++){
    const decl=DATA.sun[x][0]*Math.PI/180, eq=DATA.sun[x][1];
    for(let y=0;y<rows;y++){
      const m=(y+0.5)*1440/rows;
      const H=((m+eq)/4-180)*Math.PI/180;
      const alt=Math.asin(Math.sin(p)*Math.sin(decl)+
                Math.cos(p)*Math.cos(decl)*Math.cos(H))*180/Math.PI;
      const [r,g,b]=skyColor(alt), k=(y*N+x)*4;
      img.data[k]=r; img.data[k+1]=g; img.data[k+2]=b; img.data[k+3]=255;
    }
  }
  ctx.putImageData(img,0,0);
  return cv.toDataURL();
}
function segsPath(rs,key,which){
  let s="",open=false;
  for(let i=0;i<N;i++){
    const v=rs[i][key];
    if(v===null||v==="all"){open=false;continue;}
    s+=(open?"L":"M")+chX(i).toFixed(1)+" "+chY(v[which]).toFixed(1);
    open=true;
  }
  return s;
}
function renderLat(){
  const phi=latState.phi, rs=latRiseSet(phi);
  const W=CW,H=CH,ml=CML,mr=CMR,mt=CMT,mb=CMB,iw=CIW,ih=CIH;
  let s='<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg">';
  s+='<rect x="'+ml+'" y="'+mt+'" width="'+iw+'" height="'+ih+'" fill="#fff"/>';
  try{
    s+='<image x="'+ml+'" y="'+mt+'" width="'+iw+'" height="'+ih+
       '" preserveAspectRatio="none" href="'+shadeLatURL(phi)+'"/>';
  }catch(e){}
  for(const [key,w,op] of [["t",0.8,0.4],["r",1.2,0.9]]){
    s+='<path d="'+segsPath(rs,key,0)+'" fill="none" stroke="#1b3a6b" stroke-width="'+w+'" stroke-opacity="'+op+'"/>';
    s+='<path d="'+segsPath(rs,key,1)+'" fill="none" stroke="#1b3a6b" stroke-width="'+w+'" stroke-opacity="'+op+'"/>';
  }
  for(let h=0;h<=24;h+=6){
    s+='<text x="'+(ml-5)+'" y="'+(chY(h*60)+3)+'" text-anchor="end" font-size="9" fill="#666" font-family="CMUSans,Verdana,sans-serif">'+pad(h)+'</text>';
  }
  let acc=0;
  for(let m=0;m<12;m++){
    s+='<text x="'+chX(acc+14)+'" y="'+(H-mb+13)+'" text-anchor="middle" font-size="9" fill="#666" font-family="CMUSans,Verdana,sans-serif">'+MONTHS[m]+'</text>';
    acc+=MLEN[m];
  }
  s+='<rect x="'+ml+'" y="'+mt+'" width="'+iw+'" height="'+ih+'" fill="none" stroke="#333"/>';
  s+='</svg>';
  document.getElementById("latchart").innerHTML=s;
  const pole=phi/90, sg=v=>(v>=0?"+":"&#8722;")+Math.abs(v).toFixed(3);
  document.getElementById("latread").innerHTML=
    sg(pole)+" ("+(phi>=0?"":"&#8722;")+Math.abs(phi).toFixed(6)+'<span class="dg">&#176;</span>)';
  let best=null,bd=1e9;
  for(const code of DATA.order){
    const d=Math.abs(DATA.cities[code].lat-phi);
    if(d<bd){bd=d;best=code;}
  }
  document.getElementById("latline").textContent=
    "Closest Major City: "+DATA.cities[best].name;
}
let latRAF=false;
function latQueue(){
  if(latRAF)return; latRAF=true;
  requestAnimationFrame(()=>{latRAF=false; renderLat();});
}
function initLat(){
  const sl=document.getElementById("latslider");
  const setRange=()=>{
    if(latState.mode==="deg"){
      sl.min=0; sl.max=90; sl.step=0.05; sl.value=Math.abs(latState.phi);
    } else {
      sl.min=-1; sl.max=1; sl.step=0.001; sl.value=latState.phi/90;
    }
  };
  setRange();
  sl.addEventListener("input",()=>{
    const v=parseFloat(sl.value);
    if(isNaN(v))return;
    latState.phi=latState.mode==="deg"?v:v*90;
    latQueue();
  });
  document.querySelectorAll("#latmode button").forEach(b=>{
    b.onclick=()=>{
      latState.mode=b.dataset.lm;
      document.querySelectorAll("#latmode button").forEach(x=>
        x.classList.toggle("on",x===b));
      setRange();
      latQueue();
    };
  });
  renderLat();
}

function renderControls(){
  const sel=document.getElementById("city");
  sel.innerHTML="";
  DATA.order.slice().sort().forEach(code=>{
    const o=document.createElement("option"); o.value=code;
    o.textContent=code+": "+DATA.cities[code].name;
    sel.appendChild(o);
  });
  sel.value=state.city;
  sel.onchange=()=>{state.city=sel.value; renderAll();};
  const seg=document.getElementById("seg");
  seg.innerHTML="";
  VARIANTS.forEach(v=>{
    const b=document.createElement("button");
    b.textContent=v.label; b.dataset.v=v.id;
    b.onclick=()=>{state.variant=v.id; renderAll();};
    seg.appendChild(b);
  });
  const mt=document.getElementById("maptheme");
  mt.innerHTML="";
  Object.keys(THEMES).forEach(id=>{
    const b=document.createElement("button");
    b.textContent=id; b.dataset.mt=id;
    if(id===state.mapTheme)b.classList.add("on");
    b.onclick=()=>{
      state.mapTheme=id;
      document.querySelectorAll("#maptheme button").forEach(x=>
        x.classList.toggle("on",x.dataset.mt===id));
      renderMap();
    };
    mt.appendChild(b);
  });
  const sh=document.getElementById("shade");
  sh.innerHTML="";
  [["none","off"],["bw","day-night"],["sky","sky"]].forEach(([id,label])=>{
    const b=document.createElement("button");
    b.textContent=label; b.dataset.sh=id;
    if(id===state.shade)b.classList.add("on");
    b.onclick=()=>{
      state.shade=id;
      document.querySelectorAll("#shade button").forEach(x=>
        x.classList.toggle("on",x.dataset.sh===id));
      renderChart(DATA.cities[state.city],state.variant);
    };
    sh.appendChild(b);
  });
}

const CW=560,CH=240,CML=34,CMR=10,CMT=8,CMB=22,CIW=CW-CML-CMR,CIH=CH-CMT-CMB;
const chX=i=>CML+CIW*i/(N-1), chY=m=>CMT+CIH*m/1440;

// ---- altitude-shading overlays for the year chart ------------------------
// One pixel column per day, 7.5-minute rows; sun altitude at that local
// clock time under the active clock variant (so DST cuts shear the raster
// exactly like the band). "bw": white at full day, black at full night.
// "sky": dark blue night, orange at dawn/dusk, yellow to near-white day.
const SKY=[[-18,8,21,39],[-8,27,58,94],[-3,196,98,42],[2,240,178,80],
           [10,250,225,150],[30,253,248,235],[60,255,255,255]];
function skyColor(alt){
  const a=Math.max(SKY[0][0],Math.min(SKY[SKY.length-1][0],alt));
  for(let k=1;k<SKY.length;k++){
    if(a<=SKY[k][0]){
      const u=(a-SKY[k-1][0])/(SKY[k][0]-SKY[k-1][0]);
      return [0,1,2].map(j=>Math.round(SKY[k-1][j+1]+u*(SKY[k][j+1]-SKY[k-1][j+1])));
    }
  }
  return [255,255,255];
}
function shadeDataURL(c,v,mode){
  const rows=192, cv=document.createElement("canvas");
  cv.width=N; cv.height=rows;
  const ctx=cv.getContext("2d"), img=ctx.createImageData(N,rows);
  const lat=c.lat*Math.PI/180;
  for(let x=0;x<N;x++){
    const su=DATA.sun[x], decl=su[0]*Math.PI/180, eq=su[1];
    const off=offFor(c,x,v);
    for(let y=0;y<rows;y++){
      const m=(y+0.5)*1440/rows;                    // local clock minutes
      const H=(((m-off)+eq+4*c.lon)/4-180)*Math.PI/180;   // hour angle
      const alt=Math.asin(Math.sin(lat)*Math.sin(decl)+
                Math.cos(lat)*Math.cos(decl)*Math.cos(H))*180/Math.PI;
      let r,g,b;
      if(mode==="bw"){
        let s=Math.max(0,Math.min(1,(alt+16)/24));  // black by -16, white by +8
        s=s*s*(3-2*s);
        r=g=b=Math.round(255*s);
      } else {
        [r,g,b]=skyColor(alt);
      }
      const k=(y*N+x)*4;
      img.data[k]=r; img.data[k+1]=g; img.data[k+2]=b; img.data[k+3]=255;
    }
  }
  ctx.putImageData(img,0,0);
  return cv.toDataURL();
}
function renderChart(c,v){
  const W=CW,H=CH,ml=CML,mr=CMR,mt=CMT,mb=CMB,iw=CIW,ih=CIH;
  const X=chX, Y=chY;
  function poly(k1,k2){
    let p="";
    for(let i=0;i<N;i++) p+=(i?"L":"M")+X(i).toFixed(1)+" "+Y(ev(c,i,v,k1)).toFixed(1);
    for(let i=N-1;i>=0;i--) p+="L"+X(i).toFixed(1)+" "+Y(ev(c,i,v,k2)).toFixed(1);
    return p+"Z";
  }
  let s='<svg viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg">';
  s+='<rect x="'+ml+'" y="'+mt+'" width="'+iw+'" height="'+ih+'" fill="#fff" stroke="none"/>';
  for(let h=0;h<=24;h+=6){
    s+='<line x1="'+ml+'" x2="'+(W-mr)+'" y1="'+Y(h*60)+'" y2="'+Y(h*60)+'" stroke="#e2e2e2" stroke-width="1"/>';
    s+='<text x="'+(ml-5)+'" y="'+(Y(h*60)+3)+'" text-anchor="end" font-size="9" fill="#666" font-family="CMUSans,Verdana,sans-serif">'+pad(h)+'</text>';
  }
  let acc=0;
  for(let m=0;m<12;m++){
    s+='<line y1="'+mt+'" y2="'+(H-mb)+'" x1="'+X(acc)+'" x2="'+X(acc)+'" stroke="#efefef" stroke-width="1"/>';
    s+='<text x="'+X(acc+14)+'" y="'+(H-mb+13)+'" text-anchor="middle" font-size="9" fill="#666" font-family="CMUSans,Verdana,sans-serif">'+MONTHS[m]+'</text>';
    acc+=MLEN[m];
  }
  s+='<path d="'+poly(0,3)+'" fill="#1b3a6b" fill-opacity="0.13"/>';
  s+='<path d="'+poly(1,2)+'" fill="#1b3a6b" fill-opacity="0.42"/>';
  if(state.shade!=="none"){
    try{
      s+='<image x="'+ml+'" y="'+mt+'" width="'+iw+'" height="'+ih+
         '" preserveAspectRatio="none" opacity="0.85" href="'+
         shadeDataURL(c,v,state.shade)+'"/>';
    }catch(e){}  // no canvas (non-browser); overlay is cosmetic, skip
  }
  cuts(c,v).forEach(t=>{
    s+='<line y1="'+mt+'" y2="'+(H-mb)+'" x1="'+X(t.i)+'" x2="'+X(t.i)+'" stroke="#a03020" stroke-width="1" stroke-dasharray="3 3"/>';
  });
  if(c.us&&v==="spaA"){
    s+='<line y1="'+mt+'" y2="'+(H-mb)+'" x1="'+X(DATA.spaCutIdx)+'" x2="'+X(DATA.spaCutIdx)+'" stroke="#888" stroke-width="1" stroke-dasharray="1.5 3"/>';
  }
  s+='<line id="selLine" y1="'+mt+'" y2="'+(H-mb)+'" x1="'+X(state.day)+'" x2="'+X(state.day)+'" stroke="#111" stroke-width="1"/>';
  s+='<circle id="selDot" cx="'+X(state.day)+'" cy="'+Y(ev(c,state.day,v,2))+'" r="3" fill="#111"/>';
  s+='<rect x="'+ml+'" y="'+mt+'" width="'+iw+'" height="'+ih+'" fill="none" stroke="#333" stroke-width="1"/>';
  s+='<line id="hovLine" y1="'+mt+'" y2="'+(H-mb)+'" x1="0" x2="0" stroke="#8a8a8a" stroke-width="1" style="display:none"/>';
  s+='<circle id="hovDot" r="3" fill="#8a8a8a" style="display:none"/>';
  s+='</svg>';
  const box=document.getElementById("chart");
  box.innerHTML=s+'<div class="tip" id="tip"></div>';
  const svg=box.firstChild;
  svg.style.cursor="crosshair";
  const dayAt=e=>{
    const r=svg.getBoundingClientRect();
    const px=(e.clientX-r.left)/r.width*W;
    if(px<ml-2||px>W-mr+2)return -1;
    const i=Math.round((px-ml)/iw*(N-1));
    return (i>=0&&i<N)?i:-1;
  };
  svg.addEventListener("click",e=>{
    const i=dayAt(e);
    if(i>=0){state.day=i; refresh();}
  });
  const tip=document.getElementById("tip"),
        hovLine=document.getElementById("hovLine"),
        hovDot=document.getElementById("hovDot");
  const hideHover=()=>{hovLine.style.display="none";hovDot.style.display="none";
                       tip.style.display="none";};
  svg.addEventListener("mousemove",e=>{
    const i=dayAt(e);
    if(i<0){hideHover();return;}
    const x=X(i);
    hovLine.setAttribute("x1",x); hovLine.setAttribute("x2",x);
    hovLine.style.display="";
    hovDot.setAttribute("cx",x); hovDot.setAttribute("cy",Y(ev(c,i,v,2)));
    hovDot.style.display="";
    tip.innerHTML="<b>"+fmtDate(i)+" "+DATA.year+"</b><br>"+
      "sunrise: "+fmt(ev(c,i,v,1))+"<br>"+
      "sunset: "+fmt(ev(c,i,v,2))+"<br>"+
      "day length: "+fmtDur(c.days[i][2]-c.days[i][1]);
    tip.style.display="block";
    const br=box.getBoundingClientRect();
    let tx=e.clientX-br.left+14, ty=e.clientY-br.top+14;
    if(tx+tip.offsetWidth>br.width-4) tx=e.clientX-br.left-tip.offsetWidth-14;
    if(ty+tip.offsetHeight>br.height-2) ty=e.clientY-br.top-tip.offsetHeight-10;
    tip.style.left=tx+"px"; tip.style.top=ty+"px";
  });
  svg.addEventListener("mouseleave",hideHover);
}

function renderDay(){
  const c=DATA.cities[state.city], v=state.variant, i=state.day;
  const set=ev(c,i,v,2), rise=ev(c,i,v,1), dawn=ev(c,i,v,0), dusk=ev(c,i,v,3);
  document.getElementById("bigTime").textContent=fmt(set);
  document.getElementById("bigSub").textContent=
    "Sunset, "+fmtDate(i)+" "+DATA.year+" · daylight "+fmtDur(c.days[i][2]-c.days[i][1]);
  const rows=[["First light",fmt(dawn)],["Sunrise",fmt(rise)],["Sunset",fmt(set)],
    ["Last light",fmt(dusk)],["Total daylight",fmtDur(c.days[i][2]-c.days[i][1])],
    ["Clock this day",fmtOff(offFor(c,i,v))]];
  document.getElementById("stats").innerHTML=
    rows.map(r=>"<tr><td>"+r[0]+"</td><td>"+r[1]+"</td></tr>").join("");
}

const collapsedMonths=new Set();
function renderList(c,v){
  const cutAt={};
  cuts(c,v).forEach(t=>cutAt[t.i]=t.jump);
  let h="", acc=0;
  for(let m=0;m<12;m++){
    const closed=collapsedMonths.has(m)?" closed":"";
    let rSum=0,sSum=0;
    for(let d=0;d<MLEN[m];d++){rSum+=ev(c,acc+d,v,1);sSum+=ev(c,acc+d,v,2);}
    h+='<div class="mrow'+closed+'" data-m="'+m+'"><span class="mchev">'+
       (closed?"&#9656;":"&#9662;")+'</span><span>'+MONTHS[m]+" "+DATA.year+'</span>'+
       '<span class="mavg">avg '+fmt(rSum/MLEN[m])+" - "+fmt(sSum/MLEN[m])+'</span></div>';
    h+='<div class="mbody'+closed+'" data-mb="'+m+'">';
    for(let d=0;d<MLEN[m];d++){
      const i=acc+d;
      if(cutAt[i]!==undefined){
        h+='<div class="cutrow">clocks '+(cutAt[i]>0?"go forward":"go back")+" "+
           Math.abs(cutAt[i])+" h on "+shortDate(i)+"</div>";
      }
      if(c.us&&v==="spaA"&&i===DATA.spaCutIdx){
        h+='<div class="cutrow grey">1 Nov fall-back cancelled under the SPA scenario</div>';
      }
      const dawn=ev(c,i,v,0), rise=ev(c,i,v,1), set=ev(c,i,v,2), dusk=ev(c,i,v,3);
      const L=x=>(100*x/1440).toFixed(2);
      h+='<div class="drow" data-i="'+i+'"><span class="d">'+mmdd(i)+'</span>'+
         '<span class="t">'+fmt(rise)+'</span>'+
         '<span class="track">'+
           '<span class="tick" style="left:25%"></span><span class="tick" style="left:50%"></span><span class="tick" style="left:75%"></span>'+
           '<span class="tw" style="left:'+L(dawn)+'%;width:'+L(dusk-dawn)+'%"></span>'+
           '<span class="day" style="left:'+L(rise)+'%;width:'+L(set-rise)+'%"></span>'+
         '</span>'+
         '<span class="t">'+fmt(set)+'</span></div>';
    }
    h+='</div>';
    acc+=MLEN[m];
  }
  const list=document.getElementById("list");
  list.innerHTML=h;
  list.querySelectorAll(".drow").forEach(el=>{
    el.onclick=()=>{state.day=+el.dataset.i; refresh();};
  });
  list.querySelectorAll(".mrow").forEach(el=>{
    el.onclick=()=>{
      const m=+el.dataset.m;
      const body=list.querySelector('.mbody[data-mb="'+m+'"]');
      const chev=el.querySelector(".mchev");
      const closing=!collapsedMonths.has(m);
      if(closing)collapsedMonths.add(m); else collapsedMonths.delete(m);
      el.classList.toggle("closed",closing);
      if(body)body.classList.toggle("closed",closing);
      if(chev)chev.textContent=closing?"▸":"▾";
    };
  });
  markSel();
}

function markSel(){
  // highlight only; never scroll the page. Changing the date must not move
  // the viewport (operator request, 22 Jul): the stats card and chart update
  // in place, and the list highlight is there when you scroll to it.
  document.querySelectorAll(".drow.sel").forEach(e=>e.classList.remove("sel"));
  const el=document.querySelector('.drow[data-i="'+state.day+'"]');
  if(el)el.classList.add("sel");
}

function renderAll(){
  const c=DATA.cities[state.city], v=state.variant;
  document.querySelectorAll(".seg button").forEach(b=>
    b.classList.toggle("on",b.dataset.v===v));
  document.getElementById("vsub").textContent=VARIANTS.find(x=>x.id===v).sub;
  const ns=c.lat>=0?"N":"S", ewv=c.lon>0?"E":"W";
  const DG='<span class="dg">&#176;</span>';   // cmr10 maps U+00B0 to the wrong
  // glyph, in the browser exactly as in matplotlib; force Georgia for it
  document.getElementById("listhead").innerHTML=
    c.name+" ("+state.city+") &#183; "+Math.abs(c.lat).toFixed(2)+DG+" "+ns+", "+
    Math.abs(c.lon).toFixed(2)+DG+" "+ewv+" &#183; "+c.role+
    (c.airport?" &#183; "+c.airport:"")+" &#183; "+c.tz;
  document.getElementById("scenNote").style.display=
    (!c.us&&(v==="spaA"||v==="spaS"))?"block":"none";
  let iLate=0,iEarly=0,iLong=0;
  for(let i=1;i<N;i++){
    if(ev(c,i,v,2)>ev(c,iLate,v,2))iLate=i;
    if(ev(c,i,v,2)<ev(c,iEarly,v,2))iEarly=i;
    if(c.days[i][2]-c.days[i][1]>c.days[iLong][2]-c.days[iLong][1])iLong=i;
  }
  document.getElementById("extremes").textContent=
    "latest sunset "+fmt(ev(c,iLate,v,2))+", "+shortDate(iLate)+
    " · earliest sunset "+fmt(ev(c,iEarly,v,2))+", "+shortDate(iEarly)+
    " · longest day "+fmtDur(c.days[iLong][2]-c.days[iLong][1])+", "+shortDate(iLong);
  renderDay();
  renderChart(c,v);
  renderMap();
  renderList(c,v);
  renderAmp();
}

document.getElementById("prevD").onclick=()=>{state.day=Math.max(0,state.day-1);
  refresh();};
document.getElementById("nextD").onclick=()=>{state.day=Math.min(N-1,state.day+1);
  refresh();};
document.getElementById("todayD").onclick=()=>{const t=new Date();
  let i=Math.round((Date.UTC(t.getFullYear(),t.getMonth(),t.getDate())-Date.UTC(DATA.year,0,1))/86400000);
  state.day=Math.max(0,Math.min(N-1,i));
  refresh();};
document.getElementById("playD").onclick=()=>setPlay(!playTimer);
document.querySelectorAll("#speed button").forEach(b=>{
  b.onclick=()=>{
    state.speed=+b.dataset.s;
    document.querySelectorAll("#speed button").forEach(x=>
      x.classList.toggle("on",x===b));
    if(playTimer)setPlay(true);          // re-arm at the new rate
  };
});

document.getElementById("foot").innerHTML=
  "NOAA solar position engine (package claude-opus-4.8_solar-sunset-2026), "+
  "city-centre coordinates, zenith 90.833<span class=\"dg\">&#176;</span> for rise "+
  "and set, 96<span class=\"dg\">&#176;</span> for civil twilight; "+
  "accuracy about ±1 minute. Times are 24-hour local. "+
  "SPA columns assume the Sunshine Protection Act (House 308-117, 14 Jul @@YEAR@@) "+
  "is enacted before 1 Nov @@YEAR@@ with no state opt-outs; the Senate had not voted "+
  "when this was built. Spherical Earth, sea-level horizon; real terrain moves observed "+
  "times by minutes.";

renderControls();
renderAll();
latState.phi=DATA.cities[state.city].lat;   // start the explorer at the
initLat();                                  // currently selected city
</script>
</body>
</html>
"""


def main():
    with open(os.path.join(HERE, "map_assets.json")) as f:
        assets = json.load(f)
    html = (TEMPLATE
            .replace("@@YEAR@@", str(YEAR))
            .replace("@@NLOC@@", str(len(ORDER)))
            .replace("@@CMR@@", font_b64("cmr10.ttf"))
            .replace("@@CMB@@", font_b64("cmb10.ttf"))
            .replace("@@CMS@@", font_b64("cmss10.ttf"))
            .replace("@@LAND@@", assets["land"])
            .replace("@@LIGHTS@@", json.dumps(assets["lights"], separators=(",", ":")))
            .replace("@@DATA@@", json.dumps(build_data(), separators=(",", ":"))))
    path = f"{OUT}/almanac_{YEAR}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {path} ({os.path.getsize(path)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
