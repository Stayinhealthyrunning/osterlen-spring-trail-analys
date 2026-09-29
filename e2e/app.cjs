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
      // The user supplied soundtrack is intentionally kept outside the repo until
      // the binary asset is committed. Keep browser QA focused on lifecycle/UI.
      if(pathname==='/assets/kustlinjens-steg.mp3'){const audio=Buffer.from('SUQzBAAAAAAAIlRTU0UAAAAOAAADTGF2ZjYxLjcuMTAzAAAAAAAAAAAAAAD/4zjAAAAAAAAAAAAASW5mbwAAAA8AAAAGAAACiABxcXFxcXFxcXFxcXFxcXFxjo6Ojo6Ojo6Ojo6Ojo6Ojo6qqqqqqqqqqqqqqqqqqqqqx8fHx8fHx8fHx8fHx8fHx8fj4+Pj4+Pj4+Pj4+Pj4+Pj4/////////////////////8AAAAATGF2YzYxLjE5AAAAAAAAAAAAAAAAJANwAAAAAAAAAoif1QtqAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/4xjEAAAAA0gAAAAATEFNRTMuMTAwVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVX/4xjEOwAAA0gAAAAAVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVUxBTUUzLjEwMFVVVVVVVVVVVVX/4xjEdgAAA0gAAAAAVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVX/4xjEsQAAA0gAAAAAVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVX/4xjExAAAA0gAAAAAVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVX/4xjExAAAA0gAAAAAVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVU=','base64');res.writeHead(200,{'Content-Type':'audio/mpeg','Content-Length':audio.length,'Accept-Ranges':'bytes'});res.end(audio);return;}
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
  page.on('requestfailed',req=>{if(!req.url().includes('tile.openstreetmap.org'))report.errors.push('network: '+req.url());});
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
      await shot('parity-desktop-top');
    });

    await run('race/year and runner autocomplete are one coherent selection context',async()=>{
      await open('ost-2025-ultra60');
      assert.equal(await page.locator('#year').inputValue(),'2025');
      const input=page.locator('#lookup');await input.fill('Johan');
      assert.ok(await page.locator('#lookup-suggestions [data-lookup-result]').count()>0);
      await input.press('ArrowDown');assert.ok((await input.getAttribute('aria-activedescendant'))?.startsWith('lookup-option-'));
      await input.press('Escape');assert.equal(await page.locator('#lookup-suggestions').isHidden(),true);
      await page.locator('#year').selectOption('2026');await ready();assert.equal(await page.locator('#year').inputValue(),'2026');
      await page.locator('#year').selectOption('2025');await ready();
      await openProfileBySearch('Johan Lantz');assert.ok((await page.locator('#profile-body').innerText()).includes('Johan Lantz'));
      await page.locator('#close-profile').click();
    });

    await run('individual analysis auto-loads Ultravasan-style OSM Replay with side panels and references',async()=>{
      await open('ost-2025-ultra60');await openProfileBySearch('Johan Lantz');
      assert.equal(await page.locator('#load-profile-replay').count(),0);
      await page.locator('#profile .runner-replay').waitFor();
      assert.ok(await page.locator('#profile .runner-replay-now').isVisible());
      assert.ok(await page.locator('#profile .runner-replay-map-panel').isVisible());
      assert.ok(await page.locator('#profile .runner-replay-insights').isVisible());
      assert.ok(await page.locator('#profile .leaflet-container').isVisible());
      assert.ok(await page.locator('#profile .leaflet-tile-pane').count()>0);
      const refs=await page.locator('#profile [data-reference-toggle]').count();assert.ok(refs>=2,'expected source-backed replay references');
      assert.ok(await page.locator('#profile [data-reference-toggle="class"]').count()===1);
      assert.ok(await page.locator('#profile [data-reference-toggle="sex"]').count()===1);
      const audio=page.locator('#profile [data-replay-audio]');assert.equal(await audio.count(),1);assert.equal(await audio.evaluate(a=>a.loop),true);assert.match(await audio.getAttribute('src'),/kustlinjens-steg\.mp3$/);
      const seek=page.locator('#profile [data-seek]');await seek.fill('10000');await seek.dispatchEvent('input');assert.ok((await page.locator('#profile [data-now-distance]').innerText()).includes('km'));
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
      await page.locator('#open-head-to-head').click();await page.locator('#compare-dialog[open]').waitFor();const headText=await page.locator('#compare-dialog-body').innerText();assert.ok(headText.includes('HEAD-TO-HEAD'));assert.ok(headText.includes('Jämför två lopp'));for(const label of ['SLUTLIG SKILLNAD','OFFICIELLA PASSAGER FÖRE','OBSERVERADE LEDNINGSVÄXLINGAR','Tidslucka genom loppet','Officiell placeringsresa','Segmentduellen','Pacing mot fältet','Ban- och höjdkontext'])assert.ok(headText.includes(label),label);assert.ok(await page.locator('#compare-dialog .journey-gap-line').count()>0);assert.ok(await page.locator('#compare-dialog [data-head-segment]').count()>0);await page.locator('#compare-dialog #head-to-head-course .leaflet-container').waitFor();const secondSegment=page.locator('#compare-dialog [data-head-segment]').nth(1);if(await secondSegment.count()){await secondSegment.click();assert.equal(await secondSegment.getAttribute('aria-pressed'),'true');}await page.locator('#close-compare-dialog').click();
      await page.locator('#open-map-duel').click();await page.locator('#duel[open]').waitFor();await page.locator('#duel .leaflet-container').waitFor();assert.equal(await page.locator('#duel [data-tiles]').count(),0);assert.ok(await page.locator('#duel .leaflet-tile-pane').count()>0);assert.ok(await page.locator('#duel .duel-replay').isVisible());assert.ok(await page.locator('#duel .replay-duel-board').isVisible());assert.equal(await page.locator('#duel .duel-runner-card').count(),2);const duelSeek=page.locator('#duel [data-seek]');await duelSeek.fill('8000');await duelSeek.dispatchEvent('input');assert.notEqual(await page.locator('#duel [data-duel-clock]').innerText(),'0:00:00');assert.match(await page.locator('#duel [data-duel-distance]').first().innerText(),/km/);await shot('parity-map-duel');await page.locator('#close-duel').click();
    });

    await run('overview mirrors Gotaleden KPI distribution and course profile hierarchy',async()=>{
      await open('ost-2025-ultra60');
      assert.equal(await page.locator('#overview .overview-kpis article').count(),5);
      assert.ok((await page.locator('#overview').innerText()).includes('Visade deltagare'));
      assert.ok((await page.locator('#overview').innerText()).includes('Fullföljande'));
      assert.ok((await page.locator('#overview').innerText()).includes('Snabbaste'));
      assert.ok(await page.locator('#overview .finish-interactive').isVisible());
      await page.locator('#overview-elevation svg').waitFor();
      const female=page.locator('#overview [data-series-toggle="female"]');if(await female.count()){await female.uncheck();assert.equal(await page.locator('#overview [data-series="female"]').first().isHidden(),true);await female.check();}
    });

    await run('statistics workshop uses Gotaleden component names and interactivity',async()=>{
      await nav('statistics');const text=await page.locator('#statistics').innerText();
      for(const label of ['PLACERINGSMOTOR','Tid mot placering','MÅLTIDSSIMULATOR','Vad krävs?','REPET DRAS','Avhopp genom loppet','FARTSIGNATUR','Delsträckornas karaktär','PLACERINGSEXPRESS','Största avancemang'])assert.ok(text.includes(label),label);
      assert.ok(await page.locator('#statistics .scatter-point').count()>100);
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
      assert.ok(await page.locator('#segments .podium article').count()>0);
      const to=page.locator('#segment-to'),opts=await to.locator('option').count();if(opts>1){await to.selectOption({index:1});assert.ok(await page.locator('#segments .podium article').count()>0);}
      await page.locator('#segments [data-standout-tab="fastest"]').click();assert.equal(await page.locator('#segments [data-standout-tab="fastest"]').getAttribute('aria-selected'),'true');assert.ok(await page.locator('#segments .standout-row').count()>0);
      assert.equal((await page.locator('#segments').innerText()).includes('SPURTVINNAREN'),false,'no unsupported speaker-control sprint analysis');
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
      await open('ost-2025-duo60');await nav('gender');assert.equal((await page.locator('#gender').innerText()).includes('Kvinnor'),false);assert.ok((await page.locator('#gender').innerText()).includes('klass')||(await page.locator('#gender').innerText()).includes('Klass'));
      await nav('age-analysis');assert.ok((await page.locator('#age-analysis').innerText()).includes('OFFICIELLA KLASSER'));assert.equal((await page.locator('#age-analysis').innerText()).includes('<30'),false);
      await nav('results');await page.locator('[data-result]').first().click();assert.ok((await page.locator('#profile-body').innerText()).includes('Publicerade lagmedlemmar'));await page.locator('#close-profile').click();
    });

    await run('finish-only families never acquire segments or replay',async()=>{
      for(const family of ['trail22','trail14','trail5']){
        await open('ost-2026-'+family);assert.equal(await page.locator('#analysis-nav [data-section="segments"]').count(),0);assert.equal(await page.locator('#segments').count(),0);
        await nav('results');await page.locator('[data-result]').first().click();assert.equal(await page.locator('#profile .runner-replay').count(),0);await page.locator('#close-profile').click();
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