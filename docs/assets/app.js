import {DataLoader} from './data-loader.js';
import {adapt} from './data-adapter.js';
import {urlState,stateURL,switched,storage,sections,flowSections} from './app-state.js';
import {filterRows,finite,finished,median} from './analytics.js';
import {esc,time,empty,statusLabel,info,elevation} from './charts.js';
import * as views from './views.js';
import {plan} from './race-plan.js';
import {pace,table,tr} from './charts.js';
const $=s=>document.querySelector(s),loader=new DataLoader(),labels={overview:'Översikt',statistics:'Statistik',gender:'Genusperspektiv','age-analysis':'Klass & ålder',segments:'Delsträckor',history:'Historik',clubs:'Klubb & ort',method:'Metod',results:'Resultat',compare:'Jämför'};
let boot,a,state,store,favorites=[],generation=0,renderVersion=0,mapView=null,profileMap=null,duelMap=null,headToHeadCourse=null,courseDifficultyMap=null,profileTrigger=null,compareTrigger=null,clubSuggestionIndex=-1,lookupSuggestionIndex=-1,compareSuggestionIndex=-1,duelSuggestionIndex=-1,clubArenaSuggestionIndex=-1,sectionObserver=null;
function safeStorage(){try{return localStorage;}catch{return null;}}
function status(text){$('#load-status').textContent=text;}
function syncURL(replace=false){history[replace?'replaceState':'pushState'](null,'',stateURL(location.href,state));}
function closeMaps(){mapView?.destroy();mapView=null;profileMap?.destroy();profileMap=null;duelMap?.destroy();duelMap=null;headToHeadCourse?.destroy();headToHeadCourse=null;courseDifficultyMap?.destroy();courseDifficultyMap=null;}
function saveFavorites(){store.write('favorites',favorites.slice(-40));}
function isFavorite(r){return favorites.some(f=>f.race===a.race.race_key&&f.id===String(r.source_result_id));}
async function loadRace(key,{restore=null,replace=false,scroll=true,preserveScroll=false}={}){
 const preservedY=preserveScroll?window.scrollY:null,token=++generation;closeMaps();$('#profile').close();if($('#compare-dialog')?.open)$('#compare-dialog').close();$('#duel').close();state=switched(state,key);if(restore)Object.assign(state,restore);
 $('#view').setAttribute('aria-busy','true');$('#view').innerHTML=empty('Laddar vald upplaga…');status('Katalog klar → laddar valt lopp/år');$('#year').disabled=true;
 try{const doc=await loader.race(key);if(token!==generation)return;a=adapt(doc,boot);state.compare=state.compare.filter(id=>a.byId.has(id)).slice(0,a.race.capabilities.replay?5:2);state.section=normalizeSection(state.section);filters();controls();await render();syncURL(replace);status('Katalog → vald upplaga klar · '+a.records.length+' resultat · historik i analysflödet · rutt/replay efter behov');if(preserveScroll&&finite(preservedY)){window.scrollTo(0,preservedY);requestAnimationFrame(()=>window.scrollTo(0,preservedY));}else if(scroll&&isFlowSection(state.section))scrollToSection(state.section,{focus:state.section!=='overview',behavior:'auto'});if(state.profile)openProfile(state.profile,false);}
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
 const nav=[['runner-lookup','Löpare'],['map-duel-panel','Karta & Kartduell'],['goal-pace','Måltempo'],...availableSections().filter(key=>key!=='method').map(key=>[key,labels[key]])];
 $('#analysis-nav').innerHTML='<div class="analysis-nav__scroll">'+nav.map(([key,label])=>{const overview=key==='overview',tool=key==='runner-lookup'||key==='map-duel-panel'||key==='goal-pace',target=overview?'overview-context':key;return '<button '+(tool||overview?'data-scroll-target="'+target+'"':'data-section="'+key+'"')+(overview?' data-set-section="overview"':'')+' class="'+(isFlowSection(key)?'anchor-nav':'special-nav')+'" '+(state.section===key?'aria-current="location"':'')+'>'+label+'</button>';}).join('')+'</div><button class="share-view" id="share-view" type="button" aria-label="Dela aktuell vy">Dela</button>';
 const team=a.race.participant.entity==='team';$('#lookup-title').textContent=team?'Analysera ett lags lopp':'Analysera en löpares lopp';$('#lookup-copy').textContent=team?'Sök på lagnamn eller startnummer och öppna en komplett lagprofil med passager, placering, tempo, jämförelser och Replay när underlaget medger det.':'Sök på namn eller startnummer och öppna en komplett profil med mellantider, placering, tempo, jämförelser och Replay.';$('#favorites-title').textContent=team?'Sparade lag':'Sparade löpare';$('#duel-copy').textContent=a.race.capabilities.replay?(team?'Kartduell jämför två till fem lag på banan. För analys av ett enda lag använder du deltagaranalysen och Replay.':'Kartduell jämför två till fem deltagare på banan. För analys av en enda deltagare använder du deltagaranalysen och Replay.'):'Den här upplagan saknar källstöd för Replay. Välj exakt två resultat för Direktjämförelse.';
 $('#unit').value=state.unit;
 renderTopTools();
 renderGoalPace();
}
function filters(){
 const options=(key,label)=>'<label>'+label+'<select data-filter="'+key+'"><option value="">Alla</option>'+[...new Set(a.records.map(r=>r[key]).filter(Boolean))].sort((x,y)=>String(x).localeCompare(String(y),'sv',{numeric:true})).map(v=>'<option value="'+esc(v)+'">'+esc(v)+'</option>').join('')+'</select></label>';
 const club=a.race.capabilities.club_analysis?'<div class="filter-autocomplete"><label>Klubb & ort<input id="club-filter" data-filter="club" type="search" autocomplete="off" role="combobox" aria-autocomplete="list" aria-controls="club-suggestions" aria-expanded="false" placeholder="Börja skriva klubb eller ort"></label><div id="club-suggestions" class="suggestions" role="listbox" hidden></div></div>':'';
 const statusOrder=['FINISHED','DNF','DNS','DSQ','UNKNOWN'],present=new Set(a.records.map(r=>r.status).filter(Boolean)),statuses=statusOrder.filter(v=>present.has(v)),statusFilter='<label>Status<select data-filter="status"><option value="">Alla</option>'+statuses.map(v=>'<option value="'+esc(v)+'">'+esc(statusLabel(v))+'</option>').join('')+'</select></label>';
 $('#filters').innerHTML=(a.race.capabilities.sex_filter&&a.race.participant.entity==='person'?'<label>Kön<select data-filter="sex"><option value="">Alla</option><option value="F">Kvinnor</option><option value="M">Män</option></select></label>':'')+options('class_name',a.race.participant.entity==='team'?'Lagklass':'Klass')+club+statusFilter+'<label>Fartenhet<select id="unit"><option value="pace">min/km</option><option value="speed">km/h</option></select></label><button id="reset-filters">Återställ</button>';
}
function selected(){return filterRows(a.records,state.filters);}
function compareLimit(){return a?.race?.capabilities?.replay?5:2;}
function filterSummary(){
 const names={sex:'Kön',class_name:a.race.participant.entity==='team'?'Lagklass':'Klass',status:'Status',club:'Klubb / ort'},value=(key,v)=>key==='sex'?(v==='F'?'Kvinnor':v==='M'?'Män':v):key==='status'?statusLabel(v):v;
 const active=Object.entries(state.filters).filter(([,v])=>v);return active.map(([key,v])=>(names[key]||key)+': '+value(key,v)).join(' · ')||'Inga fältfilter';
}
function availableFlowSections(){return flowSections.filter(key=>key!=='segments'||a.race.capabilities.segment_analysis).filter(key=>key!=='gender'||a.race.participant.entity==='person'||a.race.participant.entity==='team').filter(key=>key!=='age-analysis'||a.race.capabilities.age_analysis||a.race.participant.entity==='team').filter(key=>key!=='clubs'||a.race.capabilities.club_analysis);}
function availableSections(){return availableFlowSections();}
function isFlowSection(section){return flowSections.includes(section);}
function normalizeSection(section){return availableSections().includes(section)?section:'overview';}
function updateNav(){document.querySelectorAll('#analysis-nav button').forEach(b=>{const section=b.dataset.section||b.dataset.setSection;if(section===state.section)b.setAttribute('aria-current','location');else b.removeAttribute('aria-current');});}
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
 if(available.includes('segments'))parts.push(flowSection('segments',flowHeading('DELSTRÄCKELABBET','Var avgjordes loppet?','Jämför segment, relativa prestationer och placeringar utan att fabricera saknade passager.')+views.courseDifficulty(a,rows,state)+views.segments(a,rows,state)));
 if(available.includes('history'))parts.push(flowSection('history',flowHeading('HISTORIK','År för år','Deltagande visas brett; prestation jämförs endast när banunderlaget uttryckligen tillåter det.')+empty('Laddar liten historiksammanställning…')));
 if(available.includes('clubs'))parts.push(flowSection('clubs',flowHeading('KLUBB- OCH ORTSARENAN','Gemenskap i siffror','Sök en klubb eller välj upp till fyra för att jämföra deltagare, målgång och fart i det valda loppet.')+views.clubs(a,rows,state)));
 if(available.includes('results'))parts.push(flowSection('results',resultsShell()));
 if(available.includes('method'))parts.push(flowSection('method','<section class="data-note panel"><p>'+esc(dataPrinciple())+'</p><details><summary>Metod och dataprinciper</summary>'+views.methodology(a,boot,state,rows)+'</details></section>'));
 v.innerHTML='<div class="long-analysis">'+parts.join('')+'</div>';observeFlowSections();renderTargetSimulator(rows);if(available.includes('statistics'))bindScatterZoom($('#statistics'));if(available.includes('results'))resultTable();if(available.includes('overview'))loadOverviewElevation(token);if(available.includes('segments'))hydrateCourseDifficulty(token);
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
 const head=$('#open-head-to-head'),map=$('#open-map-duel'),entity=a.race.participant.entity==='team'?'lag':'deltagare';if(head){head.disabled=picked.length!==2;head.textContent=picked.length===2?'Öppna Direktjämförelse':'Välj två '+entity;}if(map){map.hidden=!a.race.capabilities.replay;map.disabled=picked.length<2||picked.length>5;map.textContent=picked.length>=2?'Öppna Kartduell':'Välj minst två '+entity;}
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
 root.innerHTML='<div class="goal-pace-controls"><div><label for="goal-hours">Timmar</label><input id="goal-hours" type="number" inputmode="numeric" min="0" max="48" value="'+h+'"></div><div><label for="goal-minutes">Minuter</label><input id="goal-minutes" type="number" inputmode="numeric" min="0" max="59" value="'+m+'"></div><button type="button" class="primary" id="goal-create">Skapa loppplan</button>'+info('plan-method','Måltiden fördelas på publicerade kompletta passager i vald upplaga när sådant underlag finns. Om sådan viktning saknas används endast explicit rapporterad segmentdistans. Summan stäms av mot vald måltid och är en planeringsreferens, inte en individuell prognos.')+'</div><p class="goal-pace-distance">Måltiden gäller <strong>'+esc(a.race.section||boot.presentation[a.race.race_family].label)+'</strong> · '+Number(a.race.nominal_distance_km).toFixed(1).replace('.',',')+' km nominell distans.</p><div id="plan-output" aria-live="polite"></div>';renderPlanOutput();
}

