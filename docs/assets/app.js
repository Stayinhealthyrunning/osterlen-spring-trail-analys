import {DataLoader} from './data-loader.js';
import {adapt} from './data-adapter.js';
import {urlState,stateURL,switched,storage,sections,flowSections} from './app-state.js';
import {filterRows,finite,finished,median} from './analytics.js';
import {esc,time,empty,statusLabel,info,elevation} from './charts.js';
import * as views from './views.js';
import {plan} from './race-plan.js';
import {pace,table,tr} from './charts.js';
const $=s=>document.querySelector(s),loader=new DataLoader(),labels={overview:'Översikt',statistics:'Statistik',gender:'Genusperspektiv','age-analysis':'Klass & ålder',segments:'Delsträckor',history:'Historik',clubs:'Klubb & ort',method:'Metod',results:'Resultat',compare:'Jämför'};
let boot,a,state,store,favorites=[],generation=0,renderVersion=0,mapView=null,profileMap=null,duelMap=null,headToHeadCourse=null,profileTrigger=null,compareTrigger=null,clubSuggestionIndex=-1,lookupSuggestionIndex=-1,compareSuggestionIndex=-1,duelSuggestionIndex=-1,clubArenaSuggestionIndex=-1,sectionObserver=null;
function safeStorage(){try{return localStorage;}catch{return null;}}
function status(text){$('#load-status').textContent=text;}
function syncURL(replace=false){history[replace?'replaceState':'pushState'](null,'',stateURL(location.href,state));}
function closeMaps(){mapView?.destroy();mapView=null;profileMap?.destroy();profileMap=null;duelMap?.destroy();duelMap=null;headToHeadCourse?.destroy();headToHeadCourse=null;}
function saveFavorites(){store.write('favorites',favorites.slice(-40));}
function isFavorite(r){return favorites.some(f=>f.race===a.race.race_key&&f.id===String(r.source_result_id));}
async function loadRace(key,{restore=null,replace=false,scroll=true}={}){
 const token=++generation;closeMaps();$('#profile').close();if($('#compare-dialog')?.open)$('#compare-dialog').close();$('#duel').close();state=switched(state,key);if(restore)Object.assign(state,restore);
 $('#view').setAttribute('aria-busy','true');$('#view').innerHTML=empty('Laddar vald upplaga…');status('Katalog klar → laddar valt lopp/år');$('#year').disabled=true;
 try{const doc=await loader.race(key);if(token!==generation)return;a=adapt(doc,boot);state.compare=state.compare.filter(id=>a.byId.has(id)).slice(0,a.race.capabilities.replay?5:2);state.section=normalizeSection(state.section);controls();filters();await render();syncURL(replace);status('Katalog → vald upplaga klar · '+a.records.length+' resultat · historik i analysflödet · rutt/replay efter behov');if(scroll&&isFlowSection(state.section))scrollToSection(state.section,{focus:state.section!=='overview',behavior:'auto'});if(state.profile)openProfile(state.profile,false);}
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
 const nav=[['runner-lookup','Löpare'],['map-duel-panel','Karta & Kartduell'],['goal-pace','Måltempo'],...availableSections().filter(key=>key!=='compare').map(key=>[key,labels[key]])];
 $('#analysis-nav').innerHTML=nav.map(([key,label])=>'<button '+(key==='runner-lookup'||key==='map-duel-panel'||key==='goal-pace'?'data-scroll-target="'+key+'"':'data-section="'+key+'"')+' class="'+(isFlowSection(key)?'anchor-nav':'special-nav')+'" '+(state.section===key?'aria-current="location"':'')+'>'+label+'</button>').join('');
 $('#unit').value=state.unit;
 renderTopTools();
 renderGoalPace();
}
function filters(){
 const options=(key,label)=>'<label>'+label+'<select data-filter="'+key+'"><option value="">Alla</option>'+[...new Set(a.records.map(r=>r[key]).filter(Boolean))].sort((x,y)=>String(x).localeCompare(String(y),'sv',{numeric:true})).map(v=>'<option value="'+esc(v)+'">'+esc(v)+'</option>').join('')+'</select></label>';
 const club=a.race.capabilities.club_analysis?'<div class="filter-autocomplete"><label>Klubb & ort<input id="club-filter" data-filter="club" type="search" autocomplete="off" role="combobox" aria-autocomplete="list" aria-controls="club-suggestions" aria-expanded="false" placeholder="Börja skriva klubb eller ort"></label><div id="club-suggestions" class="suggestions" role="listbox" hidden></div></div>':'';
 const statusOrder=['FINISHED','DNF','DNS','DSQ','UNKNOWN'],present=new Set(a.records.map(r=>r.status).filter(Boolean)),statuses=statusOrder.filter(v=>present.has(v)),statusFilter='<label>Status<select data-filter="status"><option value="">Alla</option>'+statuses.map(v=>'<option value="'+esc(v)+'">'+esc(statusLabel(v))+'</option>').join('')+'</select></label>';
 $('#filters').innerHTML=(a.race.capabilities.sex_filter&&a.race.participant.entity==='person'?'<label>Kön<select data-filter="sex"><option value="">Alla</option><option value="F">Kvinnor</option><option value="M">Män</option></select></label>':'')+options('class_name',a.race.participant.entity==='team'?'Lagklass':'Klass')+statusFilter+club+'<button id="reset-filters">Återställ</button>';
}
function selected(){return filterRows(a.records,state.filters);}
function compareLimit(){return a?.race?.capabilities?.replay?5:2;}
function filterSummary(){
 const names={sex:'Kön',class_name:a.race.participant.entity==='team'?'Lagklass':'Klass',status:'Status',club:'Klubb / ort'},value=(key,v)=>key==='sex'?(v==='F'?'Kvinnor':v==='M'?'Män':v):key==='status'?statusLabel(v):v;
 const active=Object.entries(state.filters).filter(([,v])=>v);return active.map(([key,v])=>(names[key]||key)+': '+value(key,v)).join(' · ')||'Inga fältfilter';
}
function availableFlowSections(){return flowSections.filter(key=>key!=='segments'||a.race.capabilities.segment_analysis).filter(key=>key!=='gender'||a.race.participant.entity==='person'||a.race.participant.entity==='team').filter(key=>key!=='age-analysis'||a.race.capabilities.age_analysis||a.race.participant.entity==='team').filter(key=>key!=='clubs'||a.race.capabilities.club_analysis);}
function availableSections(){return [...availableFlowSections(),'results'];}
function isFlowSection(section){return flowSections.includes(section);}
function normalizeSection(section){return availableSections().includes(section)?section:'overview';}
function updateNav(){document.querySelectorAll('#analysis-nav button').forEach(b=>{if(b.dataset.section===state.section)b.setAttribute('aria-current','location');else b.removeAttribute('aria-current');});}
function flowHeading(key,title,copy){return '<div class="flow-heading section-intro"><p class="eyebrow">'+key+'</p><h2>'+title+'</h2><p>'+copy+'</p></div>';}
function flowSection(key,html){return '<section id="'+key+'" class="flow-section" tabindex="-1" aria-label="'+labels[key]+'">'+html+'</section>';}
function motionBehavior(behavior='smooth'){return behavior==='smooth'&&globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'auto':behavior;}
function scrollToSection(section,{focus=true,behavior='smooth'}={}){const target=document.getElementById(section);if(!target)return;target.scrollIntoView({block:'start',behavior:motionBehavior(behavior)});if(focus)target.focus({preventScroll:true});}
function observeFlowSections(){
 sectionObserver?.disconnect();sectionObserver=null;if(!('IntersectionObserver' in globalThis))return;
 sectionObserver=new IntersectionObserver(entries=>{const visible=entries.filter(e=>e.isIntersecting).sort((x,y)=>y.intersectionRatio-x.intersectionRatio)[0],key=visible?.target?.id;if(key&&isFlowSection(key)&&state.section!==key){state.section=key;updateNav();}},{rootMargin:'-18% 0px -62% 0px',threshold:[0,.15,.35,.6]});
 document.querySelectorAll('.flow-section').forEach(el=>sectionObserver.observe(el));
}
async function loadOverviewElevation(token){
 const root=$('#overview-elevation'),badge=$('#overview-elevation-source');if(!root)return;
 if(!a.course?.assets?.route){root.innerHTML=empty('Lokalt användbar rutt saknas för den här upplagan. Ingen annan upplagas höjdprofil lånas.');if(badge)badge.textContent='Rutt saknas';return;}
 try{const route=await loader.route(a.race);if(token!==renderVersion||!root.isConnected)return;root.innerHTML=elevation(route.elevation,route.anchors);if(badge)badge.textContent=route.provenance_label||'Ruttbaserad höjd';}
 catch(e){if(token===renderVersion&&root.isConnected){root.innerHTML=empty(e.message);if(badge)badge.textContent='Höjdprofil saknas';}}
}
async function renderAnalysisFlow(v,rows,token){
 const available=availableFlowSections(),parts=[];
 if(available.includes('overview'))parts.push(flowSection('overview',views.overview(a,rows,state,boot)));
 if(available.includes('statistics'))parts.push(flowSection('statistics',flowHeading('STATISTIKVERKSTAD','Vad hände i loppet?','Fördjupa dig i placeringar, avhopp, fartmönster och vad en viss sluttid brukar räcka till.')+views.statistics(a,rows,state)));
 if(available.includes('gender'))parts.push(flowSection('gender',flowHeading('GENUSPERSPEKTIV','Fältet ur flera perspektiv','Deltagande, fullföljande och pacing för hela urvalet, kvinnor och män – när källstödet räcker.')+views.gender(a,rows,state)));
 if(available.includes('age-analysis')){const team=a.race.participant.entity==='team';parts.push(flowSection('age-analysis',flowHeading(team?'OFFICIELLA KLASSER':'KLASS & ÅLDER',team?'Klassanalys':'Ålderslabbet',team?'Jämför deltagande, målgång, fart och pacing mellan källans publicerade lagklasser.':'Analytiska åldersgrupper – inte officiella tävlingsklasser. Grupper med för litet underlag döljs.')+views.ageAnalysis(a,rows,state)));}
 if(available.includes('segments'))parts.push(flowSection('segments',flowHeading('DELSTRÄCKELABBET','Var avgjordes loppet?','Jämför segment, relativa prestationer och placeringar utan att fabricera saknade passager.')+views.segments(a,rows,state)+views.course(a)));
 if(available.includes('history'))parts.push(flowSection('history',flowHeading('HISTORIK','År för år','Deltagande visas brett; prestation jämförs endast när banunderlaget uttryckligen tillåter det.')+empty('Laddar liten historiksammanställning…')));
 if(available.includes('clubs'))parts.push(flowSection('clubs',flowHeading('KLUBB- OCH ORTSARENAN','Gemenskap i siffror','Sök en klubb eller välj upp till fyra för att jämföra deltagare, målgång och fart i det valda loppet.')+views.clubs(a,rows,state)));
 if(available.includes('method'))parts.push(flowSection('method',flowHeading('METOD','Så är analysen byggd','Källvärden, beräkningar, jämförbarhet och begränsningar samlade på ett ställe.')+views.methodology(a,boot,state,rows)));
 v.innerHTML='<div class="long-analysis">'+parts.join('')+'</div>';observeFlowSections();renderTargetSimulator(rows);if(available.includes('overview'))loadOverviewElevation(token);
 if(available.includes('history')){try{const d=await loader.history();const root=$('#history');if(token===renderVersion&&root)root.innerHTML=flowHeading('HISTORIK','År för år','Deltagande visas brett; prestation jämförs endast när banunderlaget uttryckligen tillåter det.')+views.historyView(a,d,boot,state);}catch(e){const root=$('#history');if(token===renderVersion&&root)root.innerHTML=flowHeading('HISTORIK','År för år','Deltagande visas brett; prestation jämförs endast när banunderlaget uttryckligen tillåter det.')+empty(e.message);}}
}
async function render(){
 const token=++renderVersion,rows=selected();sectionObserver?.disconnect();sectionObserver=null;mapView?.destroy();mapView=null;
 state.section=normalizeSection(state.section);
 $('#selection-count').textContent='Visar '+rows.length+' av '+a.records.length+' resultat · '+filterSummary();
 updateNav();
 const v=$('#view');v.setAttribute('aria-busy','false');
 if(isFlowSection(state.section))await renderAnalysisFlow(v,rows,token);
 if(state.section==='compare'){v.innerHTML=views.compare(a,state);compareOptions('');}
 if(state.section==='results'){renderResults();}
}
function renderTargetSimulator(rows){
 const root=$('#target-time-simulator');if(!root)return;const values=rows.filter(finished).map(r=>Number(r.finish_seconds)).sort((x,y)=>x-y);if(values.length<5){root.innerHTML=empty('Minst fem fullföljare krävs.');return;}const min=Math.floor(values[0]/60)*60,max=Math.ceil(values.at(-1)/60)*60,mid=Math.round(median(values)/60)*60;root.innerHTML='<label>Välj måltid<input id="target-time" type="range" min="'+min+'" max="'+max+'" step="60" value="'+mid+'"></label><strong id="target-time-label">'+time(mid)+'</strong><div id="target-time-result"></div>';updateTargetSimulator(values,mid);
}
function updateTargetSimulator(values,target){
 const label=$('#target-time-label'),out=$('#target-time-result');if(!label||!out)return;label.textContent=time(target);const faster=values.filter(v=>v<target).length,share=100*faster/values.length,place=Math.min(values.length,faster+1);out.innerHTML='<p><strong>Cirka plats '+place+'</strong> av '+values.length+' fullföljare</p><p>Snabbare än '+share.toFixed(1).replace('.',',')+' % av aktuellt urval.</p>';
}
function renderTopTools(){
 const favRoot=$('#favorites-top'),current=favorites.filter(f=>f.race===a.race.race_key&&a.byId.has(f.id));
 if(favRoot)favRoot.innerHTML=current.length?'<div class="favorites-list">'+current.map(f=>'<button type="button" data-open-favorite="'+esc(f.race)+'" data-id="'+esc(f.id)+'"><strong>'+esc(f.name)+'</strong><small>'+a.race.year+' · öppna analys</small></button>').join('')+'</div>':'<p class="favorites-empty">Inga sparade '+(a.race.participant.entity==='team'?'lag':'löpare')+' i den här upplagan ännu.</p>';
 const picked=state.compare.map(id=>a.byId.get(id)).filter(Boolean),chips=$('#duel-selected');if(chips)chips.innerHTML=picked.map((r,i)=>'<button type="button" data-duel-remove="'+esc(r.source_result_id)+'"><i>'+(i+1)+'</i>'+esc(r.name)+' <span>×</span></button>').join('');
 const head=$('#open-head-to-head'),map=$('#open-map-duel');if(head){head.disabled=picked.length!==2;head.textContent=picked.length===2?'Öppna Direktjämförelse':'Välj två resultat';}if(map){map.hidden=!a.race.capabilities.replay;map.disabled=picked.length<2||picked.length>5;map.textContent=picked.length>=2?'Öppna Kartduell':'Välj minst två resultat';}
}
function duelOptions(query){
 const root=$('#duel-suggestions'),input=$('#duel-search');if(!root||!input)return;const q=query.trim();duelSuggestionIndex=-1;
 if(!q){root.hidden=true;root.innerHTML='';input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');return;}
 const limit=compareLimit();root.hidden=false;input.setAttribute('aria-expanded','true');
 if(state.compare.length>=limit){root.innerHTML='<p class="picker-empty">Max '+limit+' resultat valda. Ta bort ett val för att lägga till ett annat.</p>';return;}
 const needle=q.toLocaleLowerCase('sv'),matches=a.records.filter(r=>resultMatches(r,q)&&!state.compare.includes(String(r.source_result_id))).sort((x,y)=>{const rank=r=>String(r.name).toLocaleLowerCase('sv').startsWith(needle)?0:String(r.bib)===q?1:2;return rank(x)-rank(y)||String(x.name).localeCompare(String(y.name),'sv');}).slice(0,8);
 root.innerHTML=matches.length?matches.map((r,i)=>'<button id="duel-option-'+i+'" type="button" role="option" aria-selected="false" data-duel-add="'+esc(r.source_result_id)+'"><span><strong>'+esc(r.name)+'</strong><small>#'+esc(r.bib)+' · '+esc(r.class_name||'Klass saknas')+'</small></span><b>Lägg till</b></button>').join(''):'<p class="picker-empty">Inga resultat matchar.</p>';
}
function moveDuelSuggestion(direction){const input=$('#duel-search'),items=[...document.querySelectorAll('#duel-suggestions [data-duel-add]')];if(!items.length)return;duelSuggestionIndex=(duelSuggestionIndex+direction+items.length)%items.length;items.forEach((item,i)=>item.setAttribute('aria-selected',i===duelSuggestionIndex));input.setAttribute('aria-activedescendant',items[duelSuggestionIndex].id);items[duelSuggestionIndex].scrollIntoView({block:'nearest'});}
function buildReplayReferences(record,route){
 const cps=a.checkpoints.filter(cp=>cp.replay_anchor&&finite(route.anchors?.[cp.key])).map(cp=>({cp,distance:Number(route.anchors[cp.key])}));
 const build=(id,label,color,rows)=>{const anchors=[];for(const {cp,distance} of cps){const values=rows.map(r=>a.observation(r,cp.key)?.elapsed_seconds).filter(finite);if(values.length<5)continue;const value=median(values);if(!finite(value)||(anchors.length&&value<=anchors.at(-1).time))continue;anchors.push({time:value,distance});}return anchors.length>=2?{id,label,color,anchors,count:rows.length}:null;};
 const finishers=a.records.filter(finished),out=[build('field','Hela fältet','#596761',finishers)];
 if(record.class_name)out.push(build('class','Min klass','#138a78',finishers.filter(r=>r.class_name===record.class_name)));
 if(record.sex==='F'||record.sex==='M')out.push(build('sex',record.sex==='F'?'Kvinnor':'Män',record.sex==='F'?'#b51d60':'#2563eb',finishers.filter(r=>r.sex===record.sex)));
 return out.filter(Boolean);
}
function replayInsights(record){
 if(!a.race.capabilities.segment_analysis)return [];const field=a.segmentStats(a.records),items=a.boundary.slice(1).map((cp,i)=>{const s=a.segment(record,i),m=field[i]?.time?.median;return s&&finite(m)?{name:a.boundary[i].name+' → '+cp.name,delta:s.seconds-m,segmentIndex:i}:null;}).filter(Boolean);if(!items.length)return [];const strongest=items.slice().sort((x,y)=>x.delta-y.delta)[0],toughest=items.slice().sort((x,y)=>y.delta-x.delta)[0];return [{title:'Starkaste del',primary:strongest.name,detail:(strongest.delta<=0?'−':'+')+time(Math.abs(strongest.delta))+' mot fältmedian',segmentIndex:strongest.segmentIndex},{title:'Tuffaste del',primary:toughest.name,detail:(toughest.delta<=0?'−':'+')+time(Math.abs(toughest.delta))+' mot fältmedian',segmentIndex:toughest.segmentIndex}];
}
function renderGoalPace(){
 const root=$('#goal-pace-content'),panel=$('#goal-pace');if(!root||!panel)return;panel.hidden=!a.race.capabilities.goal_pace;if(panel.hidden){root.innerHTML='';return;}
 $('#goal-pace-race').textContent=boot.presentation[a.race.race_family].label+' · '+a.race.year;const target=boot.presentation[a.race.race_family].default_goal_seconds,h=Math.floor(target/3600),m=Math.floor(target%3600/60);
 root.innerHTML='<div class="card-heading"><div><h3>Måltempo & loppplan</h3><p>En historisk referens, inte en individuell prognos.</p></div>'+info('plan-method','Måltiden fördelas på publicerade kompletta passager i vald upplaga när sådant underlag finns. Resultatet är en planeringsreferens, inte en individuell prognos.')+'</div><div class="toolbar"><label>Timmar<input id="goal-hours" type="number" min="0" max="48" value="'+h+'"></label><label>Minuter<input id="goal-minutes" type="number" min="0" max="59" value="'+m+'"></label></div><div id="plan-output"></div>';renderPlanOutput();
}
function resultMatches(r,q){return (r.name+' '+r.bib+' '+(r.club||'')).toLocaleLowerCase('sv').includes(q.toLocaleLowerCase('sv'));}
function lookupOptions(query){const root=$('#lookup-suggestions'),input=$('#lookup');if(!root||!input)return;const q=query.trim();lookupSuggestionIndex=-1;if(!q){root.hidden=true;root.innerHTML='';input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');return;}const needle=q.toLocaleLowerCase('sv'),matches=a.records.filter(r=>resultMatches(r,q)).sort((x,y)=>{const rank=r=>String(r.name).toLocaleLowerCase('sv').startsWith(needle)?0:String(r.bib)===q?1:2;return rank(x)-rank(y)||String(x.name).localeCompare(String(y.name),'sv');}).slice(0,8);root.hidden=false;input.setAttribute('aria-expanded','true');root.innerHTML=matches.length?matches.map((r,i)=>'<button id="lookup-option-'+i+'" type="button" role="option" aria-selected="false" data-lookup-result="'+esc(r.source_result_id)+'"><span><strong>'+esc(r.name)+'</strong><small>#'+esc(r.bib)+' · '+esc(r.class_name||'Klass saknas')+' · '+(finished(r)?time(r.finish_seconds):esc(statusLabel(r.status)))+'</small></span><b>Öppna profil</b></button>').join(''):'<p class="picker-empty">Inga löpare eller lag matchar i vald upplaga.</p>';}
function moveLookupSuggestion(direction){const input=$('#lookup'),items=[...document.querySelectorAll('#lookup-suggestions [data-lookup-result]')];if(!items.length)return;lookupSuggestionIndex=(lookupSuggestionIndex+direction+items.length)%items.length;items.forEach((item,i)=>item.setAttribute('aria-selected',i===lookupSuggestionIndex));input.setAttribute('aria-activedescendant',items[lookupSuggestionIndex].id);items[lookupSuggestionIndex].scrollIntoView({block:'nearest'});}
function chooseLookup(id){const input=$('#lookup');lookupOptions('');if(input)input.value='';openProfile(id);}

function renderResults(){
 $('#view').innerHTML='<section class="card"><h3>Resultatdatabas</h3><p class="muted">'+(state.globalQuery!==null?'Global sökning i hela upplagan. Fältfiltren begränsar inte sökningen.':'Tabellen följer aktuella fältfilter.')+'</p><div class="toolbar"><label>Sök i filtrerade resultat<input id="table-search" type="search" value="'+esc(state.query||'')+'" placeholder="Namn, startnummer, klubb"></label></div><div id="result-table"></div><div class="toolbar"><button id="prev-page">Föregående</button><span id="page-label"></span><button id="next-page">Nästa</button></div></section><section class="card"><h3>Sparade lopp</h3><div id="favorites">'+(favorites.length?favorites.map(f=>'<button data-open-favorite="'+esc(f.race)+'" data-id="'+esc(f.id)+'">'+esc(f.name)+' · '+esc(f.year)+'</button>').join(' '):'<p class="muted">Spara ett resultat från profilen. Favoriter stannar på din enhet.</p>')+'</div></section>';resultTable();
}
function resultTable(){
 let rows=(state.globalQuery!==null?a.records:selected()).filter(r=>resultMatches(r,state.query||''));const key=state.sort||'overall_place',dir=state.dir||1;
 rows=rows.slice().sort((x,y)=>{const p=x[key],q=y[key];if(p==null)return q==null?0:1;if(q==null)return -1;return (typeof p==='number'&&typeof q==='number'?p-q:String(p).localeCompare(String(q),'sv',{numeric:true}))*dir;});
 const pages=Math.max(1,Math.ceil(rows.length/40));state.page=Math.min(state.page,pages);const current=rows.slice((state.page-1)*40,state.page*40);
 const heads=[['overall_place','Plats'],['bib','Nr'],['name',a.race.participant.entity==='team'?'Lag':'Namn'],['class_name','Klass'],['club','Klubb / ort'],['country','Land'],['finish_seconds','Sluttid'],['status','Status']];
 $('#result-table').innerHTML='<div class="table-scroll"><table><thead><tr>'+heads.map(([k,label])=>'<th scope="col" aria-sort="'+(key===k?(dir===1?'ascending':'descending'):'none')+'"><button data-sort="'+k+'">'+label+(key===k?(dir===1?' ↑':' ↓'):'')+'</button></th>').join('')+'</tr></thead><tbody>'+current.map(r=>'<tr tabindex="0" data-result="'+esc(r.source_result_id)+'" aria-label="Öppna '+esc(r.name)+'">'+heads.map(([k])=>'<td '+(k==='name'?'class="name"':'')+'>'+(k==='finish_seconds'?(finished(r)?time(r[k]):'–'):k==='status'?esc(statusLabel(r[k])):esc(r[k]??'–'))+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>'+(rows.length?'':empty('Inga resultat matchar sökningen och filtren.'));
 $('#page-label').textContent=state.page+' / '+pages+' · '+rows.length+' resultat';$('#prev-page').disabled=state.page<=1;$('#next-page').disabled=state.page>=pages;
}
function compareOptions(q){
 const root=$('#compare-options');if(!root)return;
 q=q.trim();const input=$('#compare-search');compareSuggestionIndex=-1;if(!q){root.hidden=true;root.innerHTML='';input?.setAttribute('aria-expanded','false');input?.removeAttribute('aria-activedescendant');return;}
 root.hidden=false;input?.setAttribute('aria-expanded','true');const limit=compareLimit();if(state.compare.length>=limit){root.innerHTML='<p class="picker-empty">'+(limit===5?'Max fem resultat kan väljas till Kartduell.':'Den här upplagan saknar rutt/replay; Direktjämförelse använder exakt två resultat.')+' Ta bort ett val för att lägga till ett annat.</p>';return;}
 const needle=q.toLocaleLowerCase('sv'),matches=a.records.filter(r=>resultMatches(r,q)&&!state.compare.includes(String(r.source_result_id))).sort((x,y)=>{const rank=r=>String(r.name).toLocaleLowerCase('sv').startsWith(needle)?0:String(r.bib)===q?1:2;return rank(x)-rank(y)||String(x.name).localeCompare(String(y.name),'sv');}).slice(0,8);
 root.innerHTML=matches.length?matches.map((r,i)=>'<button id="compare-option-'+i+'" role="option" aria-selected="false" data-add-compare="'+esc(r.source_result_id)+'"><span><strong>'+esc(r.name)+'</strong><small>#'+esc(r.bib)+' · '+esc(r.class_name||'Klass saknas')+'</small></span><b>Lägg till</b></button>').join(''):'<p class="picker-empty">Inga resultat matchar sökningen.</p>';
}
function moveCompareSuggestion(direction){
 const input=$('#compare-search'),items=[...document.querySelectorAll('#compare-options [data-add-compare]')];if(!items.length)return;
 compareSuggestionIndex=(compareSuggestionIndex+direction+items.length)%items.length;items.forEach((item,i)=>item.setAttribute('aria-selected',i===compareSuggestionIndex));input?.setAttribute('aria-activedescendant',items[compareSuggestionIndex].id);items[compareSuggestionIndex].scrollIntoView({block:'nearest'});
}
async function loadHeadToHeadCourse(){
 const root=$('#head-to-head-course');headToHeadCourse?.destroy();headToHeadCourse=null;if(!root||state.compare.length!==2)return;
 if(!a.course?.assets?.route){root.innerHTML=empty('Lokalt användbar rutt saknas för den här upplagan. Ingen annan upplagas bana lånas.');return;}
 try{const [route,module]=await Promise.all([loader.route(a.race),import('./map-engine.js')]);if(!root.isConnected||!$('#compare-dialog')?.open)return;headToHeadCourse=await module.mountCourseContext(root,{route,adapter:a,segment:0});}
 catch(e){if(root.isConnected)root.innerHTML=empty(e.message);}
}
function renderCompareDialog(){
 const dialog=$('#compare-dialog'),body=$('#compare-dialog-body');if(!dialog||!body||!a)return;
 headToHeadCourse?.destroy();headToHeadCourse=null;body.innerHTML=views.compare(a,state);compareOptions('');if(state.compare.length===2)requestAnimationFrame(()=>loadHeadToHeadCourse());
}
function openCompareDialog(){
 const dialog=$('#compare-dialog');if(!dialog||!a)return;compareTrigger=document.activeElement;renderCompareDialog();if(!dialog.open)dialog.showModal();$('#compare-search')?.focus();
}

function clubArenaValues(){const seen=new Map();for(const r of a.records){const value=String(r.club||'').trim(),key=value.toLocaleLowerCase('sv');if(value&&!seen.has(key))seen.set(key,value);}return [...seen.values()].sort((x,y)=>x.localeCompare(y,'sv'));}
function renderClubArenaSuggestions(q){
 const root=$('#club-arena-suggestions'),input=$('#club-arena-search');if(!root||!input)return;q=q.trim();clubArenaSuggestionIndex=-1;if(!q){root.hidden=true;root.innerHTML='';input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');return;}
 const selectedKeys=new Set((state.clubNames||[]).map(v=>v.toLocaleLowerCase('sv'))),needle=q.toLocaleLowerCase('sv'),matches=clubArenaValues().filter(v=>v.toLocaleLowerCase('sv').includes(needle)&&!selectedKeys.has(v.toLocaleLowerCase('sv'))).slice(0,8);root.hidden=false;input.setAttribute('aria-expanded','true');root.innerHTML=(state.clubNames||[]).length>=4?'<p class="picker-empty">Max fyra klubbar eller orter kan jämföras. Ta bort ett val först.</p>':matches.length?matches.map((v,i)=>'<button id="club-arena-option-'+i+'" type="button" role="option" aria-selected="false" data-club-arena-add="'+esc(v)+'"><span><strong>'+esc(v)+'</strong><small>Publicerad klubb / ort i vald upplaga</small></span><b>Välj</b></button>').join(''):'<p class="picker-empty">Ingen klubb eller ort matchar.</p>';
}
function moveClubArenaSuggestion(direction){const input=$('#club-arena-search'),items=[...document.querySelectorAll('#club-arena-suggestions [data-club-arena-add]')];if(!items.length)return;clubArenaSuggestionIndex=(clubArenaSuggestionIndex+direction+items.length)%items.length;items.forEach((item,i)=>item.setAttribute('aria-selected',i===clubArenaSuggestionIndex));input.setAttribute('aria-activedescendant',items[clubArenaSuggestionIndex].id);items[clubArenaSuggestionIndex].scrollIntoView({block:'nearest'});}
function refreshAgeSection(){
 const root=$('#age-analysis');if(!root)return;const team=a.race.participant.entity==='team';root.innerHTML=flowHeading(team?'OFFICIELLA KLASSER':'KLASS & ÅLDER',team?'Klassanalys':'Ålderslabbet',team?'Jämför deltagande, målgång, fart och pacing mellan källans publicerade lagklasser.':'Analytiska åldersgrupper – inte officiella tävlingsklasser. Grupper med för litet underlag döljs.')+views.ageAnalysis(a,selected(),state);
}
function refreshClubSection(){
 const root=$('#clubs');if(!root)return;root.innerHTML=flowHeading('KLUBB- OCH ORTSARENAN','Gemenskap i siffror','Sök en klubb eller välj upp till fyra för att jämföra deltagare, målgång och fart i det valda loppet.')+views.clubs(a,selected(),state);
}
function refreshSegmentSection(){
 const root=$('#segments');if(!root)return;root.innerHTML=flowHeading('DELSTRÄCKELABBET','Var avgjordes loppet?','Jämför segment, relativa prestationer och placeringar utan att fabricera saknade passager.')+views.segments(a,selected(),state)+views.course(a);
}
async function refreshHistorySection(){
 const root=$('#history');if(!root)return;root.innerHTML=flowHeading('HISTORIK','År för år','Deltagande visas brett; prestation jämförs endast när banunderlaget uttryckligen tillåter det.')+empty('Laddar liten historiksammanställning…');try{const d=await loader.history();if(root.isConnected)root.innerHTML=flowHeading('HISTORIK','År för år','Deltagande visas brett; prestation jämförs endast när banunderlaget uttryckligen tillåter det.')+views.historyView(a,d,boot,state);}catch(e){if(root.isConnected)root.innerHTML=flowHeading('HISTORIK','År för år','Deltagande visas brett; prestation jämförs endast när banunderlaget uttryckligen tillåter det.')+empty(e.message);}
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
 try{
  const [route,module]=await Promise.all([loader.route(a.race),import('./map-engine.js')]);
  if(token!==generation||!root.isConnected||(kind==='profile'&&!$('#profile').open)||(kind==='duel'&&!$('#duel').open))return;
  const record=kind==='profile'?records[0]:null,referenceSeries=record?buildReplayReferences(record,route):[],insights=record?replayInsights(record):[];
  const mounted=await module.mountMap(root,{route,adapter:a,records,segment:state.segment,referenceSeries,insights,profile:kind==='profile',musicSrc:'assets/kustlinjens-steg.mp3'});
  if(token!==generation||!root.isConnected||(kind==='profile'&&!$('#profile').open)||(kind==='duel'&&!$('#duel').open)){mounted.destroy();return;}
  if(kind==='profile')profileMap=mounted;else if(kind==='duel')duelMap=mounted;else mapView=mounted;
 }catch(e){if(root.isConnected)root.innerHTML=empty(e.message);}
}
async function openProfile(id,update=true){
 const r=a.byId.get(String(id));if(!r)return;profileMap?.destroy();profileMap=null;profileTrigger=document.activeElement;state.profile=String(id);
 $('#profile-body').innerHTML=views.profile(a,r,state,isFavorite(r));if(!$('#profile').open)$('#profile').showModal();if(update)syncURL();
 if(a.race.capabilities.replay&&$('#profile-replay'))await showMap($('#profile-replay'),[r],'profile');
}
async function navigate(section,update=true,{behavior='smooth',focus=true}={}){if(section==='compare'){openCompareDialog();return;}section=normalizeSection(section);const previous=state.section;state.section=section;if(isFlowSection(section)){if(!isFlowSection(previous)||!document.getElementById(section))await render();else updateNav();if(update)syncURL();scrollToSection(section,{focus,behavior});return;}await render();if(update)syncURL();$('#analysis').scrollIntoView({block:'start',behavior:motionBehavior(behavior)});}
document.addEventListener('click',async e=>{
 const b=e.target.closest('button,a');if(!b||!state)return;
 if(b.dataset.family){const family=b.dataset.family,editions=Object.values(boot.race_catalog).filter(r=>r.race_family===family),race=editions.find(r=>r.year===a.race.year)||editions.sort((x,y)=>y.year-x.year)[0];await loadRace(race.race_key);$('#analysis').scrollIntoView();return;}
 if(b.dataset.clubSuggestion){chooseClub(b.dataset.clubSuggestion);return;}
 if(b.dataset.clubArenaAdd){state.clubNames=[...(state.clubNames||[]),b.dataset.clubArenaAdd].slice(0,4);refreshClubSection();return;}
 if(b.dataset.clubRemove){state.clubNames=(state.clubNames||[]).filter(name=>name!==b.dataset.clubRemove);refreshClubSection();return;}
 if(b.dataset.ageGroup){const id=b.dataset.ageGroup,current=new Set(state.ageGroups||[]);if(current.has(id)){if(current.size>1)current.delete(id);}else if(current.size<5)current.add(id);state.ageGroups=[...current];refreshAgeSection();return;}
 if(b.dataset.ageHeatStat){state.ageHeatStat=b.dataset.ageHeatStat==='fastest10'?'fastest10':'median';refreshAgeSection();return;}
 if(b.dataset.standoutTab){state.standoutTab=b.dataset.standoutTab;refreshSegmentSection();return;}
 if(b.dataset.profileJump){document.getElementById(b.dataset.profileJump)?.scrollIntoView({behavior:motionBehavior('smooth'),block:'start'});return;}
 if(b.dataset.lookupResult){chooseLookup(b.dataset.lookupResult);return;}
 if(b.id==='focus-runner-search'){const input=$('#lookup');input?.focus();input?.scrollIntoView({block:'center',behavior:motionBehavior('smooth')});return;}
 if(b.id==='open-compare-dialog'){openCompareDialog();return;}
 if(b.dataset.scrollTarget){e.preventDefault();document.getElementById(b.dataset.scrollTarget)?.scrollIntoView({behavior:motionBehavior('smooth'),block:'start'});return;}
 if(b.dataset.section){e.preventDefault();await navigate(b.dataset.section);return;}
 if(b.dataset.duelAdd){const id=b.dataset.duelAdd;if(!state.compare.includes(id)&&state.compare.length<compareLimit())state.compare.push(id);duelOptions('');if($('#duel-search'))$('#duel-search').value='';renderTopTools();syncURL();return;}
 if(b.dataset.duelRemove){state.compare=state.compare.filter(id=>id!==b.dataset.duelRemove);renderTopTools();syncURL();return;}
 if(b.id==='open-head-to-head'&&state.compare.length===2){openCompareDialog();return;}
 if(b.id==='head-to-head-duel'&&state.compare.length===2&&a.race.capabilities.replay){const dialog=$('#duel');dialog.showModal();await showMap($('#duel-body'),state.compare.map(id=>a.byId.get(id)).filter(Boolean),'duel');return;}
 if(b.dataset.headSegment!==undefined){const index=Number(b.dataset.headSegment)||0;document.querySelectorAll('#compare-dialog [data-head-segment]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));headToHeadCourse?.selectSegment(index);return;}
 if(b.id==='open-map-duel'){const dialog=$('#duel');dialog.showModal();await showMap($('#duel-body'),state.compare.map(id=>a.byId.get(id)).filter(Boolean),'duel');return;}
 if(b.dataset.info){const t=document.getElementById(b.dataset.info);t.hidden=!t.hidden;b.setAttribute('aria-expanded',!t.hidden);return;}
 if(b.dataset.segment){const keepCourse=Boolean(mapView&&$('#course-map')?.querySelector('.map'));state.segment=+b.dataset.segment;mapView?.select(state.segment);document.querySelectorAll('button[data-segment]').forEach(x=>x.setAttribute('aria-pressed',+x.dataset.segment===state.segment));if(isFlowSection(state.section)){await render();if(keepCourse&&$('#load-course'))await showMap($('#course-map'),[],'course');}return;}
 if(b.dataset.sort){state.dir=state.sort===b.dataset.sort?-(state.dir||1):1;state.sort=b.dataset.sort;resultTable();return;}
 if(b.dataset.addCompare){const id=b.dataset.addCompare,limit=compareLimit(),openAfter=b.dataset.openCompareAfter==='true'||Boolean(b.closest('#profile'));if(!state.compare.includes(id)&&state.compare.length<limit)state.compare.push(id);else if(!state.compare.includes(id)){status(limit===5?'Max fem resultat kan väljas till Kartduell':'Direktjämförelse använder högst två resultat för den här upplagan');return;}status(state.compare.length+' resultat valda för jämförelse');if(openAfter){if($('#profile')?.open)$('#profile').close();openCompareDialog();}else if($('#compare-dialog')?.open){renderCompareDialog();requestAnimationFrame(()=>$('#compare-search')?.focus());}syncURL();return;}
 if(b.dataset.removeCompare){state.compare=state.compare.filter(id=>id!==b.dataset.removeCompare);if($('#compare-dialog')?.open)renderCompareDialog();else await render();syncURL();return;}
 if(b.dataset.clearCompare!==undefined){state.compare=[];if($('#compare-dialog')?.open){renderCompareDialog();requestAnimationFrame(()=>$('#compare-search')?.focus());}else await render();syncURL();return;}
 if(b.dataset.quickFilter){state.globalQuery=null;state.filters[b.dataset.quickFilter]=b.dataset.quickValue||'';const input=document.querySelector('[data-filter="'+b.dataset.quickFilter+'"]');if(input)input.value=b.dataset.quickValue||'';await render();return;}
 if(b.dataset.favorite){const r=a.byId.get(b.dataset.favorite);if(isFavorite(r))favorites=favorites.filter(f=>!(f.race===a.race.race_key&&f.id===b.dataset.favorite));else favorites.push({race:a.race.race_key,id:String(r.source_result_id),name:r.name,year:a.race.year});saveFavorites();b.textContent=isFavorite(r)?'Sparad':'Spara lopp';b.setAttribute('aria-pressed',isFavorite(r));renderTopTools();return;}
 if(b.dataset.openFavorite){await loadRace(b.dataset.openFavorite,{restore:{profile:b.dataset.id}});return;}
 if(b.id==='reset-filters'){state.filters={};filters();await render();}
 if(b.id==='prev-page'){state.page--;resultTable();}
 if(b.id==='next-page'){state.page++;resultTable();}
 if(b.id==='load-course')await showMap($('#course-map'),[],'course');
 if(b.id==='open-duel'){const dialog=$('#duel');dialog.showModal();await showMap($('#duel-body'),state.compare.map(id=>a.byId.get(id)),'duel');}
 if(b.id==='close-profile')$('#profile').close();
 if(b.id==='close-compare-dialog')$('#compare-dialog').close();
 if(b.id==='close-duel')$('#duel').close();
});
document.addEventListener('click',e=>{const row=e.target.closest('[data-result]');if(row)openProfile(row.dataset.result);});
document.addEventListener('change',e=>{const input=e.target.closest('[data-series-toggle]');if(!input)return;const key=input.dataset.seriesToggle,chart=input.closest('.interactive-chart');chart?.querySelectorAll('[data-series="'+key+'"]').forEach(item=>{item.hidden=!input.checked;if(item.namespaceURI==='http://www.w3.org/2000/svg')item.style.display=input.checked?'':'none';});});
document.addEventListener('change',e=>{if(!state)return;if(e.target.id==='segment-from'){state.segmentFrom=e.target.value;const keys=a.boundary.map(cp=>cp.key),from=keys.indexOf(state.segmentFrom),to=keys.indexOf(state.segmentTo);if(to<=from)state.segmentTo=keys[Math.min(keys.length-1,from+1)];refreshSegmentSection();}else if(e.target.id==='segment-to'){state.segmentTo=e.target.value;const keys=a.boundary.map(cp=>cp.key),from=keys.indexOf(state.segmentFrom),to=keys.indexOf(state.segmentTo);if(to<=from)state.segmentFrom=keys[Math.max(0,to-1)];refreshSegmentSection();}else if(e.target.id==='segment-metric'){state.segmentMetric=e.target.value;refreshSegmentSection();}else if(e.target.id==='history-reference'){state.historyReference=e.target.value;state.historySegment=null;refreshHistorySection();}else if(e.target.id==='history-segment'){state.historySegment=e.target.value;refreshHistorySection();}});
document.addEventListener('keydown',e=>{
 if(e.target.id==='lookup'&&['ArrowDown','ArrowUp','Enter','Escape'].includes(e.key)){if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();moveLookupSuggestion(e.key==='ArrowDown'?1:-1);}else if(e.key==='Enter'&&lookupSuggestionIndex>=0){e.preventDefault();const item=document.querySelectorAll('#lookup-suggestions [data-lookup-result]')[lookupSuggestionIndex];if(item)chooseLookup(item.dataset.lookupResult);}else if(e.key==='Escape')lookupOptions('');return;}
 if(e.target.id==='duel-search'&&['ArrowDown','ArrowUp','Enter','Escape'].includes(e.key)){if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();moveDuelSuggestion(e.key==='ArrowDown'?1:-1);}else if(e.key==='Enter'&&duelSuggestionIndex>=0){e.preventDefault();document.querySelectorAll('#duel-suggestions [data-duel-add]')[duelSuggestionIndex]?.click();}else if(e.key==='Escape')duelOptions('');return;}
 if(e.target.id==='club-arena-search'&&['ArrowDown','ArrowUp','Enter','Escape'].includes(e.key)){if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();moveClubArenaSuggestion(e.key==='ArrowDown'?1:-1);}else if(e.key==='Enter'&&clubArenaSuggestionIndex>=0){e.preventDefault();document.querySelectorAll('#club-arena-suggestions [data-club-arena-add]')[clubArenaSuggestionIndex]?.click();}else if(e.key==='Escape')renderClubArenaSuggestions('');return;}
  if(e.target.id==='compare-search'&&['ArrowDown','ArrowUp','Enter','Escape'].includes(e.key)){if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();moveCompareSuggestion(e.key==='ArrowDown'?1:-1);}else if(e.key==='Enter'&&compareSuggestionIndex>=0){e.preventDefault();document.querySelectorAll('#compare-options [data-add-compare]')[compareSuggestionIndex]?.click();}else if(e.key==='Escape')compareOptions('');return;}
 if(e.target.id==='club-filter'&&['ArrowDown','ArrowUp','Enter','Escape'].includes(e.key)){if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();moveClubSuggestion(e.key==='ArrowDown'?1:-1);}else if(e.key==='Enter'&&clubSuggestionIndex>=0){e.preventDefault();const item=document.querySelectorAll('#club-suggestions [data-club-suggestion]')[clubSuggestionIndex];if(item)chooseClub(item.dataset.clubSuggestion);}else if(e.key==='Escape')renderClubSuggestions('');return;}
 if(e.key==='Escape'){document.querySelectorAll('[data-info][aria-expanded=true]').forEach(b=>{document.getElementById(b.dataset.info).hidden=true;b.setAttribute('aria-expanded','false');});}
 if(e.key==='Enter'||e.key===' '){const row=e.target.closest('[data-result]');if(row){e.preventDefault();openProfile(row.dataset.result);}const hit=e.target.closest('svg [data-segment]');if(hit){e.preventDefault();state.segment=+hit.dataset.segment;render();}}
});
document.addEventListener('input',e=>{
 if(!state)return;if(e.target.dataset.filter){state.globalQuery=null;state.filters[e.target.dataset.filter]=e.target.value;state.page=1;render();if(e.target.id==='club-filter')renderClubSuggestions(e.target.value);}
 if(e.target.id==='lookup'){lookupOptions(e.target.value);}
 if(e.target.id==='duel-search'){duelOptions(e.target.value);}
 if(e.target.id==='club-arena-search'){renderClubArenaSuggestions(e.target.value);}
 if(e.target.id==='target-time'){const values=selected().filter(finished).map(r=>Number(r.finish_seconds)).sort((x,y)=>x-y);updateTargetSimulator(values,Number(e.target.value));}
 if(e.target.id==='table-search'){state.query=e.target.value;state.page=1;resultTable();}
 if(e.target.id==='compare-search')compareOptions(e.target.value);
 if(e.target.id==='goal-hours'||e.target.id==='goal-minutes')renderPlanOutput();
});
document.addEventListener('click',e=>{if(!e.target.closest('#global-search'))lookupOptions('');if(!e.target.closest('#map-duel-panel'))duelOptions('');if(!e.target.closest('.club-arena'))renderClubArenaSuggestions('');if(!e.target.closest('.filter-autocomplete'))renderClubSuggestions('');if(!e.target.closest('.compare-search-wrap')){const root=$('#compare-options');if(root){root.hidden=true;$('#compare-search')?.setAttribute('aria-expanded','false');}}});
$('#year').onchange=()=>{const r=Object.values(boot.race_catalog).find(r=>r.race_family===a.race.race_family&&r.year===+$('#year').value);if(r)loadRace(r.race_key);};
$('#unit').onchange=()=>{state.unit=$('#unit').value;store.write('unit',state.unit);render();if(state.profile)openProfile(state.profile,false);};
$('#global-search').onsubmit=async e=>{e.preventDefault();if(!a)return;const q=$('#lookup').value.trim(),matches=a.records.filter(r=>resultMatches(r,q));if(lookupSuggestionIndex>=0){const item=document.querySelectorAll('#lookup-suggestions [data-lookup-result]')[lookupSuggestionIndex];if(item){chooseLookup(item.dataset.lookupResult);return;}}if(matches.length===1)chooseLookup(matches[0].source_result_id);else{lookupOptions('');state.query=q;state.globalQuery=q;state.page=1;await navigate('results');$('#analysis').scrollIntoView();}};
$('#profile').addEventListener('close',()=>{profileMap?.destroy();profileMap=null;if(state?.profile){state.profile=null;syncURL(true);}profileTrigger?.focus?.();});
$('#compare-dialog').addEventListener('close',()=>{headToHeadCourse?.destroy();headToHeadCourse=null;const root=$('#compare-dialog-body');if(root)root.innerHTML='';compareTrigger?.focus?.();compareTrigger=null;});
$('#duel').addEventListener('close',()=>{duelMap?.destroy();duelMap=null;});
addEventListener('popstate',async()=>{if(!boot)return;const restored=urlState(location.href,boot.race_catalog,boot.default_race),openCompare=restored.section==='compare';if(openCompare)restored.section='overview';if(restored.raceKey!==state.raceKey)await loadRace(restored.raceKey,{restore:restored,replace:true});else{Object.assign(state,restored);state.section=normalizeSection(state.section);await render();if(isFlowSection(state.section))scrollToSection(state.section,{focus:true,behavior:'auto'});if(restored.profile)openProfile(restored.profile,false);else $('#profile').close();}if(openCompare)openCompareDialog();});
async function start(){
 try{history.scrollRestoration='manual';const params=new URLSearchParams(location.search),explicitSection=Boolean(location.hash||params.has('section')),openCompare=location.hash==='#compare'||params.get('section')==='compare';if(!explicitSection)window.scrollTo(0,0);boot=await loader.bootstrap();store=storage(boot.event.storage_namespace,safeStorage());const saved=store.read('favorites',[]);favorites=Array.isArray(saved)?saved.filter(f=>f&&typeof f.id==='string'&&boot.race_catalog[f.race]).slice(-40):[];const unit=store.read('unit','pace');state={...urlState(location.href,boot.race_catalog,boot.default_race),unit:unit==='speed'?'speed':'pace',filters:{},segment:0,page:1};if(openCompare)state.section='overview';await loadRace(state.raceKey,{restore:{...state},replace:true,scroll:explicitSection&&!openCompare});if(!explicitSection)window.scrollTo(0,0);if(openCompare)openCompareDialog();}
 catch(e){$('#view').innerHTML=empty(e.message);status('Katalogen kunde inte laddas. Ladda om sidan för att försöka igen.');}
}
start();


function renderPlan(root=$('#view')){
 if(!a.race.capabilities.goal_pace)return;
 const target=boot.presentation[a.race.race_family].default_goal_seconds,h=Math.floor(target/3600),m=Math.floor(target%3600/60);
 root.insertAdjacentHTML('beforeend','<section class="card"><div class="card-heading"><div><h3>Måltempo & loppplan</h3><p>En historisk referens, inte en individuell prognos.</p></div>'+info('plan-method','Måltiden fördelas på publicerade kompletta passager i vald upplaga när sådant underlag finns. Resultatet är en planeringsreferens, inte en individuell prognos.')+'</div><div class="toolbar"><label>Timmar<input id="goal-hours" type="number" min="0" max="48" value="'+h+'"></label><label>Minuter<input id="goal-minutes" type="number" min="0" max="59" value="'+m+'"></label></div><div id="plan-output"></div></section>');
 renderPlanOutput();
}
function renderPlanOutput(){
 const h=Number($('#goal-hours')?.value),m=Number($('#goal-minutes')?.value),target=h*3600+m*60,root=$('#plan-output');if(!root)return;
 if(h<0||h>48||m<0||m>59||target<=0){root.innerHTML=empty('Ange en positiv måltid och minuter mellan 0 och 59.');return;}
 const p=plan(a,target);
 root.innerHTML='<p>Måltempo: <strong>'+pace(p.pace,state.unit)+'</strong> · nominell distans</p>'+(p.segments.length?table(['Till kontroll','Delsträcketid'],p.segments.map(s=>tr([esc(s.name),time(s.seconds)]))):'')+'<p class="muted">'+(p.method==='observed'?'Kalibrerat på kompletta publicerade passager i just denna upplaga, n='+p.n+'. Medianandelar av varje deltagares sluttid normaliseras till måltiden. Fältfiltren påverkar inte referensen.':p.method==='distance'?'Distansfallback: fördelat enbart på explicita rapporterade segmentdistanser. Saknad distans lämnas oallokerad.':'Enkel beräkning från måltid och nominell distans. Inget segmentunderlag finns.')+'</p>';
}
