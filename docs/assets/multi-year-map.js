/* Shared cross-edition route viewer. Geometry is evidence-labelled per edition;
 * playback interpolates only between the selected result's real timing anchors. */
(function(global){
'use strict';
const colors=['#1967bc','#d34787','#138a73','#d09325','#854bb0'];
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const finite=x=>Number.isFinite(Number(x))&&x!==null&&x!=='';
const fmt=t=>{let n=Math.max(0,Math.round(Number(t)||0));return Math.floor(n/3600)+':'+String(Math.floor(n/60)%60).padStart(2,'0')+':'+String(n%60).padStart(2,'0')};
const merc=(lat,lon)=>[(Number(lon)+180)/360*256,(1-Math.asinh(Math.tan(Number(lat)*Math.PI/180))/Math.PI)/2*256];
const interp=(points,km)=>{
 if(!points.length)return null;
 if(km<=points[0][2])return points[0];
 if(km>=points.at(-1)[2])return points.at(-1);
 let lo=1,hi=points.length-1;
 while(lo<hi){let m=(lo+hi)>>1;if(points[m][2]<km)lo=m+1;else hi=m}
 const a=points[lo-1],b=points[lo],f=(km-a[2])/Math.max(1e-9,b[2]-a[2]);
 return [a[0]+f*(b[0]-a[0]),a[1]+f*(b[1]-a[1]),km];
};
const atTime=(anchors,t)=>{
 if(!anchors.length)return null;
 if(t<=anchors[0].time)return anchors[0].distance;
 for(let i=1;i<anchors.length;i++)if(t<=anchors[i].time){
  const a=anchors[i-1],b=anchors[i],f=(t-a.time)/Math.max(.0001,b.time-a.time);
  return a.distance+f*(b.distance-a.distance);
 }
 return anchors.at(-1).distance; // freeze after last genuine observation
};
function mount(root,rawItems){
 if(!root)return{destroy(){}};
 const items=rawItems.map((raw,i)=>{
  const points=(raw.points||[]).filter(p=>p.length>=3&&p.every(finite)).map(p=>p.map(Number)).sort((a,b)=>a[2]-b[2]);
  let previousTime=-1,previousDistance=-1;
  const anchors=(raw.anchors||[]).filter(a=>finite(a.time)&&finite(a.distance)&&Number(a.time)>previousTime&&Number(a.distance)>=previousDistance&&(previousTime=Number(a.time))>=0&&(previousDistance=Number(a.distance))>=0).map(a=>({time:Number(a.time),distance:Number(a.distance)}));
  return {...raw,points,anchors,index:i,color:colors[i%colors.length],visible:true};
 });
 const mapped=items.filter(item=>item.points.length>=2);
 if(!mapped.length){
  root.innerHTML='<div class="multi-year-warning"><strong>Ingen rutt att rita för dessa upplagor.</strong><p>Resultatjämförelsen fungerar ändå. Kartan får inte låna en annan upplagas GPX.</p></div>';
  return{destroy(){}};
 }
 const W=900,H=470,all=mapped.flatMap(item=>item.points),baseCoords=all.map(p=>merc(p[0],p[1]));
 const xs=baseCoords.map(p=>p[0]),ys=baseCoords.map(p=>p[1]),left=Math.min(...xs),right=Math.max(...xs),top=Math.min(...ys),bottom=Math.max(...ys);
 const baseZoom=Math.max(7,Math.min(15,Math.floor(Math.log2(Math.min((W-100)/Math.max(.001,right-left),(H-90)/Math.max(.001,bottom-top))))));
 let zoom=baseZoom,clock=0,playing=false,raf=0,started=0,initialClock=0,visible=true,terminated=false,seconds=120;
 const maxClock=Math.max(0,...items.map(i=>i.anchors.at(-1)?.time||0));
 const title='<div class="multi-year-map-head"><div><p class="eyebrow">KARTJÄMFÖRELSE MELLAN ÅR</p><h3>Banvarianter och beräknad position</h3><p>Varje färg visar den valda upplagans egen dokumenterade rutt. Färgade markörer interpoleras endast mellan observerade tidspassager; efter sista observationen stannar de.</p></div></div>';
 const legends=items.map(item=>'<label class="multi-year-route-option"><input type="checkbox" data-route-visible="'+item.index+'" '+(item.points.length>=2?'checked':'disabled')+'><i style="background:'+item.color+'"></i><span><strong>'+esc(item.year+' · '+item.name)+'</strong><small>'+esc(item.provenance||'Rutt saknas')+(item.points.length>=2?' · '+item.points.at(-1)[2].toFixed(1).replace('.',',')+' km':'')+'</small></span></label>').join('');
 root.innerHTML=title+'<div class="multi-year-route-legend">'+legends+'</div><div class="multi-year-map-surface"><svg id="multi-year-route-svg" viewBox="0 0 900 470" role="img" aria-label="Jämförelsekarta med separata bansträckningar"></svg><div class="multi-year-map-zoom"><button type="button" data-map-zoom="1" aria-label="Zooma in på banorna">+</button><button type="button" data-map-zoom="-1" aria-label="Zooma ut">−</button><button type="button" data-map-fit>Hela banorna</button></div></div><p class="multi-year-map-credit">Kartunderlag © OpenStreetMap contributors. GPX-geometri är banreferens, inte löparens uppmätta GPS-position.</p><div class="multi-year-map-controls"><button type="button" data-map-play '+(maxClock===0?'disabled':'')+'>Spela</button><button type="button" data-map-reset>Starta om</button><label>Uppspelningstid <select data-map-duration><option value="30">30 sek</option><option value="60">60 sek</option><option value="120" selected>120 sek</option><option value="180">180 sek</option></select></label><span data-map-time>'+fmt(0)+'</span></div><input class="multi-year-map-range" data-map-range type="range" min="0" max="'+Math.ceil(maxClock)+'" value="0" step="1" aria-label="Gemensam tävlingsklocka"><p class="multi-year-map-note" role="status" data-map-note>Gemensam tid räknas från respektive upplagas start. Den fysiska banan kan vara annorlunda. Ingen gemensam placering mellan år beräknas.</p>';
 const svg=root.querySelector('#multi-year-route-svg'),range=root.querySelector('[data-map-range]'),play=root.querySelector('[data-map-play]');
 const readout=root.querySelector('[data-map-time]');
 let projection=null;
 function tileImage(z,x,y,px,py){const n=2**z;if(x<0||y<0||x>=n||y>=n)return'';return '<image href="https://tile.openstreetmap.org/'+z+'/'+x+'/'+y+'.png" x="'+px.toFixed(1)+'" y="'+py.toFixed(1)+'" width="256.2" height="256.2"/>'}
 function drawMap(){
  const coords=mapped.filter(i=>i.visible).flatMap(i=>i.points.map(p=>merc(p[0],p[1]))),boundCoords=coords.length?coords:baseCoords;
  const minX=Math.min(...boundCoords.map(x=>x[0])),maxX=Math.max(...boundCoords.map(x=>x[0])),minY=Math.min(...boundCoords.map(x=>x[1])),maxY=Math.max(...boundCoords.map(x=>x[1]));
  const scale=2**zoom,cx=(minX+maxX)/2*scale,cy=(minY+maxY)/2*scale;
  const point=p=>{const xy=merc(p[0],p[1]);return [W/2+(xy[0]*scale-cx),H/2+(xy[1]*scale-cy)]};
  projection=point;
  const firstX=Math.floor((cx-W/2)/256),lastX=Math.floor((cx+W/2)/256),firstY=Math.floor((cy-H/2)/256),lastY=Math.floor((cy+H/2)/256);
  const tiles=[];for(let x=firstX;x<=lastX;x++)for(let y=firstY;y<=lastY;y++)tiles.push(tileImage(zoom,x,y,W/2+x*256-cx,H/2+y*256-cy));
  const paths=mapped.filter(i=>i.visible).map(item=>{
   const line=item.points.map((p,j)=>{const xy=point(p);return(j?'L':'M')+xy[0].toFixed(1)+' '+xy[1].toFixed(1)}).join(' ');
   return '<path d="'+line+'" fill="none" stroke="#fff" stroke-width="7" stroke-linejoin="round" opacity=".85"/><path d="'+line+'" fill="none" stroke="'+item.color+'" stroke-width="3.8" stroke-linejoin="round" stroke-linecap="round"/>';
  }).join('');
  const markers=mapped.filter(i=>i.visible&&i.anchors.length>=2).map(i=>'<g data-map-marker="'+i.index+'"><circle r="9" fill="#fff" stroke="'+i.color+'" stroke-width="3"/><circle r="4" fill="'+i.color+'"/></g>').join('');
  svg.innerHTML='<rect width="'+W+'" height="'+H+'" fill="#edf1ec"/>'+tiles.join('')+paths+markers;
  updateClock(clock);
 }
 function updateClock(value){
  clock=Math.min(maxClock,Math.max(0,Number(value)||0));range.value=String(clock);readout.textContent=fmt(clock);
  for(const item of mapped){
   const marker=svg.querySelector('[data-map-marker="'+item.index+'"]');if(!marker||!projection)continue;
   const d=atTime(item.anchors,clock),pos=d===null?null:interp(item.points,d);
   if(!pos){marker.setAttribute('visibility','hidden');continue}
   const xy=projection(pos);marker.setAttribute('transform','translate('+xy[0].toFixed(1)+' '+xy[1].toFixed(1)+')');marker.removeAttribute('visibility');
  }
 }
 function stop(){playing=false;cancelAnimationFrame(raf);if(play)play.textContent='Spela'}
 function frame(now){if(!playing||terminated)return;const elapsed=(now-started)/1000,goal=initialClock+elapsed/seconds*maxClock;updateClock(goal);if(goal>=maxClock)stop();else raf=requestAnimationFrame(frame)}
 play?.addEventListener('click',()=>{if(playing){stop();return}if(clock>=maxClock)updateClock(0);started=performance.now();initialClock=clock;playing=true;play.textContent='Pausa';raf=requestAnimationFrame(frame)});
 root.querySelector('[data-map-reset]')?.addEventListener('click',()=>{stop();updateClock(0)});
 root.querySelector('[data-map-duration]')?.addEventListener('change',e=>{seconds=Number(e.target.value)||120;if(playing){started=performance.now();initialClock=clock}});
 range?.addEventListener('input',()=>{stop();updateClock(range.value)});
 root.querySelectorAll('[data-map-zoom]').forEach(b=>b.addEventListener('click',()=>{zoom=Math.max(7,Math.min(17,zoom+Number(b.dataset.mapZoom)));drawMap()}));
 root.querySelector('[data-map-fit]')?.addEventListener('click',()=>{zoom=baseZoom;drawMap()});
 root.querySelectorAll('[data-route-visible]').forEach(b=>b.addEventListener('change',()=>{items[Number(b.dataset.routeVisible)].visible=b.checked;drawMap()}));
 drawMap();
 return{destroy(){terminated=true;stop();projection=null}};
}
global.LoppMultiYearRouteMap={mount};
})(globalThis);