function renderProfilePlanOutput(){
 const hours=$('#profile-goal-hours')?.value,minutes=$('#profile-goal-minutes')?.value,h=Number(hours),m=Number(minutes),root=$('#profile-plan-output');if(!root)return;
 if(hours===''||minutes===''||!Number.isInteger(h)||!Number.isInteger(m)||h<0||h>48||m<0||m>59){root.innerHTML='<div class="goal-pace-error" role="alert">Ange hela, giltiga timmar och minuter.</div>';return;}
 const target=h*3600+m*60;if(target<=0){root.innerHTML='<div class="goal-pace-error" role="alert">Ange en positiv måltid.</div>';return;}
 const p=plan(a,target);if(!p){root.innerHTML='<div class="goal-pace-error" role="alert">Loppplanen kunde inte beräknas.</div>';return;}
 const method=p.method==='observed'?'Bananpassad':p.method==='distance'?'Distansbaserad':'Jämnt snitt';
 const rows=p.segments.length?p.segments.map(s=>tr([esc(s.name),finite(s.distanceKm)?Number(s.distanceKm).toFixed(1).replace('.',',')+' km':'–',time(s.seconds),time(s.cumulativeSeconds),pace(s.paceSecondsKm,state.unit)])):[];
 root.innerHTML='<div class="profile-plan-summary"><span><small>Måltid</small><strong>'+time(target)+'</strong></span><span><small>Snittfart</small><strong>'+pace(p.pace,state.unit)+'</strong></span><span><small>Metod</small><strong>'+method+'</strong></span></div>'+(rows.length?table(['Delsträcka','Distans','Segmenttid','Passage','Tempo'],rows):'<p class="muted">Det här loppet saknar segmentunderlag för en detaljerad plan.</p>');
}
function toggleProfilePlan(id){
 const root=document.querySelector('[data-profile-plan-panel]'),button=document.querySelector('[data-profile-plan="'+CSS.escape(String(id))+'"]'),r=a.byId.get(String(id));if(!root||!r)return;
 const opening=root.hidden;if(opening&&!root.dataset.ready){const target=finished(r)?Number(r.finish_seconds):Number(boot.presentation[a.race.race_family].default_goal_seconds),h=Math.floor(target/3600),m=Math.floor(target%3600/60);root.innerHTML='<div class="profile-inline-tool-head"><div><p class="eyebrow">MÅLTEMPO I PROFILEN</p><h3>Planera utan att lämna Replay</h3><p>Utgå från en måltid och se en bananpassad plan direkt här.</p></div><button type="button" class="secondary" data-profile-plan-close>Stäng</button></div><div class="profile-plan-controls"><label>Timmar<input id="profile-goal-hours" type="number" min="0" max="48" value="'+h+'"></label><label>Minuter<input id="profile-goal-minutes" type="number" min="0" max="59" value="'+m+'"></label></div><div id="profile-plan-output" aria-live="polite"></div>';root.dataset.ready='true';renderProfilePlanOutput();}
 root.hidden=!opening;if(button)button.setAttribute('aria-expanded',String(opening));
}

