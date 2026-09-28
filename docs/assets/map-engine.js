import {esc,elevation,time,empty} from './charts.js';
import {distanceAtTime,finite} from './analytics.js';
import {methodText} from './views.js';
let leafletPromise;
function leaflet(){
 if(globalThis.L)return Promise.resolve(globalThis.L);
 if(!leafletPromise)leafletPromise=new Promise(resolve=>{
 const css=document.createElement('link');css.rel='stylesheet';css.href='vendor/leaflet-1.9.4/leaflet.css';document.head.append(css);
 const script=document.createElement('script');script.src='vendor/leaflet-1.9.4/leaflet.js';script.onload=()=>resolve(globalThis.L);script.onerror=()=>resolve(null);document.head.append(script);
 });return leafletPromise;
}
export function pointAtDistance(points,d){
 if(!points.length||!finite(d))return null;let lo=0,hi=points.length-1;
 while(lo<hi){const mid=(lo+hi)>>1;if(points[mid][3]<d)lo=mid+1;else hi=mid;}
 const p=points[Math.max(0,lo-1)],q=points[lo],f=q[3]>p[3]?Math.max(0,Math.min(1,(d-p[3])/(q[3]-p[3]))):0;
 return [p[0]+(q[0]-p[0])*f,p[1]+(q[1]-p[1])*f];
}
export function terrainMetrics(profile,range=null){
 const from=range&&finite(range[0])?Math.min(range[0],range[1]):-Infinity,to=range&&finite(range[1])?Math.max(range[0],range[1]):Infinity;
 const window=(profile||[]).filter(p=>finite(p[0])&&p[0]>=from&&p[0]<=to),pts=window.filter(p=>finite(p[1])).map(p=>[Number(p[0]),Number(p[1])]),coverage=window.length?pts.length/window.length:0;
 // Do not bridge large gaps in partial GPX elevation. Descriptive D+/D− is shown
 // only for a near-complete profile; incomplete sources remain explicitly unavailable.
 if(pts.length<2||coverage<.9)return null;
 let ascent=0,descent=0;for(let i=1;i<pts.length;i++){const d=pts[i][1]-pts[i-1][1];if(d>0)ascent+=d;else descent-=d;}
 return {ascent,descent,min:Math.min(...pts.map(p=>p[1])),max:Math.max(...pts.map(p=>p[1])),distance:pts.at(-1)[0]-pts[0][0],coverage};
}
export async function mountMap(root,{route,adapter,records=[],segment=0,reduced=matchMedia('(prefers-reduced-motion: reduce)').matches}){
 let destroyed=false,map=null,timer=null,markers=[],high=null,t=0;const models=records.map(r=>({r,anchors:adapter.anchors(r,route)})).filter(m=>m.anchors.length>=2),duration=Math.max(1,...models.flatMap(m=>m.anchors.map(a=>a.time)));
 root.innerHTML='<p><span class="badge">'+esc(route.provenance_label)+'</span> · '+route.full_distance_km.toFixed(2)+' km mätt GPX</p><div class="map"></div><p class="map-status">Neutral banvy · aktuell upplagas rutt</p><div class="map-legend">'+records.map((r,i)=>'<span>'+(i+1)+'. '+esc(r.name)+'</span>').join('')+'</div><div class="map-control">'+(models.length?'<button data-play '+(reduced?'disabled':'')+'>Spela</button><button data-reset>Från start</button><label class="sr-only" for="replay-'+root.id+'">Replaytid</label><input id="replay-'+root.id+'" data-seek type="range" min="0" max="'+duration+'" value="0" step="1"><output class="replay-clock">0:00:00</output>':'')+'<button data-tiles>Visa kartbakgrund</button></div>'+(reduced?'<p class="muted">Reducerad rörelse: använd tidsreglaget för stillbilder.</p>':'')+(records.length&&!models.length?empty('För få geografiskt förankrade observationer för denna replay. Saknade passager fylls inte.'): '')+(records.length?'':'<div class="route-metrics"></div>')+'<div class="map-elevation"></div><details><summary>Kartans och replayns underlag</summary><p>'+esc(methodText.replay)+'</p><p>Ruttkälla: '+esc(route.source)+'. Höjd: '+esc(route.elevation_method)+'.</p></details>';
 const box=root.querySelector('.map'),status=root.querySelector('.map-status'),colors=['#1677a8','#b51d60','#497b35','#92691a','#7651a0'];
 const b=adapter.boundary;function selectedRange(index){return [route.anchors[b[index]?.key],route.anchors[b[index+1]?.key]];}
 function drawElevation(index){root.querySelector('.map-elevation').innerHTML=elevation(route.elevation,route.anchors,selectedRange(index));}
 function drawTerrain(index){const el=root.querySelector('.route-metrics');if(!el)return;const total=terrainMetrics(route.elevation),hasSegment=adapter.race.capabilities.segment_analysis&&b.length>1,selected=hasSegment?terrainMetrics(route.elevation,selectedRange(index)):null;if(!total){el.innerHTML=empty('GPX-filen saknar en tillräckligt komplett höjdprofil för tillförlitliga terrängmått. D+/D− visas därför inte.');return;}el.innerHTML='<div><span>Hela rutten · D+</span><strong>'+Math.round(total.ascent)+' m</strong></div><div><span>Hela rutten · D−</span><strong>'+Math.round(total.descent)+' m</strong></div>'+(hasSegment?'<div><span>Vald delsträcka · D+</span><strong>'+(selected?Math.round(selected.ascent)+' m':'–')+'</strong></div><div><span>Vald delsträcka · D−</span><strong>'+(selected?Math.round(selected.descent)+' m':'–')+'</strong></div>':'')+'<p>Beskrivande mått från den utjämnade GPX-höjdprofilen; inte officiell D+/D−.</p>';}
 drawElevation(segment);drawTerrain(segment);
 function fallback(){
  const lats=route.points.map(p=>p[0]),lons=route.points.map(p=>p[1]),minLat=Math.min(...lats),maxLat=Math.max(...lats),minLon=Math.min(...lons),maxLon=Math.max(...lons);
  const cos=Math.cos((minLat+maxLat)/2*Math.PI/180),scale=Math.min(560/((maxLon-minLon)*cos||1),320/(maxLat-minLat||1));
  const project=p=>[320+(p[1]-(minLon+maxLon)/2)*cos*scale,190-(p[0]-(minLat+maxLat)/2)*scale];
  const line=route.points.map((p,i)=>(i?'L':'M')+project(p).join(',')).join(' ');
  box.innerHTML='<svg class="route-fallback" viewBox="0 0 640 380" role="img" aria-label="Aktuell rutt utan kartbakgrund"><path d="'+line+'" fill="none" stroke="'+colors[0]+'" stroke-width="4"/><g class="runners"></g></svg>';
  return models.map((m,i)=>({update(d){const p=pointAtDistance(route.points,d);if(!p)return;let node=box.querySelector('[data-runner="'+i+'"]');if(!node){node=document.createElementNS('http://www.w3.org/2000/svg','g');node.dataset.runner=i;node.innerHTML='<circle r="9" fill="'+colors[i]+'"/><text x="12" y="-10" font-size="13">'+esc(m.r.name)+'</text>';box.querySelector('.runners').append(node);}node.setAttribute('transform','translate('+project(p).join(' ')+')');}}));
 }
 const L=await leaflet();if(destroyed||!root.isConnected)return {destroy(){}};
 if(L){
  map=L.map(box,{zoomControl:true,attributionControl:true,scrollWheelZoom:false,zoomAnimation:!reduced,fadeAnimation:!reduced});
  const line=L.polyline(route.points.map(p=>[p[0],p[1]]),{color:colors[0],weight:4}).addTo(map);map.fitBounds(line.getBounds(),{padding:[30,30]});
  Object.entries(route.anchors).forEach(([key,d])=>{const p=pointAtDistance(route.points,d);if(!p)return;const cp=adapter.checkpoints.find(c=>c.key===key);L.circleMarker(p,{radius:5,color:colors[0],fillOpacity:1}).bindTooltip(esc(cp?.name||key),{direction:'top'}).addTo(map);});
  markers=models.map((m,i)=>{const dot=L.circleMarker(pointAtDistance(route.points,m.anchors[0].distance),{radius:9,color:colors[i],fillColor:colors[i],fillOpacity:1}).bindTooltip((i+1)+'. '+esc(m.r.name),{permanent:true,direction:'right',className:'runner-label'}).addTo(map);return {update:d=>{const p=pointAtDistance(route.points,d);if(p)dot.setLatLng(p);}};});
 }else markers=fallback();
 function highlight(index){drawElevation(index);drawTerrain(index);if(!map)return;if(high)high.remove();const [from,to]=selectedRange(index);if(!finite(from)||!finite(to))return;const points=[pointAtDistance(route.points,from),...route.points.filter(p=>p[3]>from&&p[3]<to).map(p=>[p[0],p[1]]),pointAtDistance(route.points,to)];high=L.polyline(points,{color:colors[2],weight:7,opacity:.75}).addTo(map);}
 highlight(segment);
 root.querySelector('[data-tiles]').onclick=event=>{
  if(!map){status.textContent='Neutral banvy används. Kartbiblioteket kunde inte laddas.';return;}
  event.target.disabled=true;status.textContent='Laddar kartbakgrund…';
  const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap contributors'});
  let failed=false;
  tiles.on('tileerror',()=>{if(failed)return;failed=true;box.classList.add('route-only');tiles.remove();status.textContent='Kartbakgrunden kunde inte läsas. Neutral banvy behåller rutt, kontroller och deltagare.';});
  tiles.on('load',()=>{if(!failed)status.textContent='OpenStreetMap · aktuell upplagas rutt';});tiles.addTo(map);
 };
 function stop(){if(timer)cancelAnimationFrame(timer);timer=null;const p=root.querySelector('[data-play]');if(p)p.textContent='Spela';}
 function seek(value){t=Math.max(0,Math.min(duration,value));models.forEach((m,i)=>markers[i].update(distanceAtTime(m.anchors,t)));const range=root.querySelector('[data-seek]');if(range)range.value=t;const clock=root.querySelector('output');if(clock)clock.textContent=time(t);}
 if(models.length){
  root.querySelector('[data-seek]').oninput=e=>{stop();seek(+e.target.value);};
  root.querySelector('[data-reset]').onclick=()=>{stop();seek(0);};
  root.querySelector('[data-play]').onclick=()=>{if(timer){stop();return;}if(reduced)return;if(t>=duration)seek(0);let last=performance.now();root.querySelector('[data-play]').textContent='Pausa';function tick(now){if(destroyed)return;seek(t+(now-last)/120000*duration);last=now;if(t<duration)timer=requestAnimationFrame(tick);else stop();}timer=requestAnimationFrame(tick);};
  seek(0);
 }
 return {destroy(){destroyed=true;stop();map?.remove();},select:highlight,seek};
}

