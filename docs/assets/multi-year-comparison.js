import {adapt} from './data-adapter.js';
import {finite,finished,comparable} from './analytics.js';
import {esc,time} from './charts.js';

const tokenFor=(raceKey,id)=>String(raceKey)+'::'+String(id);
const splitToken=token=>{const index=String(token||'').indexOf('::');return index<1?null:{raceKey:String(token).slice(0,index),id:String(token).slice(index+2)};};
const resultMatches=(record,query)=>{const q=String(query||'').trim().toLocaleLowerCase('sv');return q&&`${record?.name||''} ${record?.bib||''} ${record?.club||''}`.toLocaleLowerCase('sv').includes(q);};
const pct=value=>finite(value)?Number(value).toFixed(1).replace('.',',')+' %':'–';
const signed=value=>!finite(value)?'–':Number(value)===0?'0:00':(Number(value)>0?'+':'−')+time(Math.abs(Number(value)));

export function wholeCourseComparable(boot,leftRace,rightRace){
  if(!leftRace||!rightRace)return false;
  return comparable(leftRace,rightRace,boot?.courses||{});
}
function fieldPercentile(adapter,record){
  if(!finished(record)||!finite(record.finish_seconds))return null;
  const finishers=adapter.records.filter(row=>finished(row)&&finite(row.finish_seconds));
  if(!finishers.length)return null;
  const slower=finishers.filter(row=>Number(row.finish_seconds)>Number(record.finish_seconds)).length;
  return 100*slower/finishers.length;
}
function checkpointRows(left,right,sameCourse){
  if(!sameCourse)return[];
  const rightBoundaries=new Map(right.adapter.boundary.map((cp,index)=>[cp.key,{cp,index}]));
  return left.adapter.boundary.slice(1).map((cp,leftIndex)=>{
    const match=rightBoundaries.get(cp.key);if(!match)return null;
    const a=left.adapter.observation(left.record,cp.key),b=right.adapter.observation(right.record,cp.key);
    if(!a||!b||!finite(a.elapsed_seconds)||!finite(b.elapsed_seconds))return null;
    return {key:cp.key,name:cp.name,elapsedA:Number(a.elapsed_seconds),elapsedB:Number(b.elapsed_seconds),gap:Number(b.elapsed_seconds)-Number(a.elapsed_seconds),placeA:finite(a.place_overall)?Number(a.place_overall):null,placeB:finite(b.place_overall)?Number(b.place_overall):null,leftIndex,rightIndex:match.index};
  }).filter(Boolean);
}
function segmentRows(left,right,sameCourse){
  if(!sameCourse)return[];
  const rightBoundaries=new Map(right.adapter.boundary.map((cp,index)=>[cp.key,{cp,index}]));
  const fieldA=left.adapter.segmentStats(left.adapter.records),fieldB=right.adapter.segmentStats(right.adapter.records),rows=[];
  for(let i=1;i<left.adapter.boundary.length;i++){
    const from=left.adapter.boundary[i-1],to=left.adapter.boundary[i],rightTo=rightBoundaries.get(to.key),rightFrom=rightBoundaries.get(from.key);
    if(!rightTo||!rightFrom||rightTo.index!==rightFrom.index+1)continue;
    const sa=left.adapter.segment(left.record,i-1),sb=right.adapter.segment(right.record,rightFrom.index);
    if(!sa||!sb)continue;
    const ma=fieldA[i-1]?.time?.median,mb=fieldB[rightFrom.index]?.time?.median;
    rows.push({name:from.name+' → '+to.name,timeA:sa.seconds,timeB:sb.seconds,delta:sb.seconds-sa.seconds,fieldA:finite(ma)&&ma>0?100*(Number(ma)/Number(sa.seconds)-1):null,fieldB:finite(mb)&&mb>0?100*(Number(mb)/Number(sb.seconds)-1):null});
  }
  return rows;
}
export function buildComparisonModel(boot,left,right){
  const sameCourse=Boolean(left?.adapter?.race?.course_version&&left.adapter.race.course_version===right?.adapter?.race?.course_version);
  const wholeComparable=wholeCourseComparable(boot,left?.adapter?.race,right?.adapter?.race);
  const bothFinished=Boolean(finished(left?.record)&&finished(right?.record)&&finite(left?.record?.finish_seconds)&&finite(right?.record?.finish_seconds));
  return {
    sameCourse,
    wholeComparable,
    finishGap:wholeComparable&&bothFinished?Number(right.record.finish_seconds)-Number(left.record.finish_seconds):null,
    checkpoints:checkpointRows(left,right,sameCourse),
    segments:segmentRows(left,right,sameCourse),
    participants:[left,right].map(item=>({name:item.record.name,bib:item.record.bib,year:item.adapter.race.year,status:item.record.status,finish:item.record.finish_seconds,place:item.record.overall_place,className:item.record.class_name,fieldPercentile:fieldPercentile(item.adapter,item.record),courseVersion:item.adapter.race.course_version}))
  };
}
function participantCard(item,index){
  const p=item.participants[index],side=index?'B':'A';
  return `<article class="multi-year-person"><span class="multi-year-side">${side}</span><div><p class="eyebrow">${esc(p.year)} · #${esc(p.bib||'–')}</p><h3>${esc(p.name)}</h3><dl><div><dt>Status</dt><dd>${esc(p.status||'–')}</dd></div><div><dt>Sluttid</dt><dd>${finite(p.finish)?time(p.finish):'–'}</dd></div><div><dt>Totalplats</dt><dd>${finite(p.place)?'#'+esc(p.place):'–'}</dd></div><div><dt>Snabbare än fältet</dt><dd>${pct(p.fieldPercentile)}</dd></div></dl></div></article>`;
}
function comparisonHtml(model){
  const finishCopy=finite(model.finishGap)?`<strong>${model.finishGap===0?'Samma sluttid':model.finishGap>0?'A snabbare med '+time(model.finishGap):'B snabbare med '+time(Math.abs(model.finishGap))}</strong><span>${model.sameCourse?'Identisk CourseVersion.':'Uttryckligen godkänd helbanekompatibilitet.'}</span>`:`<strong>Sluttider visas utan vinnare</strong><span>Banversionerna saknar uttryckligt stöd för strikt helbaneprestationsjämförelse. Fältpercentilen för respektive år kan fortfarande jämföras.</span>`;
  const checkpoints=model.checkpoints.length?`<section class="multi-year-section"><h3>Passagegap · samma banversion</h3><div class="table-wrap"><table><thead><tr><th>Kontroll</th><th>A</th><th>B</th><th>Lucka B−A</th><th>Placering A/B</th></tr></thead><tbody>${model.checkpoints.map(row=>`<tr><th>${esc(row.name)}</th><td>${time(row.elapsedA)}</td><td>${time(row.elapsedB)}</td><td>${signed(row.gap)}</td><td>${finite(row.placeA)?'#'+row.placeA:'–'} / ${finite(row.placeB)?'#'+row.placeB:'–'}</td></tr>`).join('')}</tbody></table></div><p class="muted small">Endast verkliga gemensamma analysgränser visas. Saknade passager fylls inte ut.</p></section>`:`<section class="multi-year-section multi-year-warning"><h3>Passagegap är avstängt</h3><p>Passagegap och segmentduell kräver exakt samma CourseVersion. Det förhindrar att olika banor behandlas som om de vore samma.</p></section>`;
  const segments=model.segments.length?`<section class="multi-year-section"><h3>Segment mot dig själv och respektive års fält</h3><div class="table-wrap"><table><thead><tr><th>Delsträcka</th><th>A tid</th><th>B tid</th><th>B−A</th><th>A mot fält</th><th>B mot fält</th></tr></thead><tbody>${model.segments.map(row=>`<tr><th>${esc(row.name)}</th><td>${time(row.timeA)}</td><td>${time(row.timeB)}</td><td>${signed(row.delta)}</td><td>${pct(row.fieldA)}</td><td>${pct(row.fieldB)}</td></tr>`).join('')}</tbody></table></div><p class="muted small">Fältvärdet är segmenttid relativt medianen bland kompletta fullföljare i respektive upplaga; positivt betyder snabbare än årets fältmedian.</p></section>`:''; 
  return `<div class="multi-year-comparison"><div class="multi-year-people">${participantCard(model,0)}${participantCard(model,1)}</div><section class="multi-year-finish"><p class="eyebrow">SLUTRESULTAT</p>${finishCopy}</section>${checkpoints}${segments}<section class="multi-year-method"><strong>Jämförelse över år</strong><p>Resultat och fältpercentil kommer från respektive upplaga. Sluttid jämförs direkt endast när banversionerna är identiska eller uttryckligen grupperade som helbanekompatibla. Passage- och segmentdata kräver identisk CourseVersion.</p></section></div>`;
}

