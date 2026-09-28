import {DataLoader} from './data-loader.js';
import {adapt} from './data-adapter.js';
import {urlState,stateURL,switched,storage,sections,flowSections} from './app-state.js';
import {filterRows,finite,finished} from './analytics.js';
import {esc,time,empty} from './charts.js';
import * as views from './views.js';
import {plan} from './race-plan.js';
import {pace,table,tr} from './charts.js';
const $=s=>document.querySelector(s),loader=new DataLoader(),labels={overview:'Översikt',results:'Resultat',dynamics:'Loppets dynamik',segments:'Delsträckor',course:'Bana / Course Intelligence',compare:'Jämför',history:'Historisk översikt',method:'Metod'};
let boot,a,state,store,favorites=[],generation=0,renderVersion=0,mapView=null,profileMap=null,duelMap=null,profileTrigger=null,clubSuggestionIndex=-1;
function safeStorage(){try{return localStorage;}catch{return null;}}
function status(text){$('#load-status').textContent=text;}
function syncURL(replace=false){history[replace?'replaceState':'pushState'](null,'',stateURL(location.href,state));}
function closeMaps(){mapView?.destroy();mapView=null;profileMap?.destroy();profileMap=null;duelMap?.destroy();duelMap=null;}
function saveFavorites(){store.write('favorites',favorites.slice(-40));}
function isFavorite(r){return favorites.some(f=>f.race===a.race.race_key&&f.id===String(r.source_result_id));}
async function loadRace(key,{restore=null,replace=false}={}){
 const token=++generation;closeMaps();$('#profile').close();$('#duel').close();state=switched(state,key);if(restore)Object.assign(state,restore);
 $('#view').setAttribute('aria-busy','true');$('#view').innerHTML=empty('Laddar vald upplaga…');status('Katalog klar → laddar valt lopp/år');$('#year').disabled=true;
 try{const doc=await loader.race(key);if(token!==generation)return;a=adapt(doc,boot);state.compare=state.compare.filter(id=>a.byId.has(id));state.section=normalizeSection(state.section);controls();filters();await render();syncURL(replace);status('Katalog → vald upplaga klar · '+a.records.length+' resultat · rutt och historik efter behov');if(isFlowSection(state.section))scrollToSection(state.section,{focus:state.section!=='overview',behavior:'auto'});if(state.profile)openProfile(state.profile,false);}
 catch(e){if(token===generation){$('#view').innerHTML=empty(e.message)+'<button id="retry">Försök igen</button>';$('#retry').onclick=()=>loadRace(key,{restore:state,replace:true});}}
 finally{if(token===generation){$('#view').setAttribute('aria-busy','false');$('#year').disabled=false;}}
}
function controls(){
 const family=a.race.race_family;
 $('#race-heading').textContent=boot.presentation[family].label+' · '+a.race.year;
 $('#family-cards').innerHTML=Object.entries(boot.presentation).map(([key,p])=>'<button class="family-card family-'+esc(key)+'" data-family="'+esc(key)+'" aria-pressed="'+(family===key)+'"><strong>'+esc(p.label)+'</strong><span>'+esc(p.distance)+'</span><small>'+esc(p.description)+'</small></button>').join('');
 const catalog=Object.values(boot.race_catalog).filter(r=>r.race_family===family);
 const years=[...catalog.map(r=>r.year),...boot.cancelled_years].sort((x,y)=>y-x);
 $('#year').innerHTML=years.map(y=>'<option value="'+y+'" '+(y===a.race.year?'selected':'')+' '+(boot.cancelled_years.includes(y)?'disabled':'')+'>'+y+(boot.cancelled_years.includes(y)?' · Inställt':'')+'</option>').join('');
 $('#analysis-nav').innerHTML=availableSections().map(key=>'<button data-section="'+key+'" class="'+(isFlowSection(key)?'anchor-nav':'special-nav')+'" '+(state.section===key?'aria-current="page"':'')+'>'+labels[key]+'</button>').join('');
 $('#unit').value=state.unit;
}
function filters(){
 const options=(key,label)=>'<label>'+label+'<select data-filter="'+key+'"><option value="">Alla</option>'+[...new Set(a.records.map(r=>r[key]).filter(Boolean))].sort().map(v=>'<option value="'+esc(v)+'">'+esc(v)+'</option>').join('')+'</select></label>';
 const club=a.race.capabilities.club_analysis?'<div class="filter-autocomplete"><label>Klubb & ort<input id="club-filter" data-filter="club" type="search" autocomplete="off" role="combobox" aria-autocomplete="list" aria-controls="club-suggestions" aria-expanded="false" placeholder="Börja skriva klubb eller ort"></label><div id="club-suggestions" class="suggestions" role="listbox" hidden></div></div>':'';
 $('#filters').innerHTML=(a.race.capabilities.sex_filter&&a.race.participant.entity==='person'?'<label>Kön<select data-filter="sex"><option value="">Alla</option><option value="F">Kvinnor</option><option value="M">Män</option></select></label>':'')+options('class_name',a.race.participant.entity==='team'?'Lagklass':'Klass')+options('status','Status')+club+'<button id="reset-filters">Återställ</button>';
}
function selected(){return filterRows(a.records,state.filters);}
function availableFlowSections(){return flowSections.filter(key=>key!=='segments'||a.race.capabilities.segment_analysis).filter(key=>key!=='course'||a.course);}
function availableSections(){return [...availableFlowSections(),'results','compare'];}
function isFlowSection(section){return flowSections.includes(section);}
function normalizeSection(section){return availableSections().includes(section)?section:'overview';}
function updateNav(){document.querySelectorAll('#analysis-nav button').forEach(b=>{if(b.dataset.section===state.section)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});}
function flowHeading(key,title,copy){return '<header class="flow-heading"><p class="eyebrow">'+key+'</p><h2>'+title+'</h2><p>'+copy+'</p></header>';}
function flowSection(key,html){return '<section id="'+key+'" class="flow-section" tabindex="-1" aria-label="'+labels[key]+'">'+html+'</section>';}
function scrollToSection(section,{focus=true,behavior='smooth'}={}){const target=document.getElementById(section);if(!target)return;target.scrollIntoView({block:'start',behavior});if(focus)target.focus({preventScroll:true});}
async function renderAnalysisFlow(v,rows,token){
 const available=availableFlowSections(),parts=[];
 if(available.includes('overview'))parts.push(flowSection('overview',views.overview(a,rows,state,boot)));
 if(available.includes('dynamics'))parts.push(flowSection('dynamics',flowHeading('LOPPETS DYNAMIK','Så rör sig fältet','Percentiler, status och de källstödda perspektiv som finns för den valda upplagan.')+views.dynamics(a,rows,state)));
 if(available.includes('segments'))parts.push(flowSection('segments',flowHeading('DELSTRÄCKOR','Loppet mellan kontrollerna','Tempo, spridning och placeringsrörelser från publicerade passager.')+views.segments(a,rows,state)));
 if(available.includes('course'))parts.push(flowSection('course',flowHeading('COURSE INTELLIGENCE','Banan och dess underlag','Banversion, geometri och lokalt tillgängliga ruttlager med tydliga proveniensgränser.')+views.course(a)));
 if(available.includes('history'))parts.push(flowSection('history',flowHeading('HISTORISK ÖVERSIKT','Loppet över tid','Deltagande visas brett; prestation jämförs endast när banunderlaget uttryckligen tillåter det.')+empty('Laddar liten historiksammanställning…')));
 if(available.includes('method'))parts.push(flowSection('method',flowHeading('METOD','Så är analysen byggd','Källvärden, beräkningar, jämförbarhet och begränsningar samlade på ett ställe.')+views.methodology(a,boot,state)));
 v.innerHTML='<div class="long-analysis">'+parts.join('')+'</div>';
 if(available.includes('course'))renderPlan($('#course'));
 if(available.includes('history')){try{const d=await loader.history();const root=$('#history');if(token===renderVersion&&root)root.innerHTML=flowHeading('HISTORISK ÖVERSIKT','Loppet över tid','Deltagande visas brett; prestation jämförs endast när banunderlaget uttryckligen tillåter det.')+views.historyView(a,d,boot,state);}catch(e){const root=$('#history');if(token===renderVersion&&root)root.innerHTML=flowHeading('HISTORISK ÖVERSIKT','Loppet över tid','Deltagande visas brett; prestation jämförs endast när banunderlaget uttryckligen tillåter det.')+empty(e.message);}}
}
async function render(){
 const token=++renderVersion,rows=selected();mapView?.destroy();mapView=null;
 state.section=normalizeSection(state.section);
 $('#selection-count').textContent='Visar '+rows.length+' av '+a.records.length+' resultat · '+(Object.entries(state.filters).filter(([,v])=>v).map(([k,v])=>k+': '+v).join(' · ')||'Inga fältfilter');
 updateNav();
 const v=$('#view');v.setAttribute('aria-busy','false');
 if(isFlowSection(state.section))await renderAnalysisFlow(v,rows,token);
 if(state.section==='compare'){v.innerHTML=views.compare(a,state);compareOptions('');}
 if(state.section==='results'){renderResults();}
}
function resultMatches(r,q){return (r.name+' '+r.bib+' '+(r.club||'')).toLocaleLowerCase('sv').includes(q.toLocaleLowerCase('sv'));}
function renderResults(){
 $('#view').innerHTML='<section class="card"><h3>Resultatdatabas</h3><p class="muted">'+(state.globalQuery!==null?'Global sökning i hela upplagan. Fältfiltren begränsar inte sökningen.':'Tabellen följer aktuella fältfilter.')+'</p><div class="toolbar"><label>Sök i filtrerade resultat<input id="table-search" type="search" value="'+esc(state.query||'')+'" placeholder="Namn, startnummer, klubb"></label></div><div id="result-table"></div><div class="toolbar"><button id="prev-page">Föregående</button><span id="page-label"></span><button id="next-page">Nästa</button></div></section><section class="card"><h3>Sparade lopp</h3><div id="favorites">'+(favorites.length?favorites.map(f=>'<button data-open-favorite="'+esc(f.race)+'" data-id="'+esc(f.id)+'">'+esc(f.name)+' · '+esc(f.year)+'</button>').join(' '):'<p class="muted">Spara ett resultat från profilen. Favoriter stannar på din enhet.</p>')+'</div></section>';resultTable();
}
function resultTable(){
 let rows=(state.globalQuery!==null?a.records:selected()).filter(r=>resultMatches(r,state.query||''));const key=state.sort||'overall_place',dir=state.dir||1;
 rows=rows.slice().sort((x,y)=>{const p=x[key],q=y[key];if(p==null)return q==null?0:1;if(q==null)return -1;return (typeof p==='number'&&typeof q==='number'?p-q:String(p).localeCompare(String(q),'sv',{numeric:true}))*dir;});
 const pages=Math.max(1,Math.ceil(rows.length/40));state.page=Math.min(state.page,pages);const current=rows.slice((state.page-1)*40,state.page*40);
 const heads=[['overall_place','Plats'],['bib','Nr'],['name',a.race.participant.entity==='team'?'Lag':'Namn'],['class_name','Klass'],['club','Klubb / ort'],['country','Land'],['finish_seconds','Sluttid'],['status','Status']];
 $('#result-table').innerHTML='<div class="table-scroll"><table><thead><tr>'+heads.map(([k,label])=>'<th scope="col" aria-sort="'+(key===k?(dir===1?'ascending':'descending'):'none')+'"><button data-sort="'+k+'">'+label+(key===k?(dir===1?' ↑':' ↓'):'')+'</button></th>').join('')+'</tr></thead><tbody>'+current.map(r=>'<tr tabindex="0" data-result="'+esc(r.source_result_id)+'" aria-label="Öppna '+esc(r.name)+'">'+heads.map(([k])=>'<td '+(k==='name'?'class="name"':'')+'>'+(k==='finish_seconds'?(finished(r)?time(r[k]):'–'):esc(r[k]??'–'))+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>'+(rows.length?'':empty('Inga resultat matchar sökningen och filtren.'));
 $('#page-label').textContent=state.page+' / '+pages+' · '+rows.length+' resultat';$('#prev-page').disabled=state.page<=1;$('#next-page').disabled=state.page>=pages;
}
function compareOptions(q){
 const root=$('#compare-options');if(!root)return;
 q=q.trim();const input=$('#compare-search');if(!q){root.hidden=true;root.innerHTML='';input?.setAttribute('aria-expanded','false');return;}
 const matches=a.records.filter(r=>resultMatches(r,q)&&!state.compare.includes(String(r.source_result_id))).slice(0,8);root.hidden=false;input?.setAttribute('aria-expanded','true');root.innerHTML=matches.length?matches.map(r=>'<button role="option" data-add-compare="'+esc(r.source_result_id)+'"><span><strong>'+esc(r.name)+'</strong><small>#'+esc(r.bib)+' · '+esc(r.class_name||'Klass saknas')+'</small></span><b>Lägg till</b></button>').join(''):'<p class="picker-empty">Inga resultat matchar sökningen.</p>';
}
function clubValues(){const seen=new Map();for(const r of a.records){const value=String(r.club||'').trim(),key=value.toLocaleLowerCase('sv');if(value&&!seen.has(key))seen.set(key,value);}return [...seen.values()].sort((x,y)=>x.localeCompare(y,'sv'));}
function renderClubSuggestions(q){
 const root=$('#club-suggestions'),input=$('#club-filter');if(!root||!input)return;q=q.trim();clubSuggestionIndex=-1;if(!q){root.hidden=true;root.innerHTML='';input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');return;}
 const needle=q.toLocaleLowerCase('sv'),matches=clubValues().filter(v=>v.toLocaleLowerCase('sv').includes(needle)).slice(0,8);root.hidden=false;input.setAttribute('aria-expanded','true');root.innerHTML=matches.length?matches.map((v,i)=>'<button id="club-option-'+i+'" role="option" aria-selected="false" data-club-suggestion="'+esc(v)+'"><span><strong>'+esc(v)+'</strong><small>Klubb / ort i vald upplaga</small></span><b>Välj</b></button>').join(''):'<p class="picker-empty">Ingen klubb eller ort matchar.</p>';
}
function chooseClub(value){const input=$('#club-filter');if(!input)return;input.value=value;state.filters.club=value;renderClubSuggestions('');render();}
function moveClubSuggestion(direction){const input=$('#club-filter'),items=[...document.querySelectorAll('#club-suggestions [data-club-suggestion]')];if(!items.length)return;clubSuggestionIndex=(clubSuggestionIndex+direction+items.length)%items.length;items.forEach((item,i)=>item.setAttribute('aria-selected',i===clubSuggestionIndex));input.setAttribute('aria-activedescendant',items[clubSuggestionIndex].id);items[clubSuggestionIndex].scrollIntoView({block:'nearest'});}
async function showMap(root,records,kind){
 const token=generation;root.innerHTML=empty('Laddar aktuell rutt…');
 try{const [route,module]=await Promise.all([loader.route(a.race),import('./map-engine.js')]);if(token!==generation||!root.isConnected||(kind==='profile'&&!$('#profile').open)||(kind==='duel'&&!$('#duel').open))return;const mounted=await module.mountMap(root,{route,adapter:a,records,segment:state.segment});if(token!==generation||!root.isConnected||(kind==='profile'&&!$('#profile').open)||(kind==='duel'&&!$('#duel').open)){mounted.destroy();return;}if(kind==='profile')profileMap=mounted;else if(kind==='duel')duelMap=mounted;else mapView=mounted;}
 catch(e){if(root.isConnected)root.innerHTML=empty(e.message);}
}
function openProfile(id,update=true){
 const r=a.byId.get(String(id));if(!r)return;profileMap?.destroy();profileMap=null;profileTrigger=document.activeElement;state.profile=String(id);
 $('#profile-body').innerHTML=views.profile(a,r,state,isFavorite(r));if(!$('#profile').open)$('#profile').showModal();if(update)syncURL();
}
async function navigate(section,update=true,{behavior='smooth',focus=true}={}){section=normalizeSection(section);const previous=state.section;state.section=section;if(isFlowSection(section)){if(!isFlowSection(previous)||!document.getElementById(section))await render();else updateNav();if(update)syncURL();scrollToSection(section,{focus,behavior});return;}await render();if(update)syncURL();$('#analysis').scrollIntoView({block:'start',behavior});}
document.addEventListener('click',async e=>{
 const b=e.target.closest('button,a');if(!b||!state)return;
 if(b.dataset.family){const family=b.dataset.family,editions=Object.values(boot.race_catalog).filter(r=>r.race_family===family),race=editions.find(r=>r.year===a.race.year)||editions.sort((x,y)=>y.year-x.year)[0];await loadRace(race.race_key);$('#analysis').scrollIntoView();return;}
 if(b.dataset.clubSuggestion){chooseClub(b.dataset.clubSuggestion);return;}
 if(b.dataset.section){e.preventDefault();await navigate(b.dataset.section);return;}
 if(b.dataset.info){const t=document.getElementById(b.dataset.info);t.hidden=!t.hidden;b.setAttribute('aria-expanded',!t.hidden);return;}
 if(b.dataset.segment){state.segment=+b.dataset.segment;mapView?.select(state.segment);document.querySelectorAll('button[data-segment]').forEach(x=>x.setAttribute('aria-pressed',+x.dataset.segment===state.segment));if(isFlowSection(state.section))await render();return;}
 if(b.dataset.sort){state.dir=state.sort===b.dataset.sort?-(state.dir||1):1;state.sort=b.dataset.sort;resultTable();return;}
 if(b.dataset.addCompare){const id=b.dataset.addCompare;if(!state.compare.includes(id)&&state.compare.length<5)state.compare.push(id);status(state.compare.length+' resultat valda för jämförelse');if(state.section==='compare')await render();syncURL();return;}
 if(b.dataset.removeCompare){state.compare=state.compare.filter(id=>id!==b.dataset.removeCompare);await render();syncURL();return;}
 if(b.dataset.favorite){const r=a.byId.get(b.dataset.favorite);if(isFavorite(r))favorites=favorites.filter(f=>!(f.race===a.race.race_key&&f.id===b.dataset.favorite));else favorites.push({race:a.race.race_key,id:String(r.source_result_id),name:r.name,year:a.race.year});saveFavorites();b.textContent=isFavorite(r)?'Sparad':'Spara lopp';b.setAttribute('aria-pressed',isFavorite(r));return;}
 if(b.dataset.openFavorite){await loadRace(b.dataset.openFavorite,{restore:{profile:b.dataset.id}});return;}
 if(b.id==='reset-filters'){state.filters={};filters();await render();}
 if(b.id==='prev-page'){state.page--;resultTable();}
 if(b.id==='next-page'){state.page++;resultTable();}
 if(b.id==='load-course')await showMap($('#course-map'),[],'course');
 if(b.id==='load-profile-replay')await showMap($('#profile-replay'),[a.byId.get(state.profile)],'profile');
 if(b.id==='open-duel'){const dialog=$('#duel');dialog.showModal();await showMap($('#duel-body'),state.compare.map(id=>a.byId.get(id)),'duel');}
 if(b.id==='close-profile')$('#profile').close();
 if(b.id==='close-duel')$('#duel').close();
});
document.addEventListener('click',e=>{const row=e.target.closest('[data-result]');if(row)openProfile(row.dataset.result);});
document.addEventListener('keydown',e=>{
 if(e.target.id==='club-filter'&&['ArrowDown','ArrowUp','Enter','Escape'].includes(e.key)){if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();moveClubSuggestion(e.key==='ArrowDown'?1:-1);}else if(e.key==='Enter'&&clubSuggestionIndex>=0){e.preventDefault();const item=document.querySelectorAll('#club-suggestions [data-club-suggestion]')[clubSuggestionIndex];if(item)chooseClub(item.dataset.clubSuggestion);}else if(e.key==='Escape')renderClubSuggestions('');return;}
 if(e.key==='Escape'){document.querySelectorAll('[data-info][aria-expanded=true]').forEach(b=>{document.getElementById(b.dataset.info).hidden=true;b.setAttribute('aria-expanded','false');});}
 if(e.key==='Enter'||e.key===' '){const row=e.target.closest('[data-result]');if(row){e.preventDefault();openProfile(row.dataset.result);}const hit=e.target.closest('svg [data-segment]');if(hit){e.preventDefault();state.segment=+hit.dataset.segment;render();}}
});
document.addEventListener('input',e=>{
 if(!state)return;if(e.target.dataset.filter){state.globalQuery=null;state.filters[e.target.dataset.filter]=e.target.value;state.page=1;render();if(e.target.id==='club-filter')renderClubSuggestions(e.target.value);}
 if(e.target.id==='table-search'){state.query=e.target.value;state.page=1;resultTable();}
 if(e.target.id==='compare-search')compareOptions(e.target.value);
 if(e.target.id==='goal-hours'||e.target.id==='goal-minutes')renderPlanOutput();
});
document.addEventListener('click',e=>{if(!e.target.closest('.filter-autocomplete'))renderClubSuggestions('');if(!e.target.closest('.compare-search-wrap')){const root=$('#compare-options');if(root){root.hidden=true;$('#compare-search')?.setAttribute('aria-expanded','false');}}});
$('#year').onchange=()=>{const r=Object.values(boot.race_catalog).find(r=>r.race_family===a.race.race_family&&r.year===+$('#year').value);if(r)loadRace(r.race_key);};
$('#unit').onchange=()=>{state.unit=$('#unit').value;store.write('unit',state.unit);render();if(state.profile)openProfile(state.profile,false);};
$('#global-search').onsubmit=async e=>{e.preventDefault();if(!a)return;const q=$('#lookup').value.trim(),matches=a.records.filter(r=>resultMatches(r,q));if(matches.length===1)openProfile(matches[0].source_result_id);else{state.query=q;state.globalQuery=q;state.page=1;await navigate('results');$('#analysis').scrollIntoView();}};
$('#profile').addEventListener('close',()=>{profileMap?.destroy();profileMap=null;if(state?.profile){state.profile=null;syncURL(true);}profileTrigger?.focus?.();});
$('#duel').addEventListener('close',()=>{duelMap?.destroy();duelMap=null;});
addEventListener('popstate',async()=>{if(!boot)return;const restored=urlState(location.href,boot.race_catalog,boot.default_race);if(restored.raceKey!==state.raceKey)await loadRace(restored.raceKey,{restore:restored,replace:true});else{Object.assign(state,restored);state.section=normalizeSection(state.section);await render();if(isFlowSection(state.section))scrollToSection(state.section,{focus:true,behavior:'auto'});if(restored.profile)openProfile(restored.profile,false);else $('#profile').close();}});
async function start(){
 try{$('.landscape')?.setAttribute('aria-label','Löpare på en blommande strandstig längs Österlensk kust');boot=await loader.bootstrap();store=storage(boot.event.storage_namespace,safeStorage());const saved=store.read('favorites',[]);favorites=Array.isArray(saved)?saved.filter(f=>f&&typeof f.id==='string'&&boot.race_catalog[f.race]).slice(-40):[];const unit=store.read('unit','pace');state={...urlState(location.href,boot.race_catalog,boot.default_race),unit:unit==='speed'?'speed':'pace',filters:{},segment:0,page:1};await loadRace(state.raceKey,{restore:{...state},replace:true});}
 catch(e){$('#view').innerHTML=empty(e.message);status('Katalogen kunde inte laddas. Ladda om sidan för att försöka igen.');}
}
start();


function renderPlan(root=$('#view')){
 if(!a.race.capabilities.goal_pace)return;
 const target=boot.presentation[a.race.race_family].default_goal_seconds,h=Math.floor(target/3600),m=Math.floor(target%3600/60);
 root.insertAdjacentHTML('beforeend','<section class="card"><h3>Måltempo & loppplan</h3><p>En historisk referens, inte en individuell prognos.</p><div class="toolbar"><label>Timmar<input id="goal-hours" type="number" min="0" max="48" value="'+h+'"></label><label>Minuter<input id="goal-minutes" type="number" min="0" max="59" value="'+m+'"></label></div><div id="plan-output"></div></section>');
 renderPlanOutput();
}
function renderPlanOutput(){
 const h=Number($('#goal-hours')?.value),m=Number($('#goal-minutes')?.value),target=h*3600+m*60,root=$('#plan-output');if(!root)return;
 if(h<0||h>48||m<0||m>59||target<=0){root.innerHTML=empty('Ange en positiv måltid och minuter mellan 0 och 59.');return;}
 const p=plan(a,target);
 root.innerHTML='<p>Måltempo: <strong>'+pace(p.pace,state.unit)+'</strong> · nominell distans</p>'+(p.segments.length?table(['Till kontroll','Delsträcketid'],p.segments.map(s=>tr([esc(s.name),time(s.seconds)]))):'')+'<p class="muted">'+(p.method==='observed'?'Kalibrerat på kompletta publicerade passager i just denna upplaga, n='+p.n+'. Medianandelar av varje deltagares sluttid normaliseras till måltiden. Fältfiltren påverkar inte referensen.':p.method==='distance'?'Distansfallback: fördelat enbart på explicita rapporterade segmentdistanser. Saknad distans lämnas oallokerad.':'Enkel beräkning från måltid och nominell distans. Inget segmentunderlag finns.')+'</p>';
}
