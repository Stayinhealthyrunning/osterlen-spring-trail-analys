const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');

const root=path.resolve(__dirname,'../docs'),out=path.resolve(__dirname,'../artifacts');
fs.mkdirSync(out,{recursive:true});
const generatedBootstrap=JSON.parse(fs.readFileSync(path.join(root,'data/bootstrap.json'),'utf8').replace(/^\uFEFF/,''));

const server=http.createServer((req,res)=>{
  const pathname=decodeURIComponent(req.url.split('?')[0]);
  const file=path.resolve(root,'.'+(pathname==='/'?'/index.html':pathname));
  if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
  fs.readFile(file,(err,data)=>{
    if(err){
      res.writeHead(404);res.end();return;
    }
    res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json','.css':'text/css','.png':'image/png','.webp':'image/webp','.mp3':'audio/mpeg'})[path.extname(file)]||'application/octet-stream');
    res.end(data);
  });
});

(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const base='http://127.0.0.1:'+server.address().port;
  const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH||undefined});
  const report={cases:[],errors:[],requests:[],screenshots:[],metrics:{}};
  const page=await browser.newPage({viewport:{width:1536,height:1024}});
  page.on('pageerror',e=>report.errors.push('page: '+e.message));
  page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('tile.openstreetmap.org'))report.errors.push('console: '+m.text());});
  page.on('requestfailed',req=>{const url=req.url();if(!url.includes('tile.openstreetmap.org')&&!url.endsWith('/assets/kustlinjens-steg.mp3'))report.errors.push('network: '+url);});
  page.on('request',r=>report.requests.push(r.url().replace(base,'')));

  const ready=()=>page.waitForFunction(()=>document.querySelector('#load-status')?.textContent.includes('upplaga klar'));
  async function open(race,section='overview'){await page.goto(base+'/?race='+race+(section&&section!=='overview'?'&section='+section:''));await ready();}
  async function nav(section){const selector=section==='overview'?'#analysis-nav [data-set-section="overview"]':'#analysis-nav [data-section="'+section+'"]';await page.locator(selector).click();}
  async function shot(name){const file=path.join(out,name+'.png');await page.screenshot({path:file,fullPage:true});report.screenshots.push(name+'.png');}
  async function run(name,fn){await fn();report.cases.push(name);console.log('PASS '+name);}
  async function chooseDuel(query){const input=page.locator('#duel-search');await input.fill(query);const option=page.locator('#duel-suggestions [data-duel-add]').first();await option.waitFor();await option.click();}
  async function openProfileBySearch(query){const input=page.locator('#lookup');await input.fill(query);const option=page.locator('#lookup-suggestions [data-lookup-result]').first();await option.waitFor();await input.press('ArrowDown');await input.press('Enter');await page.locator('#profile[open]').waitFor();}

  try{
    await run('startup matches Gotaleden component order and canonical top position',async()=>{
      await open('ost-2025-ultra60');
      assert.ok((await page.evaluate(()=>scrollY))<=2);
      assert.equal(await page.locator('h1').count(),1);
      assert.equal(await page.locator('main').count(),1);
      assert.ok(await page.locator('#runner-lookup').isVisible());
      assert.ok(await page.locator('#favorites-panel').isVisible());
      assert.ok(await page.locator('#map-duel-panel').isVisible());
      assert.ok(await page.locator('#overview-context').isVisible());
      assert.ok(await page.locator('#goal-pace').isVisible());
      assert.deepEqual(await page.locator('.long-analysis>.flow-section').evaluateAll(nodes=>nodes.map(n=>n.id)),['overview','statistics','gender','age-analysis','segments','history','clubs','results','method']);
      const text=await page.locator('#view').innerText();
      for(const label of ['FÖRDELNING','Måltider','BANPROFIL','STATISTIKVERKSTAD','GENUSPERSPEKTIV','KLASS & ÅLDER','DELSTRÄCKELABBET','HISTORIK','KLUBB- OCH ORTSARENAN','RESULTATDATABAS','Sök, sortera och utforska','Dataprincip'])assert.ok(text.includes(label),label);
      const navText=await page.locator('#analysis-nav').innerText();
      for(const label of ['Löpare','Karta & Kartduell','Måltempo','Översikt','Statistik','Genusperspektiv','Klass & ålder','Delsträckor','Historik','Klubb & ort','Resultat','Dela'])assert.ok(navText.includes(label),label);assert.equal(navText.includes('Metod'),false);
      await page.reload();await ready();assert.ok((await page.evaluate(()=>scrollY))<=2);
      const heroPosition=await page.locator('.hero').evaluate(el=>getComputedStyle(el).backgroundPosition);assert.ok(heroPosition.includes('38%'),'hero crop should reveal the runner head');
      const familyBox=await page.locator('.family-card').first().boundingBox(),yearBox=await page.locator('.race-year-select').boundingBox();assert.ok(familyBox&&Math.abs(familyBox.width-familyBox.height)<8,'race card should be approximately square');assert.ok(yearBox&&Math.abs(yearBox.height-familyBox.height)<8,'year selector should match race-card height');assert.ok(Math.abs(yearBox.width-familyBox.width)<8,'year selector should match race-card width');
      await shot('parity-desktop-top');
    });

    await run('race/year and runner autocomplete are one coherent selection context',async()=>{
      await open('ost-2025-ultra60');
      assert.equal(await page.locator('#year').inputValue(),'2025');
      const input=page.locator('#lookup');await input.fill('Johan');
      assert.ok(await page.locator('#lookup-suggestions [data-lookup-result]').count()>0);
      await input.press('ArrowDown');assert.ok((await input.getAttribute('aria-activedescendant'))?.startsWith('lookup-option-'));
      await input.press('Escape');assert.equal(await page.locator('#lookup-suggestions').isHidden(),true);
      await page.evaluate(()=>scrollTo(0,620));const yBefore=await page.evaluate(()=>scrollY);
      await page.locator('#year').selectOption('2026');await ready();await page.waitForTimeout(60);assert.equal(await page.locator('#year').inputValue(),'2026');assert.ok(Math.abs((await page.evaluate(()=>scrollY))-yBefore)<6,'year selection must preserve viewport');
      await page.locator('#year').selectOption('2025');await ready();await page.waitForTimeout(60);assert.ok(Math.abs((await page.evaluate(()=>scrollY))-yBefore)<6,'edition switch back must preserve viewport');
      await openProfileBySearch('Johan Lantz');assert.ok((await page.locator('#profile-body').innerText()).includes('Johan Lantz'));
      await page.locator('#close-profile').click();
    });

    await run('individual analysis auto-loads Ultravasan-style OSM Replay with side panels and references',async()=>{
      const soundtrack=fs.statSync(path.join(root,'assets','kustlinjens-steg.mp3'));assert.ok(soundtrack.size>1000000,'committed Replay soundtrack must be a real audio asset');
      await open('ost-2025-ultra60');await openProfileBySearch('Johan Lantz');
      assert.equal(await page.locator('#load-profile-replay').count(),0);
      await page.locator('#profile .runner-replay').waitFor();
      assert.ok(await page.locator('#profile .runner-replay-now').isVisible());
      assert.ok(await page.locator('#profile .runner-replay-map-panel').isVisible());
      assert.ok(await page.locator('#profile .runner-replay-insights').isVisible());
      assert.ok(await page.locator('#profile .leaflet-container').isVisible());
      assert.ok(await page.locator('#profile .leaflet-tile-pane').count()>0);
      const toolbarLeft=await page.locator('#profile>.dialog-toolbar .eyebrow').boundingBox(),factsLeft=await page.locator('#profile .detail-facts').boundingBox(),navBox=await page.locator('#profile .profile-quick-nav').boundingBox(),factsBox=await page.locator('#profile .detail-facts').boundingBox();assert.ok(toolbarLeft&&factsLeft&&Math.abs(toolbarLeft.x-factsLeft.x)<5,'profile toolbar should align with content');assert.ok(navBox&&factsBox&&factsBox.y-navBox.y-navBox.height>=8,'profile KPI cards need breathing room below tabs');
      assert.equal(await page.locator('#profile [data-map-zoom-in]').count(),1);assert.equal(await page.locator('#profile [data-map-zoom-out]').count(),1);assert.equal(await page.locator('#profile [data-map-fit]').count(),1);assert.equal(await page.locator('#profile [data-map-follow="runner"]').getAttribute('aria-pressed'),'true');
      assert.ok(['♂','♀'].includes((await page.locator('#profile .replay-person-icon').first().innerText()).trim()),'runner marker should use a sex symbol when source sex is known');
      assert.ok(await page.locator('#profile .elevation-grade-segment').count()>10);const elevationColors=await page.locator('#profile .elevation-grade-segment').evaluateAll(nodes=>[...new Set(nodes.map(n=>n.getAttribute('stroke')))]);assert.ok(elevationColors.length>=3,'elevation should encode grade with several colors');assert.equal(await page.locator('#profile [data-elevation-hit]').count(),1);assert.equal(await page.locator('#profile [data-elevation-current-line]').count(),1);
      const planButton=page.locator('#profile [data-profile-plan]');await planButton.click();assert.equal(await page.locator('#profile[open]').count(),1);assert.ok(await page.locator('#profile [data-profile-plan-panel]').isVisible());assert.ok((await page.locator('#profile [data-profile-plan-panel]').innerText()).includes('Planera utan att lämna Replay'));await page.locator('#profile [data-profile-plan-close]').click();
      const compareButton=page.locator('#profile [data-profile-compare]');const beforePressed=await compareButton.getAttribute('aria-pressed');await compareButton.click();assert.equal(await page.locator('#profile[open]').count(),1);assert.notEqual(await compareButton.getAttribute('aria-pressed'),beforePressed);
      const refs=await page.locator('#profile [data-reference-toggle]').count();assert.ok(refs>=2,'expected source-backed replay references');
      assert.ok(await page.locator('#profile [data-reference-toggle="class"]').count()===1);
      assert.ok(await page.locator('#profile [data-reference-toggle="sex"]').count()===1);
      const audio=page.locator('#profile [data-replay-audio]');assert.equal(await audio.count(),1);assert.equal(await audio.evaluate(a=>a.loop),true);assert.match(await audio.getAttribute('src'),/kustlinjens-steg\.mp3$/);assert.equal(await audio.evaluate(a=>a.paused),true,'music must wait for an explicit Replay start');
      await page.locator('#profile [data-play]').click();await page.waitForTimeout(120);assert.equal(await audio.evaluate(a=>a.paused),false,'music should start with Replay');await page.locator('#profile [data-play]').click();assert.equal(await audio.evaluate(a=>a.paused),false,'pausing Replay must not stop the soundtrack inside the open profile');
      const seek=page.locator('#profile [data-seek]');await seek.fill('10000');await seek.dispatchEvent('input');assert.ok((await page.locator('#profile [data-now-distance]').innerText()).includes('km'));
      const beforeElevationSeek=Number(await seek.inputValue()),elevationRange=page.locator('#profile [data-elevation-range]');assert.equal(await elevationRange.count(),1);const maxElevationDistance=Number(await elevationRange.getAttribute('max')),elevationTarget=(Math.round(maxElevationDistance*.72/.05)*.05).toFixed(2);await elevationRange.fill(elevationTarget);await elevationRange.dispatchEvent('input');await page.waitForTimeout(40);assert.notEqual(Number(await seek.inputValue()),beforeElevationSeek,'elevation scrubber should seek Replay');
      await page.locator('#profile [data-replay-tab="insights"]').click();assert.equal(await page.locator('#profile [data-replay-panel="insights"]').isVisible(),true);
      await shot('parity-profile-replay');
      await page.locator('#close-profile').click();assert.equal(await page.locator('#profile[open]').count(),0);
    });

    await run('top Kartduell builder, direct comparison and map duel follow Gotaleden pattern',async()=>{
      await open('ost-2025-ultra60');
      await chooseDuel('Johan Lantz');await chooseDuel('Christian Malmström');
      assert.equal(await page.locator('#duel-selected button').count(),2);
      assert.equal(await page.locator('#open-head-to-head').isEnabled(),true);
      assert.equal(await page.locator('#open-map-duel').isEnabled(),true);
      await page.locator('#open-head-to-head').click();await page.locator('#compare-dialog[open]').waitFor();const headText=await page.locator('#compare-dialog-body').innerText();assert.ok(headText.includes('HEAD-TO-HEAD'));assert.ok(headText.includes('Jämför två lopp'));for(const label of ['START','MÅL','En mellankontroll ger två tydliga segment','inte avgöra om ledningen bytte','Segmentduellen','Pacing mot fältet','Ban- och höjdkontext'])assert.ok(headText.includes(label),label);assert.equal(await page.locator('#compare-dialog .duel-story article').count(),3);assert.equal(await page.locator('#compare-dialog .journey-gap-line').count(),0);assert.ok(await page.locator('#compare-dialog [data-head-segment]').count()>0);await page.locator('#compare-dialog #head-to-head-course .leaflet-container').waitFor();const secondSegment=page.locator('#compare-dialog [data-head-segment]').nth(1);if(await secondSegment.count()){await secondSegment.click();assert.equal(await secondSegment.getAttribute('aria-pressed'),'true');}await page.locator('#close-compare-dialog').click();
      await page.locator('#open-map-duel').click();await page.locator('#duel[open]').waitFor();await page.locator('#duel .leaflet-container').waitFor();assert.equal(await page.locator('#duel [data-tiles]').count(),0);assert.ok(await page.locator('#duel .leaflet-tile-pane').count()>0);assert.ok(await page.locator('#duel .duel-replay').isVisible());assert.ok(await page.locator('#duel .replay-duel-board').isVisible());assert.equal(await page.locator('#duel .duel-runner-card').count(),2);assert.equal(await page.locator('#duel [data-map-follow="group"]').getAttribute('aria-pressed'),'true');assert.equal(await page.locator('#duel [data-map-zoom-in]').count(),1);assert.ok((await page.locator('#duel-dialog-race').innerText()).includes('2025'));assert.equal((await page.locator('#duel-dialog-count').innerText()).includes('2 deltagare'),true);assert.equal(await page.locator('#duel-dialog-clock').innerText(),'0:00:00');assert.notEqual(await page.locator('#duel-dialog-clock-max').innerText(),'0:00:00');
      const duelAudio=page.locator('#duel [data-replay-audio]');assert.equal(await duelAudio.count(),1);assert.match(await duelAudio.getAttribute('src'),/kustlinjens-steg\.mp3$/);assert.equal(await duelAudio.evaluate(a=>a.paused),true);await page.locator('#duel [data-play]').click();await page.waitForTimeout(120);assert.equal(await duelAudio.evaluate(a=>a.paused),false);await page.locator('#duel [data-play]').click();await page.locator('#duel [data-reset]').click();assert.equal(await page.locator('#duel-dialog-clock').innerText(),'0:00:00');
      const duelSeek=page.locator('#duel [data-seek]');await duelSeek.fill('8000');await duelSeek.dispatchEvent('input');assert.notEqual(await page.locator('#duel [data-duel-clock]').innerText(),'0:00:00');assert.notEqual(await page.locator('#duel-dialog-clock').innerText(),'0:00:00');assert.match(await page.locator('#duel [data-duel-distance]').first().innerText(),/km/);
      await page.evaluate(()=>{window.__duelShared='';Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async value=>{window.__duelShared=value;}}});});await page.locator('#duel-dialog-share').click();const shared=await page.evaluate(()=>window.__duelShared);assert.ok(shared.includes('duel=1'));assert.ok(shared.includes('compare='));assert.ok(shared.includes('t=8000'));await shot('parity-map-duel');await page.locator('#close-duel').click();
      await page.goto(shared);await ready();await page.locator('#duel[open]').waitFor();await page.locator('#duel .leaflet-container').waitFor();assert.equal(await page.locator('#duel-dialog-clock').innerText(),'2:13:20');await page.locator('#close-duel').click();
    });

    await run('overview mirrors Gotaleden KPI distribution and course profile hierarchy',async()=>{
      await open('ost-2025-ultra60');
      assert.equal(await page.locator('#overview .overview-kpis article').count(),5);
      assert.ok((await page.locator('#overview').innerText()).includes('Visade deltagare'));
      assert.ok((await page.locator('#overview').innerText()).includes('Fullföljande'));
      assert.ok((await page.locator('#overview').innerText()).includes('Snabbaste'));
      assert.ok(await page.locator('#overview .finish-interactive').isVisible());
      await page.locator('#overview-elevation svg').waitFor();assert.ok(await page.locator('#overview-elevation .elevation-grade-segment').count()>10);const overviewGradeColors=await page.locator('#overview-elevation .elevation-grade-segment').evaluateAll(nodes=>[...new Set(nodes.map(n=>n.getAttribute('stroke')))]);assert.ok(overviewGradeColors.length>=3);
      const female=page.locator('#overview [data-series-toggle="female"]');if(await female.count()){await female.uncheck();assert.equal(await page.locator('#overview [data-series="female"]').first().isHidden(),true);await female.check();}
    });

    await run('statistics workshop uses Gotaleden component names and interactivity',async()=>{
      await nav('statistics');const text=await page.locator('#statistics').innerText();
      for(const label of ['PLACERINGSMOTOR','Tid mot placering','MÅLTIDSSIMULATOR','Vad krävs?','REPET DRAS','Avhopp genom loppet','FARTSIGNATUR','Delsträckornas karaktär','PLACERINGSEXPRESS','Största avancemang'])assert.ok(text.includes(label),label);
      assert.ok(await page.locator('#statistics .scatter-point').count()>100);
      const scatter=page.locator('#statistics .placement-scatter-svg'),box=await scatter.boundingBox();assert.ok(box);await scatter.evaluate(svg=>{const r=svg.getBoundingClientRect(),emit=(type,x,y)=>svg.dispatchEvent(new PointerEvent(type,{bubbles:true,pointerId:41,clientX:r.left+r.width*x,clientY:r.top+r.height*y,buttons:type==='pointerup'?0:1}));emit('pointerdown',.18,.18);emit('pointermove',.76,.72);emit('pointerup',.76,.72);});assert.equal(await page.locator('#statistics [data-scatter-reset]').isVisible(),true);assert.notEqual(await scatter.getAttribute('viewBox'),'0 0 740 280');await page.locator('#statistics [data-scatter-reset]').click();assert.equal(await scatter.getAttribute('viewBox'),'0 0 740 280');
      const dnfWomen=page.locator('#statistics [data-sex-view="dnf"][data-sex="F"]'),segmentWomen=page.locator('#statistics [data-sex-view="segments"][data-sex="F"]');assert.equal(await dnfWomen.count(),1);assert.equal(await segmentWomen.count(),1);await dnfWomen.click();assert.equal(await page.locator('#statistics [data-sex-view="dnf"][data-sex="F"]').getAttribute('aria-pressed'),'false');assert.equal(await page.locator('#statistics [data-dnf-sex="F"]').count(),0);await page.locator('#statistics [data-sex-view="dnf"][data-sex="F"]').click();await segmentWomen.click();assert.equal(await page.locator('#statistics [data-segment-sex="F"]').count(),0);await page.locator('#statistics [data-sex-view="segments"][data-sex="F"]').click();
      const simBox=await page.locator('#statistics .statistics-simulator').boundingBox(),dnfBox=await page.locator('#statistics .statistics-dnf').boundingBox();assert.ok(simBox&&dnfBox&&Math.abs(simBox.height-dnfBox.height)<3,'target simulator and DNF cards should be equal height');assert.ok(await page.locator('#statistics .pace-shift-analysis').count()===1);assert.ok((await page.locator('#statistics .pace-shift-analysis').innerText()).includes('Före och efter kontrollen'));
      const slider=page.locator('#target-time');const before=await page.locator('#target-time-result').innerText();await slider.fill(String(Number(await slider.getAttribute('min'))+600));await slider.dispatchEvent('input');assert.notEqual(await page.locator('#target-time-result').innerText(),before);
      const point=page.locator('#statistics .scatter-point').first();await point.focus();await page.keyboard.press('Enter');await page.locator('#profile[open]').waitFor();await page.locator('#close-profile').click();
    });

    await run('gender perspective uses Gotaleden median-and-spread line chart and toggles',async()=>{
      await nav('gender');const text=await page.locator('#gender').innerText();
      for(const label of ['FART GENOM LOPPET','Median & spridning per delsträcka','PACING','Fartretention','AUTOMATISKA INSIKTER','Vad skiljer grupperna?'])assert.ok(text.includes(label),label);
      assert.ok(await page.locator('#gender .distribution-band').count()>0);
      assert.ok(await page.locator('#gender .distribution-median').count()>=2);
      const women=page.locator('#gender [data-series-toggle="F"]');assert.equal(await women.count(),1);await women.uncheck();assert.equal(await page.locator('#gender [data-series="F"]').first().isHidden(),true);await women.check();
    });

    await run('age lab is fixed in age order and supports Gotaleden selection and heat statistic',async()=>{
      await nav('age-analysis');
      const labels=(await page.locator('#age-analysis [data-age-group]').allTextContents()).map(x=>x.replace(/\s+\d+\s*$/,'').trim());
      const order=['<30','30–39','40–49','50–59','60+'];assert.deepEqual(labels,order.filter(x=>labels.includes(x)));
      assert.ok((await page.locator('#age-analysis').innerText()).includes('ÅLDERSGRUPPER'));assert.ok((await page.locator('#age-analysis').innerText()).includes('UNDERLAG'));assert.ok((await page.locator('#age-analysis').innerText()).includes('FARTKARTA'));
      const first=page.locator('#age-analysis [data-age-group]').first();if(await page.locator('#age-analysis [data-age-group]').count()>1){await first.click();assert.equal(await first.getAttribute('aria-pressed'),'false');}
      await page.locator('#age-analysis [data-age-heat-stat="fastest10"]').click();assert.equal(await page.locator('#age-analysis [data-age-heat-stat="fastest10"]').getAttribute('aria-pressed'),'true');
    });

    await run('segment lab matches Gotaleden control podium flow and standout hierarchy',async()=>{
      await nav('segments');const text=await page.locator('#segments').innerText();
      for(const label of ['DELSTRÄCKELABBET','Var avgjordes loppet?','Från','Till','Sortera','FÄLTETS MÅLGÅNG','När hade fältet gått i mål?','FÄLTETS FLÖDE','Så sprids startfältet','PRESTATIONER SOM STICKER UT','Fem sätt att hitta ovanliga lopp'])assert.ok(text.includes(label),label);
      assert.equal(await page.locator('#segment-from').count(),1);assert.equal(await page.locator('#segment-to').count(),1);assert.equal(await page.locator('#segment-metric').count(),1);
      const percentileWomen=page.locator('#segments [data-sex-view="percentile"][data-sex="F"]'),flowWomen=page.locator('#segments [data-sex-view="flow"][data-sex="F"]');assert.equal(await percentileWomen.count(),1);assert.equal(await flowWomen.count(),1);await percentileWomen.click();assert.equal(await page.locator('#segments [data-sex-view="percentile"][data-sex="F"]').getAttribute('aria-pressed'),'false');await page.locator('#segments [data-sex-view="percentile"][data-sex="F"]').click();
      const segmentChildren=await page.locator('#segments').evaluate(el=>[...el.children].map(x=>x.id||x.className));assert.ok(await page.locator('#segments #course-difficulty').isVisible());assert.equal(await page.locator('#segments #course-difficulty .course-standouts>button').count(),4);assert.ok(await page.locator('#segments #course-difficulty .head-to-head-course-map').count()===1);assert.ok(await page.locator('#segments #course-difficulty .course-elevation svg').count()===1);assert.ok((await page.locator('#segments').innerText()).includes('RACE INTELLIGENCE LAB · ETT ÅR'));assert.ok(await page.locator('#segments').evaluate(el=>{const course=el.querySelector('#course-difficulty'),lab=el.querySelector('.segment-lab');return Boolean(course&&lab&&(course.compareDocumentPosition(lab)&Node.DOCUMENT_POSITION_FOLLOWING));}));
      const courseGrid=await page.locator('#course-difficulty .course-main').evaluate(el=>getComputedStyle(el).gridTemplateColumns);assert.ok(courseGrid.split(' ').length>=2);const selectedSummary=await page.locator('#course-difficulty [data-course-selected-summary]').innerText();assert.match(selectedSummary,/km/);assert.match(selectedSummary,/\+\d+ m/);const courseHits=page.locator('#course-difficulty .distribution-segment-hit[data-course-segment]');assert.ok(await courseHits.count()>0);const nextHit=courseHits.nth(Math.min(1,(await courseHits.count())-1));await nextHit.hover();assert.ok(await page.locator('#course-difficulty .course-segments>button.preview').count()>=1);await page.mouse.move(1,1);await nextHit.click();assert.equal(await page.locator('#course-difficulty .course-segments>button[aria-pressed="true"]').count(),1);
      assert.ok(await page.locator('#segments .podium article').count()>0);
      const to=page.locator('#segment-to'),opts=await to.locator('option').count();if(opts>1){await to.selectOption({index:1});assert.ok(await page.locator('#segments .podium article').count()>0);}
      await page.locator('#segments [data-standout-tab="fastest"]').click();assert.equal(await page.locator('#segments [data-standout-tab="fastest"]').getAttribute('aria-selected'),'true');assert.ok(await page.locator('#segments .standout-row').count()>0);
      assert.equal((await page.locator('#segments').innerText()).includes('SPURTVINNAREN'),false,'no unsupported speaker-control sprint analysis');
    });

    await run('individual profile mirrors Gotaleden summary pacing and split hierarchy',async()=>{
      await open('ost-2025-ultra60');await nav('results');await page.locator('#result-table [data-result]').first().click();await page.locator('#profile[open]').waitFor();const text=await page.locator('#profile-body').innerText();for(const label of ['DITT LOPP','PACINGPROFIL','MELLANTIDER · ANALYTISKA DELSTRÄCKOR','Från analysgräns till analysgräns'])assert.ok(text.includes(label),label);assert.ok(await page.locator('#profile #personal-summary').isVisible());assert.ok(await page.locator('#profile #profile-replay .runner-replay').isVisible());assert.equal(await page.locator('#profile .pacing-checkpoint-line').count(),1);assert.ok((await page.locator('#profile .profile-pacing-card').innerText()).includes('Kontroll'));await page.locator('#close-profile').click();
    });

    await run('sprint winner appears only with a genuine final timing control',async()=>{
      await open('ost-2019-ultra60');await nav('segments');let text=await page.locator('#segments').innerText();assert.ok(text.includes('SPURTVINNAREN'));assert.ok(text.includes('Årets snabbaste löpare på målspurten'));assert.ok(text.includes('Loppets spurtdrottning'));assert.ok(text.includes('Loppets spurtkung'));assert.ok(text.includes('Vantalängan'));assert.ok(await page.locator('#segments [data-sprint-sex="F"]').count()>=0);
      await open('ost-2025-ultra60');await nav('segments');text=await page.locator('#segments').innerText();assert.equal(text.includes('SPURTVINNAREN'),false);
    });

    await run('club arena selects up to four clubs and renders pace and standouts',async()=>{
      await nav('clubs');const input=page.locator('#club-arena-search');await input.fill('a');const option=page.locator('#club-arena-suggestions [data-club-arena-add]').first();await option.waitFor();await option.click();
      assert.equal(await page.locator('#clubs .selected-chips button').count(),1);assert.equal(await page.locator('#clubs .club-comparison article').count(),1);assert.ok((await page.locator('#clubs').innerText()).includes('Pacing'));assert.ok((await page.locator('#clubs').innerText()).includes('Snabbaste målgångare'));
      await page.locator('#clubs [data-club-remove]').click();assert.equal(await page.locator('#clubs .selected-chips button').count(),0);
    });

    await run('history keeps cancellations and course-comparability guardrails',async()=>{
      await nav('history');await page.waitForFunction(()=>document.querySelector('#history')?.textContent.includes('Inställt'));const text=await page.locator('#history').innerText();assert.ok(text.includes('Inställt'));for(const label of ['FLERÅRIG ANALYS','AKTUELL REFERENS','DELTAGANDE','RESULTATUTVECKLING','UPPLAGEÖVERSIKT','DELSTRÄCKEHISTORIK','VERIFIERADE ÅTERKOMSTER'])assert.ok(text.includes(label),label);assert.ok(text.includes('Median sluttid'));assert.ok(!/\bNaN\b|\bundefined\b/.test(text));
    });

    await run('results database follows Gotaleden columns and opens profiles',async()=>{
      await nav('results');const text=await page.locator('#results').innerText();assert.ok(text.includes('RESULTATDATABAS'));assert.ok(text.includes('Sök, sortera och utforska'));const headers=await page.locator('#results thead th').allTextContents();assert.deepEqual(headers.map(x=>x.replace(/[↑↓]/g,'').trim()),['Plats','Namn','Kön','Klass','Klubb','Tid','Status']);const row=page.locator('#result-table [data-result]').first();assert.ok(await row.count());await row.focus();await page.keyboard.press('Enter');await page.locator('#profile[open]').waitFor();assert.ok(await page.locator('#profile .profile-quick-nav').isVisible());await page.locator('#close-profile').click();
    });

    await run('Duo uses source-backed classes instead of invented demographics',async()=>{
      await open('ost-2025-duo60');assert.ok(await page.locator('#overview .series-bar').count()>0);assert.ok(await page.locator('#overview .relay-class-kpis article').count()>0);assert.equal((await page.locator('#overview').innerText()).includes('Kvinnor'),false);const classToggle=page.locator('#overview [data-series-toggle^="class-"]').first();assert.ok(await classToggle.count());const classSeries=await classToggle.getAttribute('data-series-toggle');await classToggle.uncheck();assert.equal(await page.locator('#overview [data-series="'+classSeries+'"]').first().isHidden(),true);await classToggle.check();await nav('gender');const genderText=await page.locator('#gender').innerText();assert.equal(genderText.includes('Kvinnor'),false);assert.ok(genderText.includes('klass')||genderText.includes('Klass'));assert.ok(genderText.includes('AUTOMATISKA INSIKTER'));assert.ok(genderText.includes('Vad skiljer grupperna?'));
      await nav('age-analysis');assert.ok((await page.locator('#age-analysis').innerText()).includes('OFFICIELLA KLASSER'));assert.equal((await page.locator('#age-analysis').innerText()).includes('<30'),false);
      await nav('segments');assert.equal(await page.locator('#segment-comparison').count(),1);assert.deepEqual(await page.locator('#segment-comparison option').allTextContents(),['Egen klass','Hela fältet']);await page.locator('#segment-comparison').selectOption('field');assert.equal(await page.locator('#segment-comparison').inputValue(),'field');
      await nav('results');await page.locator('[data-result]').first().click();assert.ok((await page.locator('#profile-body').innerText()).includes('Publicerade lagmedlemmar'));await page.locator('#close-profile').click();
    });

    await run('finish-only families never acquire segments or replay',async()=>{
      for(const family of ['trail22','trail14','trail5']){
        await open('ost-2026-'+family);assert.equal(await page.locator('#analysis-nav [data-section="segments"]').count(),0);assert.equal(await page.locator('#segments').count(),0);
        await nav('results');const result=page.locator('#result-table [data-result]').first();assert.ok(await result.count());await result.focus();await page.keyboard.press('Enter');await page.locator('#profile[open]').waitFor();assert.equal(await page.locator('#profile .runner-replay').count(),0);await page.locator('#close-profile').click();
      }
      await open('ost-2018-trail22');assert.equal(await page.locator('#analysis-nav [data-section="segments"]').count(),0);
    });

    await run('all 34 editions render with capability gating and valid values',async()=>{
      for(const meta of Object.values(generatedBootstrap.race_catalog)){
        await open(meta.race_key);const heading=await page.locator('#race-heading').innerText();assert.ok(heading.includes(String(meta.year)),meta.race_key);
        assert.equal(await page.locator('#analysis-nav [data-section="segments"]').count(),meta.capabilities.segment_analysis?1:0,meta.race_key+' segments');
        assert.equal(await page.locator('[data-filter="sex"]').count(),meta.capabilities.sex_filter&&meta.participant.entity==='person'?1:0,meta.race_key+' sex');
        const pageText=await page.locator('#analysis').innerText();assert.ok(!/\bNaN\b|\bundefined\b/.test(pageText),meta.race_key+' invalid rendered value');
        assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth<=2),meta.race_key+' overflow');
      }
    });

    await run('responsive layouts have no document overflow',async()=>{
      for(const [w,h] of [[1536,1024],[1366,768],[900,900],[390,844]]){
        await page.setViewportSize({width:w,height:h});await open('ost-2025-ultra60');const overviewOverflow=await page.evaluate(()=>({delta:document.documentElement.scrollWidth-innerWidth,culprits:[...document.querySelectorAll('body *')].map(el=>{const r=el.getBoundingClientRect();return {tag:el.tagName.toLowerCase(),id:el.id||'',cls:String(el.className||'').slice(0,120),left:Math.round(r.left),right:Math.round(r.right),width:Math.round(r.width),scrollWidth:el.scrollWidth,clientWidth:el.clientWidth};}).filter(x=>x.right>innerWidth+2||x.left<-2||x.scrollWidth>x.clientWidth+2).sort((a,b)=>(b.right-innerWidth)-(a.right-innerWidth)).slice(0,20)}));assert.ok(overviewOverflow.delta<=2,w+' overview overflow '+JSON.stringify(overviewOverflow));
        await nav('gender');assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth<=2),w+' gender overflow');
        await nav('age-analysis');assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth<=2),w+' age overflow');
        await nav('segments');assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth<=2),w+' segments overflow');
        await shot('parity-'+w+'x'+h);
      }
      await page.setViewportSize({width:1536,height:1024});
    });

    await run('reduced motion preserves manual Replay controls',async()=>{
      await page.emulateMedia({reducedMotion:'reduce'});await open('ost-2025-ultra60');await openProfileBySearch('Johan Lantz');await page.locator('#profile .runner-replay').waitFor();assert.equal(await page.locator('#profile [data-play]').isDisabled(),true);assert.equal(await page.locator('#profile [data-seek]').isEnabled(),true);await page.locator('#close-profile').click();await page.emulateMedia({reducedMotion:'no-preference'});
    });

    assert.deepEqual(report.errors,[]);
    report.metrics.firstUsefulMs=await page.evaluate(()=>performance.now());
    console.log('PASS no console, page or unexpected network errors');
  }catch(e){
    report.failure=e.stack;console.error(e);process.exitCode=1;
    try{await shot('failure');}catch{}
  }finally{
    fs.writeFileSync(path.join(out,'browser-qa.json'),JSON.stringify(report,null,2));
    await browser.close();server.close();
  }
})();