export function createMultiYearComparison({boot,loader}){
  const root=document.getElementById('multi-year-comparison'),yearSelect=document.getElementById('multi-year-year'),search=document.getElementById('multi-year-search'),suggestions=document.getElementById('multi-year-suggestions'),chips=document.getElementById('multi-year-selected'),button=document.getElementById('open-multi-year-comparison'),feedback=document.getElementById('multi-year-feedback'),dialog=document.getElementById('multi-year-dialog'),body=document.getElementById('multi-year-dialog-body');
  if(!root||!yearSelect||!search||!suggestions||!chips||!button||!dialog||!body)return{setContext(){}};
  let family=null,activeYear=null,selected=[],suggestionMap=new Map(),searchVersion=0,restored=false,mapController=null;
  const cache=new Map();
  const editions=()=>Object.values(boot.race_catalog||{}).filter(item=>item.race_family===family).sort((a,b)=>b.year-a.year);
  async function loadEdition(meta){
    if(!cache.has(meta.race_key))cache.set(meta.race_key,loader.race(meta.race_key).then(doc=>({meta,adapter:adapt(doc,boot),doc})).catch(error=>{cache.delete(meta.race_key);throw error;}));
    return cache.get(meta.race_key);
  }
  function renderSelected(){
    chips.innerHTML=selected.length?selected.map((item,index)=>`<button type="button" data-multi-year-remove="${esc(item.token)}"><i>${index+1}</i><span>${esc(item.record.name)} · ${item.adapter.race.year}${item.record.bib?' · #'+esc(item.record.bib):''}</span><b>×</b></button>`).join(''):'<span class="selection-empty">Välj exakt två resultat – samma person kan väljas från olika år.</span>';
    button.disabled=selected.length!==2;button.textContent=selected.length===2?'Jämför på kartan och mellan år':'Välj två resultat för kartjämförelse';
    feedback.textContent=selected.length===2?(selected[0].adapter.race.year===selected[1].adapter.race.year?'Två resultat från samma upplaga valda.':'Olika år valda · de två bansträckningarna visas separat på kartan.'):'';
  }
  function hideSuggestions(){suggestions.hidden=true;suggestions.innerHTML='';search.setAttribute('aria-expanded','false');suggestionMap.clear();}
  async function runSearch(){
    const version=++searchVersion,q=search.value.trim();if(!q){hideSuggestions();return;}
    suggestions.hidden=false;suggestions.innerHTML='<p class="picker-empty">Laddar historiska resultat…</p>';search.setAttribute('aria-expanded','true');
    const metas=yearSelect.value==='all'?editions():editions().filter(item=>String(item.year)===yearSelect.value);
    const loaded=(await Promise.allSettled(metas.map(loadEdition))).filter(item=>item.status==='fulfilled').map(item=>item.value);if(version!==searchVersion)return;
    const selectedTokens=new Set(selected.map(item=>item.token)),needle=q.toLocaleLowerCase('sv'),matches=[];
    for(const edition of loaded)for(const record of edition.adapter.records)if(resultMatches(record,q)){const token=tokenFor(edition.meta.race_key,record.source_result_id);if(!selectedTokens.has(token))matches.push({...edition,record,token});}
    matches.sort((x,y)=>{const xn=String(x.record.name).toLocaleLowerCase('sv'),yn=String(y.record.name).toLocaleLowerCase('sv'),xp=xn.startsWith(needle)?0:1,yp=yn.startsWith(needle)?0:1;return xp-yp||y.meta.year-x.meta.year||(Number(x.record.overall_place)||99999)-(Number(y.record.overall_place)||99999)||xn.localeCompare(yn,'sv');});
    suggestionMap=new Map(matches.slice(0,16).map(item=>[item.token,item]));
    suggestions.innerHTML=suggestionMap.size?[...suggestionMap.values()].map((item,index)=>`<button type="button" id="multi-year-option-${index}" role="option" data-multi-year-add="${esc(item.token)}"><span><strong>${esc(item.record.name)}</strong><small>${item.meta.year}${item.record.bib?' · #'+esc(item.record.bib):''}${item.record.club?' · '+esc(item.record.club):''}</small></span><b>${finite(item.record.finish_seconds)?time(item.record.finish_seconds):esc(item.record.status||'–')}</b></button>`).join(''):'<p class="picker-empty">Ingen deltagare hittades i valda år.</p>';
  }
  function shareUrl(){
    const url=new URL(location.href);for(const key of ['xyFamily','xyA','xyB'])url.searchParams.delete(key);
    if(selected.length===2){url.searchParams.set('xyFamily',family);url.searchParams.set('xyA',selected[0].token);url.searchParams.set('xyB',selected[1].token);}
    return url.href;
  }
  async function openComparison(){
    if(selected.length!==2)return;
    mapController?.destroy?.();mapController=null;
    const model=buildComparisonModel(boot,selected[0],selected[1]);
    body.innerHTML='<section class="multi-year-map-card" id="multi-year-map-root"><p class="muted">Laddar dokumenterade bansträckningar…</p></section>'+comparisonHtml(model);
    if(!dialog.open)dialog.showModal();
    const token=selected.map(x=>x.token).join('|');
    const items=await Promise.all(selected.map(async x=>{
      try{
        const route=await loader.route(x.adapter.race);
        const anchors=x.adapter.anchors(x.record,route);
        return {year:x.adapter.race.year,name:x.record.name,
          provenance:route.provenance_label||x.adapter.course?.assets?.route_provenance_label||'Dokumenterad banreferens',
          points:(route.points||[]).map(p=>[p[0],p[1],p[3]]),
          anchors:anchors.map(a=>({time:a.time,distance:a.distance}))};
      }catch{
        return {year:x.adapter.race.year,name:x.record.name,provenance:'Ingen verifierad publik bana för upplagan',points:[],anchors:[]};
      }
    }));
    if(!dialog.open||selected.map(x=>x.token).join('|')!==token)return;
    mapController=globalThis.LoppMultiYearRouteMap?.mount(body.querySelector('#multi-year-map-root'),items);
  }
  async function restore(){
    if(restored)return;const params=new URLSearchParams(location.search);if(params.get('xyFamily')!==family)return;
    const tokens=[params.get('xyA'),params.get('xyB')].filter(Boolean);if(tokens.length!==2)return;const rows=[];
    for(const token of tokens){const parsed=splitToken(token),meta=editions().find(item=>item.race_key===parsed?.raceKey);if(!meta)return;const edition=await loadEdition(meta),record=edition.adapter.byId.get(parsed.id);if(!record)return;rows.push({...edition,record,token});}
    selected=rows;restored=true;renderSelected();await openComparison();
  }
  root.addEventListener('click',event=>{const add=event.target.closest('[data-multi-year-add]'),remove=event.target.closest('[data-multi-year-remove]');if(add){const item=suggestionMap.get(add.dataset.multiYearAdd);if(item&&!selected.some(row=>row.token===item.token)){selected=selected.length<2?[...selected,item]:[selected[1],item];renderSelected();search.value='';hideSuggestions();search.focus();}return;}if(remove){selected=selected.filter(row=>row.token!==remove.dataset.multiYearRemove);renderSelected();return;}});
  function updatePicker(){
    const latest=editions()[0]?.year;
    const current=String(yearSelect.value)===String(latest);
    root.hidden=current;
    const regular=document.getElementById('duel-current-picker');
    if(regular)regular.hidden=!current;
    if(!current)search.focus();else document.getElementById('duel-search')?.focus();
  }
  yearSelect.addEventListener('change',()=>{search.value='';hideSuggestions();updatePicker();});
  search.addEventListener('input',runSearch);search.addEventListener('focus',runSearch);search.addEventListener('keydown',event=>{if(event.key==='Escape')hideSuggestions();if(event.key==='Enter'){const first=suggestions.querySelector('[data-multi-year-add]');if(first){event.preventDefault();first.click();}}});
  button.addEventListener('click',openComparison);
  document.getElementById('close-multi-year-dialog')?.addEventListener('click',()=>dialog.close());
  dialog.addEventListener('close',()=>{mapController?.destroy?.();mapController=null;});
  document.getElementById('multi-year-share')?.addEventListener('click',async event=>{try{await navigator.clipboard.writeText(shareUrl());event.currentTarget.textContent='✓ Länk kopierad';setTimeout(()=>event.currentTarget.textContent='↗ Dela jämförelse',1600);}catch{prompt('Kopiera länken:',shareUrl());}});
  document.addEventListener('click',event=>{if(!event.target.closest('#multi-year-comparison'))hideSuggestions();});
  renderSelected();
  return {
    setContext(nextFamily,nextYear){
      const changed=family!==nextFamily;family=nextFamily;activeYear=Number(nextYear)||null;if(changed){selected=[];restored=false;}
      const latest=editions()[0]?.year;
      const previous=changed?String(latest):yearSelect.value;
      yearSelect.innerHTML=editions().map(item=>`<option value="${item.year}">${item.year}</option>`).join('')+'<option value="all">Alla år</option>';
      const deepLink=new URLSearchParams(location.search).get('xyFamily')===family;
      yearSelect.value=deepLink?'all':editions().some(item=>String(item.year)===String(previous))?String(previous):String(latest);
      renderSelected();if(changed)hideSuggestions();updatePicker();restore().catch(()=>{});
    }
  };
}