function resultMatches(r,q){return (r.name+' '+r.bib+' '+(r.club||'')).toLocaleLowerCase('sv').includes(q.toLocaleLowerCase('sv'));}
function lookupOptions(query){const root=$('#lookup-suggestions'),input=$('#lookup');if(!root||!input)return;const q=query.trim();lookupSuggestionIndex=-1;if(!q){root.hidden=true;root.innerHTML='';input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant');return;}const needle=q.toLocaleLowerCase('sv'),matches=a.records.filter(r=>resultMatches(r,q)).sort((x,y)=>{const rank=r=>String(r.name).toLocaleLowerCase('sv').startsWith(needle)?0:String(r.bib)===q?1:2;return rank(x)-rank(y)||String(x.name).localeCompare(String(y.name),'sv');}).slice(0,8);root.hidden=false;input.setAttribute('aria-expanded','true');root.innerHTML=matches.length?matches.map((r,i)=>'<button id="lookup-option-'+i+'" type="button" role="option" aria-selected="false" data-lookup-result="'+esc(r.source_result_id)+'"><span><strong>'+esc(r.name)+'</strong><small>#'+esc(r.bib)+' · '+esc(r.class_name||'Klass saknas')+' · '+(finished(r)?time(r.finish_seconds):esc(statusLabel(r.status)))+'</small></span><b>Öppna profil</b></button>').join(''):'<p class="picker-empty">Inga löpare eller lag matchar i vald upplaga.</p>';}
function moveLookupSuggestion(direction){const input=$('#lookup'),items=[...document.querySelectorAll('#lookup-suggestions [data-lookup-result]')];if(!items.length)return;lookupSuggestionIndex=(lookupSuggestionIndex+direction+items.length)%items.length;items.forEach((item,i)=>item.setAttribute('aria-selected',i===lookupSuggestionIndex));input.setAttribute('aria-activedescendant',items[lookupSuggestionIndex].id);items[lookupSuggestionIndex].scrollIntoView({block:'nearest'});}
function chooseLookup(id){const input=$('#lookup');lookupOptions('');if(input)input.value='';openProfile(id);}

function dataPrinciple(){
 return 'Dataprincip: visar publicerade resultat och passager för vald upplaga. Saknade kön, åldrar, passager, lagroller och banor infereras inte. Historiska prestationsmått visas endast när whole-course-jämförbarhet är uttryckligen verifierad.';
}
function resultsShell(){
 return '<section class="panel results-panel"><div class="panel-head results-head"><div><p class="eyebrow ink">RESULTATDATABAS</p><h2>Sök, sortera och utforska</h2><p class="panel-copy">Öppna en rad för komplett loppanalys.</p></div><label class="result-search">Sök<input id="table-search" type="search" value="'+esc(state.query||'')+'" placeholder="Namn, nummer eller klubb"></label></div><div id="result-table"></div><div class="pagination"><span id="result-count"></span><div><button class="button secondary" id="prev-page">Föregående</button><span id="page-label"></span><button class="button secondary" id="next-page">Nästa</button></div></div></section>';
}
function resultTable(){
 const root=$('#result-table');if(!root)return;
 let rows=(state.globalQuery!==null?a.records:selected()).filter(r=>resultMatches(r,state.query||''));const key=state.sort||'overall_place',dir=state.dir||1;
 rows=rows.slice().sort((x,y)=>{const p=x[key],q=y[key];if(p==null)return q==null?0:1;if(q==null)return -1;return (typeof p==='number'&&typeof q==='number'?p-q:String(p).localeCompare(String(q),'sv',{numeric:true}))*dir;});
 const pages=Math.max(1,Math.ceil(rows.length/40));state.page=Math.min(Math.max(1,state.page),pages);const current=rows.slice((state.page-1)*40,state.page*40),team=a.race.participant.entity==='team';
 const heads=team?[['overall_place','Total'],['name',a.race.participant.singular||'Lag'],['class_name','Klass'],['class_place','Klassplats'],['finish_seconds','Tid'],['status','Status']]:[['overall_place','Plats'],['name','Namn'],['sex','Kön'],['class_name','Klass'],['club','Klubb'],['finish_seconds','Tid'],['status','Status']];
 const cell=(r,k)=>{if(k==='name')return '<div class="result-name-cell"><span><strong>'+esc(r.name)+'</strong><small>#'+esc(r.bib)+(finite(r.age)?' · '+esc(r.age)+' år':'')+'</small></span><button type="button" class="favorite-mini" data-favorite="'+esc(r.source_result_id)+'" aria-pressed="'+isFavorite(r)+'" aria-label="'+(isFavorite(r)?'Ta bort favorit':'Spara favorit')+'">★</button></div>';if(k==='finish_seconds')return finished(r)?time(r.finish_seconds):'–';if(k==='status')return '<span class="status '+esc(r.status)+'">'+esc(statusLabel(r.status))+'</span>';if(k==='sex')return r.sex==='F'?'Kvinna':r.sex==='M'?'Man':'–';if(k==='class_place')return finite(r.class_place)?'#'+esc(r.class_place):'–';return esc(r[k]??'–');};
 root.innerHTML='<div class="table-wrap"><table><thead><tr>'+heads.map(([k,label])=>'<th scope="col" aria-sort="'+(key===k?(dir===1?'ascending':'descending'):'none')+'"><button type="button" data-sort="'+k+'">'+esc(label)+(key===k?(dir===1?' ↑':' ↓'):'')+'</button></th>').join('')+'</tr></thead><tbody>'+current.map(r=>'<tr tabindex="0" data-result="'+esc(r.source_result_id)+'" aria-label="Öppna '+esc(r.name)+'">'+heads.map(([k])=>'<td>'+cell(r,k)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>'+(rows.length?'':empty('Inga resultat matchar filtren.'));
 $('#result-count').textContent=rows.length+' resultat';$('#page-label').textContent='Sida '+state.page+' av '+pages;$('#prev-page').disabled=state.page<=1;$('#next-page').disabled=state.page>=pages;
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
function bindScatterZoom(root=document){
 const container=root.querySelector?.('.zoomable-scatter'),svg=container?.querySelector('svg'),reset=container?.querySelector('[data-scatter-reset]');if(!svg||svg.dataset.zoomBound)return;svg.dataset.zoomBound='true';let start=null,selection=null;const bounds={left:Number(svg.dataset.dataLeft),top:Number(svg.dataset.dataTop),right:Number(svg.dataset.dataRight),bottom:Number(svg.dataset.dataBottom)};
 const point=event=>{const rect=svg.getBoundingClientRect(),view=svg.viewBox.baseVal,x=view.x+(event.clientX-rect.left)*view.width/(rect.width||1),y=view.y+(event.clientY-rect.top)*view.height/(rect.height||1);return{x:Math.max(bounds.left,Math.min(bounds.right,x)),y:Math.max(bounds.top,Math.min(bounds.bottom,y))}};
 svg.onpointerdown=event=>{if(event.target.closest?.('[data-result]'))return;start=point(event);selection=document.createElementNS('http://www.w3.org/2000/svg','rect');selection.setAttribute('class','scatter-zoom-selection');selection.setAttribute('x',start.x);selection.setAttribute('y',start.y);svg.append(selection);try{svg.setPointerCapture?.(event.pointerId);}catch{}};
 svg.onpointermove=event=>{if(!start||!selection)return;const current=point(event),x=Math.min(start.x,current.x),y=Math.min(start.y,current.y);selection.setAttribute('x',x);selection.setAttribute('y',y);selection.setAttribute('width',Math.abs(current.x-start.x));selection.setAttribute('height',Math.abs(current.y-start.y))};
 svg.onpointerup=event=>{if(!start||!selection)return;const current=point(event),x=Math.min(start.x,current.x),y=Math.min(start.y,current.y),width=Math.abs(current.x-start.x),height=Math.abs(current.y-start.y);selection.remove();selection=null;start=null;if(width>28&&height>24){svg.setAttribute('viewBox',x+' '+y+' '+width+' '+height);if(reset)reset.hidden=false}};
 if(reset)reset.onclick=()=>{svg.setAttribute('viewBox','0 0 740 280');reset.hidden=true};
}
function refreshStatisticsSection(){
 const root=$('#statistics');if(!root)return;root.innerHTML=flowHeading('STATISTIKVERKSTAD','Vad hände i loppet?','Fördjupa dig i placeringar, avhopp, fartmönster och vad en viss sluttid brukar räcka till.')+views.statistics(a,selected(),state);renderTargetSimulator(selected());bindScatterZoom(root);
}
function refreshAgeSection(){
 const root=$('#age-analysis');if(!root)return;const team=a.race.participant.entity==='team';root.innerHTML=flowHeading(team?'OFFICIELLA KLASSER':'KLASS & ÅLDER',team?'Klassanalys':'Ålderslabbet',team?'Jämför deltagande, målgång, fart och pacing mellan källans publicerade lagklasser.':'Analytiska åldersgrupper – inte officiella tävlingsklasser. Grupper med för litet underlag döljs.')+views.ageAnalysis(a,selected(),state);
}
function refreshClubSection(){
 const root=$('#clubs');if(!root)return;root.innerHTML=flowHeading('KLUBB- OCH ORTSARENAN','Gemenskap i siffror','Sök en klubb eller välj upp till fyra för att jämföra deltagare, målgång och fart i det valda loppet.')+views.clubs(a,selected(),state);
}
async function hydrateCourseDifficulty(token=renderVersion){
 const root=$('#course-difficulty'),mapRoot=root?.querySelector('[data-course-map-context]'),elev=root?.querySelector('[data-course-elevation-context]');if(!root||!mapRoot)return;courseDifficultyMap?.destroy();courseDifficultyMap=null;
 if(!a.course?.assets?.route){mapRoot.innerHTML=empty('Lokalt användbar rutt saknas för den här upplagan. Ingen annan upplagas bana lånas.');if(elev)elev.innerHTML=empty('Höjdprofil saknas för den här upplagan.');return;}
 try{
  const [route,module]=await Promise.all([loader.route(a.race),import('./map-engine.js')]);if(token!==renderVersion||!root.isConnected)return;
  courseDifficultyMap=await module.mountCourseContext(mapRoot,{route,adapter:a,segment:state.segment||0});if(token!==renderVersion||!root.isConnected){courseDifficultyMap?.destroy();courseDifficultyMap=null;return;}
  const boundary=a.boundary||[],maxIndex=Math.max(0,boundary.length-2),selected=Math.max(0,Math.min(maxIndex,Number(state.segment)||0)),range=i=>[route.anchors?.[boundary[i]?.key],route.anchors?.[boundary[i+1]?.key]],sliceMetrics=i=>module.terrainMetrics(route.elevation,range(i)),drawElevation=i=>{if(elev)elev.innerHTML=elevation(route.elevation,route.anchors,range(i));};
  drawElevation(selected);
  boundary.slice(1).forEach((_,i)=>{const m=sliceMetrics(i),from=range(i)[0],to=range(i)[1],km=finite(from)&&finite(to)?Math.max(.001,Number(to)-Number(from)):null,ascent=root.querySelector('[data-course-ascent="'+i+'"]'),descent=root.querySelector('[data-course-descent="'+i+'"]'),intensity=root.querySelector('[data-course-intensity="'+i+'"]');if(ascent)ascent.textContent=m?Math.round(m.ascent)+' m':'–';if(descent)descent.textContent=m?Math.round(m.descent)+' m':'–';if(intensity)intensity.textContent=m&&finite(km)?Math.round(m.ascent/km)+' m+/km':'–';});
  const enrichSelected=i=>{const summary=root.querySelector('[data-course-selected-summary]'),m=sliceMetrics(i),from=range(i)[0],to=range(i)[1],km=finite(from)&&finite(to)?Math.max(.001,Number(to)-Number(from)):null;if(summary&&m&&finite(km)){const existing=summary.textContent.split(' · median ')[1];summary.textContent=km.toFixed(1).replace('.',',')+' km · +'+Math.round(m.ascent)+' m / −'+Math.round(m.descent)+' m · '+Math.round(m.ascent/km)+' m+/km'+(existing?' · median '+existing:'');}};
  enrichSelected(selected);
  const candidates=boundary.slice(1).map((_,i)=>({i,m:sliceMetrics(i),range:range(i)})).filter(x=>x.m&&finite(x.range[0])&&finite(x.range[1])).map(x=>({...x,km:Math.max(.001,x.range[1]-x.range[0])})),climb=candidates.slice().sort((x,y)=>(y.m.ascent/y.km)-(x.m.ascent/x.km))[0],standout=root.querySelector('[data-course-climb-standout]');
  if(standout&&climb){standout.textContent='+'+Math.round(climb.m.ascent)+' m · '+Math.round(climb.m.ascent/climb.km)+' m+/km';const button=standout.closest('[data-course-kpi]');if(button){button.disabled=false;button.dataset.courseKpi=String(climb.i);const title=button.querySelector('strong');if(title)title.textContent=boundary[climb.i].name+' → '+boundary[climb.i+1].name;}}
  const visual=i=>{const index=Math.max(0,Math.min(maxIndex,Number(i)||0));courseDifficultyMap?.selectSegment(index,{fit:false});drawElevation(index);root.querySelectorAll('[data-course-row]').forEach(row=>row.classList.toggle('preview',Number(row.dataset.courseRow)===index));root.querySelectorAll('[data-course-segment]').forEach(node=>{const active=Number(node.dataset.courseSegment)===index;node.classList.toggle('selected',active);node.setAttribute('aria-pressed',String(active));});};
  const restore=()=>visual(selected);
  root.querySelectorAll('[data-course-row],[data-course-kpi],[data-course-segment]').forEach(node=>{const index=()=>Number(node.dataset.courseRow??node.dataset.courseKpi??node.dataset.courseSegment);if(!Number.isInteger(index()))return;node.addEventListener('mouseenter',()=>visual(index()));node.addEventListener('mouseleave',restore);node.addEventListener('focus',()=>visual(index()));node.addEventListener('blur',restore);if(node.dataset.courseSegment!==undefined){node.addEventListener('click',()=>{state.segment=index();refreshSegmentSection();});node.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();node.click();}});}});
 }catch(e){if(root.isConnected){mapRoot.innerHTML=empty(e.message);if(elev)elev.innerHTML=empty('Höjdprofil kunde inte laddas.');}}
}
function refreshSegmentSection(){
 const root=$('#segments');if(!root)return;courseDifficultyMap?.destroy();courseDifficultyMap=null;root.innerHTML=flowHeading('DELSTRÄCKELABBET','Var avgjordes loppet?','Jämför segment, relativa prestationer och placeringar utan att fabricera saknade passager.')+views.courseDifficulty(a,selected(),state)+views.segments(a,selected(),state);hydrateCourseDifficulty(renderVersion);
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
async function showMap(root,records,kind,options={}){
 const token=generation;root.innerHTML=empty('Laddar aktuell rutt…');
 try{
  const [route,module]=await Promise.all([loader.route(a.race),import('./map-engine.js')]);
  if(token!==generation||!root.isConnected||(kind==='profile'&&!$('#profile').open)||(kind==='duel'&&!$('#duel').open))return;
  const record=kind==='profile'?records[0]:null,referenceSeries=record?buildReplayReferences(record,route):[],insights=record?replayInsights(record):[];
  const mounted=await module.mountMap(root,{route,adapter:a,records,segment:state.segment,referenceSeries,insights,profile:kind==='profile',musicSrc:'assets/kustlinjens-steg.mp3',initialTime:options.initialTime||0,onTimeChange:options.onTimeChange||null});
  if(token!==generation||!root.isConnected||(kind==='profile'&&!$('#profile').open)||(kind==='duel'&&!$('#duel').open)){mounted.destroy();return;}
  if(kind==='profile')profileMap=mounted;else if(kind==='duel')duelMap=mounted;else mapView=mounted;
 }catch(e){if(root.isConnected)root.innerHTML=empty(e.message);}
}
function syncDuelClock(current=0,max=0){
 const clock=$('#duel-dialog-clock'),end=$('#duel-dialog-clock-max');if(clock)clock.textContent=time(Math.max(0,Number(current)||0));if(end)end.textContent=time(Math.max(0,Number(max)||0));
}
async function openMapDuel(initialTime=0){
 if(!a?.race?.capabilities?.replay)return;const records=state.compare.map(id=>a.byId.get(id)).filter(Boolean).slice(0,5);if(records.length<2)return;
 duelMap?.destroy();duelMap=null;const dialog=$('#duel'),entity=a.race.participant.entity==='team'?'lag':'deltagare',raceLabel=boot.presentation?.[a.race.race_family]?.label||a.race.section||a.race.race_family;
 $('#duel-dialog-race').textContent=raceLabel+' · '+a.race.year;$('#duel-dialog-count').textContent=records.length+' '+entity;const share=$('#duel-dialog-share');if(share)share.innerHTML='↗ <span>Dela</span>';syncDuelClock(0,Math.max(...records.map(r=>Number(r.finish_seconds)||0),0));if(!dialog.open)dialog.showModal();
 await showMap($('#duel-body'),records,'duel',{initialTime,onTimeChange:syncDuelClock});if(duelMap)syncDuelClock(duelMap.getTime?.()||0,duelMap.getMaxTime?.()||0);
}
async function shareDuel(){
 if(!duelMap)return;const u=new URL(location.href);u.search='';u.hash='';u.searchParams.set('race',state.raceKey);u.searchParams.set('compare',state.compare.slice(0,5).join(','));u.searchParams.set('duel','1');u.searchParams.set('t',String(Math.max(0,Math.round(duelMap.getTime?.()||0))));const button=$('#duel-dialog-share');
 try{await navigator.clipboard.writeText(u.href);if(button){button.textContent='✓ Länk kopierad';setTimeout(()=>{if(button?.isConnected)button.innerHTML='↗ <span>Dela</span>';},1800);}}catch{prompt('Kopiera länken:',u.href);}
}
async function openProfile(id,update=true){
 const r=a.byId.get(String(id));if(!r)return;profileMap?.destroy();profileMap=null;profileTrigger=document.activeElement;state.profile=String(id);
 $('#profile-body').innerHTML=views.profile(a,r,state,isFavorite(r));if(!$('#profile').open)$('#profile').showModal();if(update)syncURL();
 if(a.race.capabilities.replay&&$('#profile-replay'))await showMap($('#profile-replay'),[r],'profile');
}
async function shareView(){
 syncURL(true);const button=$('#share-view');try{await navigator.clipboard.writeText(location.href);if(button){button.textContent='Länk kopierad';setTimeout(()=>{if(button?.isConnected)button.textContent='Dela';},1800);}}catch{prompt('Kopiera länken:',location.href);}
}
async function navigate(section,update=true,{behavior='smooth',focus=true}={}){if(section==='compare'){openCompareDialog();return;}section=normalizeSection(section);const previous=state.section;state.section=section;if(isFlowSection(section)){if(!isFlowSection(previous)||!document.getElementById(section))await render();else updateNav();if(update)syncURL();scrollToSection(section,{focus,behavior});return;}await render();if(update)syncURL();$('#analysis').scrollIntoView({block:'start',behavior:motionBehavior(behavior)});}
document.addEventListener('click',async e=>{
 const b=e.target.closest('button,a');if(!b||!state)return;
 if(b.dataset.family){const family=b.dataset.family,editions=Object.values(boot.race_catalog).filter(r=>r.race_family===family),race=editions.find(r=>r.year===a.race.year)||editions.sort((x,y)=>y.year-x.year)[0];await loadRace(race.race_key,{scroll:false,preserveScroll:true});return;}
 if(b.dataset.clubSuggestion){chooseClub(b.dataset.clubSuggestion);return;}
 if(b.dataset.clubArenaAdd){state.clubNames=[...(state.clubNames||[]),b.dataset.clubArenaAdd].slice(0,4);refreshClubSection();return;}
 if(b.dataset.clubRemove){state.clubNames=(state.clubNames||[]).filter(name=>name!==b.dataset.clubRemove);refreshClubSection();return;}
 if(b.dataset.ageGroup){const id=b.dataset.ageGroup,current=new Set(state.ageGroups||[]);if(current.has(id)){if(current.size>1)current.delete(id);}else if(current.size<5)current.add(id);state.ageGroups=[...current];refreshAgeSection();return;}
 if(b.dataset.ageHeatStat){state.ageHeatStat=b.dataset.ageHeatStat==='fastest10'?'fastest10':'median';refreshAgeSection();return;}
 if(b.dataset.sexView&&b.dataset.sex){state.sexViews??={};const key=b.dataset.sexView,current=state.sexViews[key]??={F:true,M:true},sex=b.dataset.sex;if((current.F?1:0)+(current.M?1:0)===1&&current[sex])return;current[sex]=!current[sex];if(['dnf','segments'].includes(key))refreshStatisticsSection();else if(['percentile','flow'].includes(key))refreshSegmentSection();return;}
 if(b.dataset.standoutTab){state.standoutTab=b.dataset.standoutTab;refreshSegmentSection();return;}
 if(b.dataset.courseKpi!==undefined||b.dataset.courseRow!==undefined){const raw=b.dataset.courseKpi!==undefined?b.dataset.courseKpi:b.dataset.courseRow,index=Number(raw);if(Number.isInteger(index)&&index>=0){state.segment=index;refreshSegmentSection();}return;}
 if(b.dataset.profileJump){document.getElementById(b.dataset.profileJump)?.scrollIntoView({behavior:motionBehavior('smooth'),block:'start'});return;}
 if(b.dataset.profileShare!==undefined){syncURL(true);const feedback=document.querySelector('[data-profile-feedback]');try{await navigator.clipboard.writeText(location.href);if(feedback)feedback.textContent='Länk kopierad';}catch{prompt('Kopiera länken:',location.href);if(feedback)feedback.textContent='Länk klar att kopiera';}return;}
 if(b.dataset.profilePlan){toggleProfilePlan(b.dataset.profilePlan);return;}
 if(b.dataset.profilePlanClose!==undefined){const panel=document.querySelector('[data-profile-plan-panel]');if(panel)panel.hidden=true;document.querySelector('[data-profile-plan]')?.setAttribute('aria-expanded','false');return;}
 if(b.dataset.profileCompare){const id=String(b.dataset.profileCompare),exists=state.compare.includes(id),limit=compareLimit();if(exists)state.compare=state.compare.filter(x=>x!==id);else if(state.compare.length<limit)state.compare.push(id);else{status(limit===5?'Max fem resultat kan väljas till Kartduell':'Max två resultat kan väljas');return;}const selectedNow=state.compare.includes(id);b.textContent=selectedNow?'✓ Vald till jämförelse':'Välj till jämförelse';b.setAttribute('aria-pressed',String(selectedNow));const feedback=document.querySelector('[data-profile-feedback]');if(feedback)feedback.textContent=selectedNow?'Loppet är valt. Du kan fortsätta använda Replay.':'Loppet togs bort från jämförelsen.';renderTopTools();syncURL(true);return;}
 if(b.dataset.lookupResult){chooseLookup(b.dataset.lookupResult);return;}
 if(b.id==='focus-runner-search'){const input=$('#lookup');input?.focus();input?.scrollIntoView({block:'center',behavior:motionBehavior('smooth')});return;}
 if(b.id==='open-compare-dialog'){openCompareDialog();return;}
 if(b.id==='share-view'){await shareView();return;}
 if(b.id==='goal-create'){renderPlanOutput();return;}
 if(b.dataset.scrollTarget){e.preventDefault();if(b.dataset.setSection){state.section=b.dataset.setSection;updateNav();syncURL();}document.getElementById(b.dataset.scrollTarget)?.scrollIntoView({behavior:motionBehavior('smooth'),block:'start'});return;}
 if(b.dataset.section){e.preventDefault();await navigate(b.dataset.section);return;}
 if(b.dataset.duelAdd){const id=b.dataset.duelAdd;if(!state.compare.includes(id)&&state.compare.length<compareLimit())state.compare.push(id);duelOptions('');if($('#duel-search'))$('#duel-search').value='';renderTopTools();syncURL();return;}
 if(b.dataset.duelRemove){state.compare=state.compare.filter(id=>id!==b.dataset.duelRemove);renderTopTools();syncURL();return;}
 if(b.id==='open-head-to-head'&&state.compare.length===2){openCompareDialog();return;}
 if(b.id==='head-to-head-duel'&&state.compare.length===2&&a.race.capabilities.replay){await openMapDuel();return;}
 if(b.dataset.headSegment!==undefined){const index=Number(b.dataset.headSegment)||0;document.querySelectorAll('#compare-dialog [data-head-segment]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));headToHeadCourse?.selectSegment(index);return;}
 if(b.id==='open-map-duel'){await openMapDuel();return;}
 if(b.dataset.info){const t=document.getElementById(b.dataset.info);t.hidden=!t.hidden;b.setAttribute('aria-expanded',!t.hidden);return;}
 if(b.dataset.segment){const keepCourse=Boolean(mapView&&$('#course-map')?.querySelector('.map'));state.segment=+b.dataset.segment;mapView?.select(state.segment);document.querySelectorAll('button[data-segment]').forEach(x=>x.setAttribute('aria-pressed',+x.dataset.segment===state.segment));if(isFlowSection(state.section)){await render();if(keepCourse&&$('#load-course'))await showMap($('#course-map'),[],'course');}return;}
 if(b.dataset.sort){state.dir=state.sort===b.dataset.sort?-(state.dir||1):1;state.sort=b.dataset.sort;resultTable();return;}
 if(b.dataset.addCompare){const id=b.dataset.addCompare,limit=compareLimit(),openAfter=b.dataset.openCompareAfter==='true'||Boolean(b.closest('#profile'));if(!state.compare.includes(id)&&state.compare.length<limit)state.compare.push(id);else if(!state.compare.includes(id)){status(limit===5?'Max fem resultat kan väljas till Kartduell':'Direktjämförelse använder högst två resultat för den här upplagan');return;}status(state.compare.length+' resultat valda för jämförelse');if(openAfter){if($('#profile')?.open)$('#profile').close();openCompareDialog();}else if($('#compare-dialog')?.open){renderCompareDialog();requestAnimationFrame(()=>$('#compare-search')?.focus());}syncURL();return;}
 if(b.dataset.removeCompare){state.compare=state.compare.filter(id=>id!==b.dataset.removeCompare);if($('#compare-dialog')?.open)renderCompareDialog();else await render();syncURL();return;}
 if(b.dataset.clearCompare!==undefined){state.compare=[];if($('#compare-dialog')?.open){renderCompareDialog();requestAnimationFrame(()=>$('#compare-search')?.focus());}else await render();syncURL();return;}
 if(b.dataset.quickFilter){state.globalQuery=null;state.filters[b.dataset.quickFilter]=b.dataset.quickValue||'';const input=document.querySelector('[data-filter="'+b.dataset.quickFilter+'"]');if(input)input.value=b.dataset.quickValue||'';await render();return;}
 if(b.dataset.favorite){e.stopPropagation();const r=a.byId.get(b.dataset.favorite);if(isFavorite(r))favorites=favorites.filter(f=>!(f.race===a.race.race_key&&f.id===b.dataset.favorite));else favorites.push({race:a.race.race_key,id:String(r.source_result_id),name:r.name,year:a.race.year});saveFavorites();b.textContent=isFavorite(r)?'Sparad':'Spara lopp';b.setAttribute('aria-pressed',isFavorite(r));renderTopTools();return;}
 if(b.dataset.openFavorite){await loadRace(b.dataset.openFavorite,{restore:{profile:b.dataset.id}});return;}
 if(b.id==='reset-filters'){state.filters={};filters();$('#unit').value=state.unit;await render();}
 if(b.id==='prev-page'){state.page--;resultTable();}
 if(b.id==='next-page'){state.page++;resultTable();}
 if(b.id==='load-course')await showMap($('#course-map'),[],'course');
 if(b.id==='open-duel'){await openMapDuel();}
 if(b.id==='close-profile')$('#profile').close();
 if(b.id==='close-compare-dialog')$('#compare-dialog').close();
 if(b.id==='duel-dialog-share'){await shareDuel();return;}
  if(b.id==='close-duel')$('#duel').close();
});
document.addEventListener('click',e=>{const row=e.target.closest('[data-result]');if(row)openProfile(row.dataset.result);});
document.addEventListener('change',e=>{const input=e.target.closest('[data-series-toggle]');if(!input)return;const key=input.dataset.seriesToggle,chart=input.closest('.interactive-chart');chart?.querySelectorAll('[data-series="'+key+'"]').forEach(item=>{item.hidden=!input.checked;if(item.namespaceURI==='http://www.w3.org/2000/svg')item.style.display=input.checked?'':'none';});});
document.addEventListener('change',e=>{if(!state)return;if(e.target.id==='unit'){state.unit=e.target.value;store.write('unit',state.unit);render();if(state.profile)openProfile(state.profile,false);}else if(e.target.id==='segment-from'){state.segmentFrom=e.target.value;const keys=a.boundary.map(cp=>cp.key),from=keys.indexOf(state.segmentFrom),to=keys.indexOf(state.segmentTo);if(to<=from)state.segmentTo=keys[Math.min(keys.length-1,from+1)];refreshSegmentSection();}else if(e.target.id==='segment-to'){state.segmentTo=e.target.value;const keys=a.boundary.map(cp=>cp.key),from=keys.indexOf(state.segmentFrom),to=keys.indexOf(state.segmentTo);if(to<=from)state.segmentFrom=keys[Math.max(0,to-1)];refreshSegmentSection();}else if(e.target.id==='segment-metric'){state.segmentMetric=e.target.value;refreshSegmentSection();}else if(e.target.id==='segment-comparison'){state.segmentComparison=e.target.value==='field'?'field':'class';refreshSegmentSection();}else if(e.target.dataset.sprintSex){if(e.target.dataset.sprintSex==='F')state.sprintWomenClass=e.target.value;else if(e.target.dataset.sprintSex==='M')state.sprintMenClass=e.target.value;refreshSegmentSection();}else if(e.target.id==='history-reference'){state.historyReference=e.target.value;state.historySegment=null;refreshHistorySection();}else if(e.target.id==='history-segment'){state.historySegment=e.target.value;refreshHistorySection();}});
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
 if(e.target.id==='profile-goal-hours'||e.target.id==='profile-goal-minutes')renderProfilePlanOutput();
});
document.addEventListener('click',e=>{if(!e.target.closest('#global-search'))lookupOptions('');if(!e.target.closest('#map-duel-panel'))duelOptions('');if(!e.target.closest('.club-arena'))renderClubArenaSuggestions('');if(!e.target.closest('.filter-autocomplete'))renderClubSuggestions('');if(!e.target.closest('.compare-search-wrap')){const root=$('#compare-options');if(root){root.hidden=true;$('#compare-search')?.setAttribute('aria-expanded','false');}}});
$('#year').onchange=async()=>{const r=Object.values(boot.race_catalog).find(r=>r.race_family===a.race.race_family&&r.year===+$('#year').value);if(r)await loadRace(r.race_key,{scroll:false,preserveScroll:true});};
$('#global-search').onsubmit=async e=>{e.preventDefault();if(!a)return;const q=$('#lookup').value.trim(),matches=a.records.filter(r=>resultMatches(r,q));if(lookupSuggestionIndex>=0){const item=document.querySelectorAll('#lookup-suggestions [data-lookup-result]')[lookupSuggestionIndex];if(item){chooseLookup(item.dataset.lookupResult);return;}}if(matches.length===1)chooseLookup(matches[0].source_result_id);else{lookupOptions('');state.query=q;state.globalQuery=q;state.page=1;await navigate('results');}};
$('#profile').addEventListener('close',()=>{profileMap?.destroy();profileMap=null;if(state?.profile){state.profile=null;syncURL(true);}profileTrigger?.focus?.();});
$('#compare-dialog').addEventListener('close',()=>{headToHeadCourse?.destroy();headToHeadCourse=null;const root=$('#compare-dialog-body');if(root)root.innerHTML='';compareTrigger?.focus?.();compareTrigger=null;});
$('#duel').addEventListener('close',()=>{duelMap?.destroy();duelMap=null;});
addEventListener('popstate',async()=>{if(!boot)return;const restored=urlState(location.href,boot.race_catalog,boot.default_race),openCompare=restored.section==='compare';if(openCompare)restored.section='overview';if(restored.raceKey!==state.raceKey)await loadRace(restored.raceKey,{restore:restored,replace:true});else{Object.assign(state,restored);state.section=normalizeSection(state.section);await render();if(isFlowSection(state.section))scrollToSection(state.section,{focus:true,behavior:'auto'});if(restored.profile)openProfile(restored.profile,false);else $('#profile').close();}if(openCompare)openCompareDialog();});
async function start(){
 try{history.scrollRestoration='manual';const params=new URLSearchParams(location.search),explicitSection=Boolean(location.hash||params.has('section')),openCompare=location.hash==='#compare'||params.get('section')==='compare',openDuel=params.get('duel')==='1',duelTime=Math.max(0,Number(params.get('t'))||0);if(!explicitSection)window.scrollTo(0,0);boot=await loader.bootstrap();store=storage(boot.event.storage_namespace,safeStorage());const saved=store.read('favorites',[]);favorites=Array.isArray(saved)?saved.filter(f=>f&&typeof f.id==='string'&&boot.race_catalog[f.race]).slice(-40):[];const unit=store.read('unit','pace');state={...urlState(location.href,boot.race_catalog,boot.default_race),unit:unit==='speed'?'speed':'pace',filters:{},segment:0,page:1};if(openCompare)state.section='overview';await loadRace(state.raceKey,{restore:{...state},replace:true,scroll:explicitSection&&!openCompare});if(!explicitSection)window.scrollTo(0,0);if(openCompare)openCompareDialog();else if(openDuel&&state.compare.length>=2&&a.race.capabilities.replay)await openMapDuel(duelTime);}
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
 const hours=$('#goal-hours')?.value,minutes=$('#goal-minutes')?.value,h=Number(hours),m=Number(minutes),root=$('#plan-output');if(!root)return;
 if(hours===''||minutes===''||!Number.isInteger(h)||!Number.isInteger(m)||h<0||h>48||m<0||m>59){root.innerHTML='<div class="goal-pace-error" role="alert">Ange hela, giltiga timmar och minuter mellan 0 och 59.</div>';return;}
 const target=h*3600+m*60;if(target<=0){root.innerHTML='<div class="goal-pace-error" role="alert">Ange en positiv måltid.</div>';return;}
 const p=plan(a,target);if(!p){root.innerHTML='<div class="goal-pace-error" role="alert">Loppplanen kunde inte beräknas.</div>';return;}
 const method=p.method==='observed'?'Bananpassad':p.method==='distance'?'Distansbaserad':'Jämnt snitt',explanation=p.method==='observed'?'Segmentmålen varierar utifrån hur kompletta fullföljare i just denna upplaga fördelade sin verkliga tid över publicerade analyssegment. Fältfiltren påverkar inte referensen.':p.method==='distance'?'Historisk komplett segmentviktning saknas. Reservplanen fördelar tiden efter explicita segmentdistanser och fabricerar inte saknade avstånd.':'Loppet saknar tillräckligt segmentunderlag; endast måltid och nominellt snitt kan visas.';
 const summary='<div class="goal-pace-summary"><article><span>Lopp</span><strong>'+esc(a.race.section||boot.presentation[a.race.race_family].label)+'</strong></article><article><span>Måltid</span><strong>'+time(target)+'</strong></article><article><span>Snittfart</span><strong>'+pace(p.pace,state.unit)+'</strong></article><article><span>Metod</span><strong>'+method+'</strong></article></div>';
 const planRows=p.segments.length?p.segments.map(s=>tr([esc(s.name),finite(s.distanceKm)?Number(s.distanceKm).toFixed(1).replace('.',',')+' km':'–',finite(s.cumulativeDistanceKm)?Number(s.cumulativeDistanceKm).toFixed(1).replace('.',',')+' km':'–',time(s.seconds),time(s.cumulativeSeconds),pace(s.paceSecondsKm,state.unit)])):[];
 root.innerHTML=summary+'<p class="goal-pace-explanation">'+esc(explanation)+(p.method==='observed'?' Komplett kohort n='+p.n+'.':'')+'</p>'+(planRows.length?'<div class="goal-pace-table">'+table(['Kontroll','Segment','Totalt','Segmenttid','Måltid','Tempo'],planRows)+'</div>':'');
}
