/* Cross-edition route viewer. Each course keeps its own sourced geometry.
 * Motion is illustrative, interpolated only between each result's observed anchors.
 * Camera/audio follow the frozen Comparison 2.0 replay defaults. */
(function(global){
'use strict';
const colors=['#1967bc','#d34787','#138a73','#d09325','#854bb0'];
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const finite=value=>value!==null&&value!==''&&value!==undefined&&Number.isFinite(Number(value));
const clamp=(value,lo,hi)=>Math.max(lo,Math.min(hi,value));
const fmt=value=>{const n=Math.max(0,Math.round(Number(value)||0));return Math.floor(n/3600)+':'+String(Math.floor(n/60)%60).padStart(2,'0')+':'+String(n%60).padStart(2,'0')};
const merc=(lat,lon)=>[(Number(lon)+180)/360*256,(1-Math.asinh(Math.tan(Number(lat)*Math.PI/180))/Math.PI)/2*256];
const interp=(points,km)=>{
 if(!points.length)return null;
 if(km<=points[0][2])return points[0];
 if(km>=points.at(-1)[2])return points.at(-1);
 let lo=1,hi=points.length-1;
 while(lo<hi){const mid=(lo+hi)>>1;if(points[mid][2]<km)lo=mid+1;else hi=mid;}
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
 return anchors.at(-1).distance; // after DNF, freeze at the last observed passage
};
function mount(root,rawItems,options={}){
 if(!root)return{destroy(){}};
 const W=900,H=470;
 const items=rawItems.map((raw,i)=>{
  const points=(raw.points||[]).filter(p=>p.length>=3&&p.every(finite)).map(p=>p.map(Number)).sort((a,b)=>a[2]-b[2]);
  const anchors=[];let previousTime=-1,previousDistance=-1;
  for(const source of raw.anchors||[]){
   const t=Number(source.time),d=Number(source.distance);
   if(!finite(source.time)||!finite(source.distance)||t<=previousTime||d<previousDistance)continue;
   previousTime=t;previousDistance=d;anchors.push({time:t,distance:d});
  }
  return {...raw,points,anchors,index:i,color:colors[i%colors.length],visible:points.length>=2};
 });
 const mapped=items.filter(item=>item.points.length>=2);
 if(!mapped.length){
  root.innerHTML='<div class="multi-year-warning"><strong>Ingen rutt att rita för dessa upplagor.</strong><p>Resultatjämförelsen fungerar ändå. Kartan får inte låna en annan upplagas GPX.</p></div>';
  return{destroy(){}};
 }
 const reduced=Boolean(global.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches);
 const maxClock=Math.max(0,...items.map(item=>item.anchors.at(-1)?.time||0));
 const all=mapped.flatMap(item=>item.points);
 const allGeo=all.map(p=>merc(p[0],p[1]));
 const bounds=geo=>{
  let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
  for(const [x,y] of geo){if(x<minX)minX=x;if(x>maxX)maxX=x;if(y<minY)minY=y;if(y>maxY)maxY=y;}
  return{minX,maxX,minY,maxY};
 };
 const fitGeo=(geo,padding=125)=>{
  if(!geo.length)return 10;
  const b=bounds(geo),dx=Math.max(.00001,b.maxX-b.minX),dy=Math.max(.00001,b.maxY-b.minY);
  return clamp(Math.log2(Math.min((W-padding*2)/dx,(H-padding*2)/dy)),7,16);
 };
 const routeGeo=()=>mapped.filter(item=>item.visible).flatMap(item=>item.geoPoints);
 const centerGeo=geo=>{
  const b=bounds(geo);return[(b.minX+b.maxX)/2,(b.minY+b.maxY)/2];
 };
 for(const item of mapped)item.geoPoints=item.points.map(p=>merc(p[0],p[1]));
 const fullRoute=()=>{const geo=routeGeo();return geo.length?geo:allGeo;};
 let currentRouteGeo=fullRoute(),fullZoom=fitGeo(currentRouteGeo,92),fullCenter=centerGeo(currentRouteGeo);
 let cameraMode='both',manualZoomDelta=0,clock=0,playing=false,raf=0,started=0,initialClock=0,seconds=120,terminated=false,activated=false;
 let renderZoom=Math.round(fullZoom),cameraZoom=fullZoom,cameraGeo=[...fullCenter];
 let origin=[0,0],scene=null,tileLayer=null,markerLayer=null,markerNodes=[],tileKey='';
 const tileCache=new Map();let neededTiles=new Set();
 const title='<div class="multi-year-map-head"><div><p class="eyebrow">KARTJÄMFÖRELSE MELLAN ÅR</p><h3>Banvarianter och beräknad position</h3><p>Olika färger visar varje upplagas egen dokumenterade rutt. Markörernas lägen beräknas mellan verkliga tidspassager, inte från deltagarens GPS.</p></div></div>';
 const legend=items.map(item=>'<label class="multi-year-route-option"><input type="checkbox" data-route-visible="'+item.index+'" '+(item.points.length>=2?'checked':'disabled')+'><i style="background:'+item.color+'"></i><span><strong>'+esc(item.year+' · '+item.name)+'</strong><small>'+esc(item.provenance||'Rutt saknas')+(item.points.length>=2?' · '+item.points.at(-1)[2].toFixed(1).replace('.',',')+' km':'')+'</small></span></label>').join('');
 const musicControls=options.musicSrc?'<button type="button" data-map-music aria-pressed="true" aria-label="Slå av eller på musik">♫ Musik</button><label>Volym <input data-map-volume type="range" min="0" max="1" step=".05" value=".3" aria-label="Musikvolym"></label><span data-map-audio-note role="status" class="muted small" hidden></span>':'';
 root.innerHTML=title+'<div class="multi-year-route-legend">'+legend+'</div><div class="multi-year-map-surface"><svg id="multi-year-route-svg" viewBox="0 0 900 470" role="img" aria-label="Jämförelsekarta med separata bansträckningar"></svg><div class="multi-year-map-zoom"><button type="button" data-map-zoom="1" aria-label="Zooma in på banorna">+</button><button type="button" data-map-zoom="-1" aria-label="Zooma ut">−</button><button type="button" data-map-fit>Visa hela banorna</button></div></div><p class="multi-year-map-credit">Kartunderlag © OpenStreetMap contributors. GPX-geometri är banreferens, inte löparens uppmätta GPS-position.</p><div class="multi-year-map-controls"><button type="button" data-map-play '+(maxClock===0?'disabled':'')+'>Spela</button><button type="button" data-map-reset>Starta om</button><label>Uppspelningstid <select data-map-duration><option value="30">30 sek</option><option value="60">60 sek</option><option value="120" selected>120 sek</option><option value="180">180 sek</option></select></label><label>Kamera <select data-map-camera aria-label="Kameraläge"><option value="full">Hela banorna</option><option value="both" selected>'+(items.length<=2?'Följ båda':'Följ alla')+'</option><option value="leader">Följ längst kommen</option></select></label>'+musicControls+'<span data-map-time>'+fmt(0)+'</span></div><input class="multi-year-map-range" data-map-range type="range" min="0" max="'+Math.ceil(maxClock)+'" value="0" step="1" aria-label="Gemensam tävlingsklocka"><p class="multi-year-map-note" role="status" data-map-note>Följ längst kommen utgår från beräknad andel av den egna banan, inte från officiell placering mellan olika år. Musik startar bara vid ett aktivt klick på Spela.</p>';
 const svg=root.querySelector('#multi-year-route-svg'),range=root.querySelector('[data-map-range]'),play=root.querySelector('[data-map-play]'),readout=root.querySelector('[data-map-time]');
 let audio=null,enabled=true,volume=.3,lastAudible=.3;
 const prefix=options.storagePrefix||'lopp-multi-year-music';
 try{enabled=global.localStorage?.getItem(prefix+'-enabled')!=='false';const saved=global.localStorage?.getItem(prefix+'-volume');if(saved!==null&&finite(saved))volume=clamp(Number(saved),0,1);}catch{}
 if(volume>0)lastAudible=volume;
 const musicButton=root.querySelector('[data-map-music]'),volumeSlider=root.querySelector('[data-map-volume]'),audioNote=root.querySelector('[data-map-audio-note]');
 if(options.musicSrc&&typeof global.Audio==='function'){
  audio=new global.Audio(options.musicSrc);audio.preload='metadata';audio.loop=true;audio.volume=volume;
  audio.addEventListener('error',()=>{if(audioNote){audioNote.hidden=false;audioNote.textContent='Musikfilen kunde inte laddas. Kartuppspelningen fungerar ändå.';}});
 }
 function renderMusic(){
  if(musicButton){musicButton.textContent=enabled?'♫ Musik':'♪ Musik av';musicButton.setAttribute('aria-pressed',String(enabled));}
  if(volumeSlider)volumeSlider.value=String(volume);
 }
 function playMusic(){
  if(!audio||!enabled||terminated)return;
  const result=audio.play();
  if(result&&typeof result.catch==='function')result.catch(()=>{if(!terminated&&audioNote){audioNote.hidden=false;audioNote.textContent='Webbläsaren väntar med musiken. Tryck på Spela igen.';}});
 }
 renderMusic();
 musicButton?.addEventListener('click',()=>{
  enabled=!enabled;
  if(enabled&&volume<=0){volume=lastAudible||.3;if(audio)audio.volume=volume;}
  try{global.localStorage?.setItem(prefix+'-enabled',String(enabled));}catch{}
  renderMusic();if(!enabled)audio?.pause();else if(playing)playMusic();
 });
 volumeSlider?.addEventListener('input',event=>{
  volume=clamp(Number(event.target.value),0,1);if(volume>0)lastAudible=volume;
  if(audio)audio.volume=volume;try{global.localStorage?.setItem(prefix+'-volume',String(volume));}catch{}
 });
 const toWorld=geo=>[geo[0]*2**renderZoom-origin[0],geo[1]*2**renderZoom-origin[1]];
 const selectedMarkers=()=>{
  const seen=[];
  for(const item of mapped){
   if(!item.visible||item.anchors.length<2)continue;
   const d=atTime(item.anchors,clock),pos=d===null?null:interp(item.points,d);
   if(pos)seen.push({item,geo:merc(pos[0],pos[1]),progress:item.points.at(-1)[2]>0?d/item.points.at(-1)[2]:0});
  }
  return seen;
 };
 function desiredCamera(){
  const tracking=selectedMarkers();
  const effectiveMode=activated?cameraMode:'full';
  if(effectiveMode==='full'||!tracking.length)return{center:fullCenter,zoom:clamp(fullZoom+manualZoomDelta,7,17)};
  const focused=effectiveMode==='leader'?[tracking.reduce((best,item)=>item.progress>best.progress?item:best,tracking[0])]:tracking;
  const geo=focused.map(x=>x.geo);
  const fitting=fitGeo(geo,110);
  // Four levels of detail beyond the full course are sufficient to follow participants
  // without obscuring their relative positions when they spread apart.
  const desired=clamp(Math.min(fullZoom+4,fitting)+manualZoomDelta,7,17);
  return{center:centerGeo(geo),zoom:desired};
 }
 // Keep the current map visible while additional pan/zoom tiles load.
 // Reuse loaded images rather than tearing down the SVG on every boundary.
 function trimTiles(){
  if(terminated||[...neededTiles].some(key=>!tileCache.get(key)?.loaded))return;
  for(const [key,entry] of tileCache)if(!neededTiles.has(key)){
   entry.node.remove();tileCache.delete(key);
  }
 }
 function updateTileLayer(force=false){
  if(!tileLayer||terminated)return;
  const z=clamp(Math.round(cameraZoom),7,17);
  const scale=2**(cameraZoom-z),cx=cameraGeo[0]*2**z,cy=cameraGeo[1]*2**z;
  const halfW=W/(2*scale),halfH=H/(2*scale);
  const x0=Math.floor((cx-halfW)/256)-1,x1=Math.floor((cx+halfW)/256)+1;
  const y0=Math.floor((cy-halfH)/256)-1,y1=Math.floor((cy+halfH)/256)+1;
  const key=[z,x0,x1,y0,y1].join('/');
  if(!force&&key===tileKey)return;
  tileKey=key;
  const max=2**z,displaySize=256*2**(renderZoom-z),required=new Set();
  for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++){
   if(x<0||y<0||x>=max||y>=max)continue;
   const id=z+'/'+x+'/'+y;
   required.add(id);
   if(tileCache.has(id))continue;
   const node=document.createElementNS('http://www.w3.org/2000/svg','image');
   node.setAttribute('data-map-tile',id);
   node.setAttribute('x',(x*displaySize-origin[0]).toFixed(5));
   node.setAttribute('y',(y*displaySize-origin[1]).toFixed(5));
   node.setAttribute('width',(displaySize+0.2*2**(renderZoom-z)).toFixed(5));
   node.setAttribute('height',(displaySize+0.2*2**(renderZoom-z)).toFixed(5));
   node.setAttribute('pointer-events','none');
   const entry={node,loaded:false};
   tileCache.set(id,entry);
   node.addEventListener('load',()=>{entry.loaded=true;trimTiles()},{once:true});
   node.addEventListener('error',()=>{entry.failed=true;/* Retain prior imagery if this tile fails. */},{once:true});
   tileLayer.appendChild(node);
   node.setAttribute('href','https://tile.openstreetmap.org/'+id+'.png');
  }
  neededTiles=required;
  trimTiles();
 }
 function updateView(forceTiles=false){
  if(!scene||terminated)return;
  const pos=toWorld(cameraGeo),scale=2**(cameraZoom-renderZoom);
  scene.setAttribute('transform','translate('+(W/2).toFixed(1)+' '+(H/2).toFixed(1)+') scale('+scale.toFixed(6)+') translate('+(-pos[0]).toFixed(2)+' '+(-pos[1]).toFixed(2)+')');
  updateTileLayer(forceTiles);
  updateMarkerScale();
 }
 function updateMarkerScale(){
  const scale=(2**(renderZoom-cameraZoom)).toFixed(6);
  for(const node of markerNodes)if(node&&node.dataset.worldX!==undefined)
   node.setAttribute('transform','translate('+node.dataset.worldX+' '+node.dataset.worldY+') scale('+scale+')');
 }
 function updateMarkers(){
  for(const item of mapped){
   const node=markerNodes[item.index];
   if(!node)continue;
   if(!item.visible||item.anchors.length<2){node.setAttribute('visibility','hidden');continue;}
   const d=atTime(item.anchors,clock),pos=d===null?null:interp(item.points,d);
   if(!pos){node.setAttribute('visibility','hidden');continue;}
   const xy=toWorld(merc(pos[0],pos[1]));
   node.dataset.worldX=xy[0].toFixed(3);node.dataset.worldY=xy[1].toFixed(3);
   node.removeAttribute('visibility');
  }
  updateMarkerScale();
 }
 function renderGeometry(){
  if(terminated)return;
  origin=allGeo[0].map(v=>v*2**renderZoom);
  const paths=mapped.map(item=>{
   const line=item.points.map((p,i)=>{const xy=toWorld(merc(p[0],p[1]));return(i?'L':'M')+xy[0].toFixed(3)+' '+xy[1].toFixed(3)}).join(' ');
   return '<g data-map-path="'+item.index+'"'+(item.visible?'':' style="display:none"')+'><path d="'+line+'" fill="none" stroke="#fff" vector-effect="non-scaling-stroke" stroke-width="7" stroke-linejoin="round" opacity=".85"/><path d="'+line+'" fill="none" stroke="'+item.color+'" vector-effect="non-scaling-stroke" stroke-width="3.8" stroke-linejoin="round" stroke-linecap="round"/></g>';
  }).join('');
  const markers=mapped.map(item=>'<g data-map-marker="'+item.index+'"><circle r="9" fill="#fff" stroke="'+item.color+'" stroke-width="3"/><circle r="4" fill="'+item.color+'"/></g>').join('');
  svg.innerHTML='<rect width="'+W+'" height="'+H+'" fill="#edf1ec"/><g data-map-scene><g data-map-tiles></g><g data-map-paths>'+paths+'</g><g data-map-markers>'+markers+'</g></g>';
  scene=svg.querySelector('[data-map-scene]');tileLayer=svg.querySelector('[data-map-tiles]');markerLayer=svg.querySelector('[data-map-markers]');
  markerNodes=[];mapped.forEach(item=>markerNodes[item.index]=markerLayer.querySelector('[data-map-marker="'+item.index+'"]'));
  tileKey='';updateMarkers();updateView(true);
 }
 function refreshCamera(immediate=false){
  const target=desiredCamera(),alpha=immediate||reduced?1:.15;
  cameraGeo=[cameraGeo[0]+(target.center[0]-cameraGeo[0])*alpha,cameraGeo[1]+(target.center[1]-cameraGeo[1])*alpha];
  cameraZoom+= (target.zoom-cameraZoom)*alpha;
  // Camera zoom transforms the persistent scene; tiles have their own zoom
  // level and load incrementally. No SVG or route/marker reset is necessary.
  updateView();
 }
 function updateClock(value,immediate=false){
  clock=clamp(Number(value)||0,0,maxClock);
  range.value=String(clock);readout.textContent=fmt(clock);
  updateMarkers();refreshCamera(immediate);
 }
 function stop(){
  playing=false;global.cancelAnimationFrame(raf);
  if(play)play.textContent='Spela';
  audio?.pause();
 }
 function frame(now){
  if(!playing||terminated)return;
  const elapsed=(now-started)/1000;
  const goal=initialClock+(elapsed/seconds)*maxClock;
  updateClock(goal,false);
  if(goal>=maxClock){stop();return;}
  raf=global.requestAnimationFrame(frame);
 }
 play?.addEventListener('click',()=>{
  if(playing){stop();return;}
  if(clock>=maxClock)updateClock(0,true);
  activated=true;started=global.performance.now();initialClock=clock;
  playing=true;play.textContent='Pausa';
  playMusic();
  raf=global.requestAnimationFrame(frame);
 });
 root.querySelector('[data-map-reset]')?.addEventListener('click',()=>{stop();activated=false;manualZoomDelta=0;updateClock(0,true);});
 root.querySelector('[data-map-duration]')?.addEventListener('change',event=>{seconds=Number(event.target.value)||120;if(playing){started=global.performance.now();initialClock=clock;}});
 root.querySelector('[data-map-camera]')?.addEventListener('change',event=>{cameraMode=event.target.value;activated=true;manualZoomDelta=0;refreshCamera(true);});
 range?.addEventListener('input',()=>{stop();activated=true;updateClock(range.value,true);});
 root.querySelectorAll('[data-map-zoom]').forEach(button=>button.addEventListener('click',()=>{activated=true;manualZoomDelta=clamp(manualZoomDelta+Number(button.dataset.mapZoom),-4,4);refreshCamera(true);}));
 root.querySelector('[data-map-fit]')?.addEventListener('click',()=>{cameraMode='full';activated=true;manualZoomDelta=0;const select=root.querySelector('[data-map-camera]');if(select)select.value='full';refreshCamera(true);});
 root.querySelectorAll('[data-route-visible]').forEach(input=>input.addEventListener('change',()=>{
  items[Number(input.dataset.routeVisible)].visible=input.checked;
  currentRouteGeo=fullRoute();fullZoom=fitGeo(currentRouteGeo,92);fullCenter=centerGeo(currentRouteGeo);
  const routeNode=svg.querySelector('[data-map-path="'+Number(input.dataset.routeVisible)+'"]');
  if(routeNode)routeNode.style.display=input.checked?'':'none';
  updateMarkers();refreshCamera(true);
 }));
 renderGeometry();
 return{destroy(){
  if(terminated)return;stop();terminated=true;
  if(audio){audio.pause();try{audio.currentTime=0}catch{}audio.removeAttribute('src');audio.load?.();}
  if(svg)svg.innerHTML='';tileCache.clear();neededTiles.clear();
  scene=null;tileLayer=null;markerLayer=null;markerNodes=[];
 },getCamera:()=>cameraMode,getTime:()=>clock};
}
global.LoppMultiYearRouteMap={mount};
})(globalThis);
