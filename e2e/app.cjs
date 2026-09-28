const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const root=path.resolve(__dirname,'../docs'),out=path.resolve(__dirname,'../artifacts');
fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{
 const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]==='/'?'/index.html':req.url.split('?')[0]));
 if(!file.startsWith(root+path.sep)){res.writeHead(403);res.end();return;}
 fs.readFile(file,(err,data)=>{if(err){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json','.css':'text/css','.png':'image/png'})[path.extname(file)]||'application/octet-stream');res.end(data);});
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const base='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({headless:true,executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH||undefined});
 const report={cases:[],errors:[],requests:[],screenshots:[],metrics:{}};
 const page=await browser.newPage({viewport:{width:1536,height:1024}});
 let expectedTiles=false;
 page.on('pageerror',e=>report.errors.push('page: '+e.message));
 page.on('console',m=>{if(m.type()==='error'&&!(expectedTiles&&m.text().includes('net::ERR_FAILED')))report.errors.push('console: '+m.text());});
 page.on('requestfailed',req=>{if(!(expectedTiles&&req.url().includes('tile.openstreetmap.org')))report.errors.push('network: '+req.url());});
 page.on('request',r=>report.requests.push(r.url().replace(base,'')));
 const ready=()=>page.waitForFunction(()=>document.querySelector('#load-status').textContent.includes('upplaga klar'));
 async function open(race,section='overview'){await page.goto(base+'/?race='+race+'&section='+section);await ready();}
 async function nav(section){await page.locator('#analysis-nav [data-section="'+section+'"]').click();}
 async function shot(name){const file=path.join(out,name+'.png');for(let attempt=0;;attempt++){try{await page.screenshot({path:file,fullPage:true});break;}catch(error){if(attempt||!String(error.message).includes('Unable to capture screenshot'))throw error;await page.waitForTimeout(150);}}report.screenshots.push(name+'.png');}
 async function run(name,fn){await fn();report.cases.push(name);console.log('PASS '+name);}
 try{
 await run('startup: bootstrap plus selected race only',async()=>{
  await open('ost-2025-ultra60');
  assert.equal(await page.locator('h1').count(),1);assert.equal(await page.locator('main').count(),1);
  assert.ok(await page.locator('#view').innerText().then(t=>t.includes('Sluttidsfördelning')));
  assert.equal(await page.locator('.route-journey li').count(),7);assert.match(await page.locator('.landscape').evaluate(el=>getComputedStyle(el).backgroundImage),/ost-coast-hero/);
  const loaded=report.requests.filter(p=>p.includes('/data/'));
  assert.deepEqual(loaded,['/data/bootstrap.json','/data/races/ost-2025-ultra60.json']);
  report.metrics.firstUsefulMs=await page.evaluate(()=>performance.now());
  await shot('desktop-overview');
 });
 await run('overview parity: gender series and club autocomplete keyboard flow',async()=>{
  assert.ok(await page.locator('.gender-story').isVisible());
  const club=page.locator('#club-filter');assert.equal(await club.inputValue(),'');assert.equal(await page.locator('#club-suggestions').isHidden(),true);
  await club.fill('a');await page.locator('#club-suggestions [data-club-suggestion]').first().waitFor();await club.press('ArrowDown');await club.press('Enter');
  assert.ok((await club.inputValue()).length>1);assert.equal(await page.locator('#club-suggestions').isHidden(),true);await page.locator('#reset-filters').click();
 });
 await run('result keyboard profile; replay; local vendor; source journey',async()=>{
  await nav('results');const row=page.locator('[data-result]').first();await row.focus();await page.keyboard.press('Enter');
  await page.locator('#profile[open]').waitFor();assert.ok((await page.locator('#profile-body').innerText()).includes('Johan Lantz'));assert.ok(await page.locator('#profile .profile-hero').isVisible());
  await page.locator('#load-profile-replay').click();await page.locator('#profile .leaflet-container').waitFor();
  await page.locator('#profile [data-seek]').fill('10000');await page.locator('#profile [data-seek]').dispatchEvent('input');
  assert.ok((await page.locator('#profile output').innerText()).includes('2:46:40'));
  await shot('desktop-profile-replay');
  await page.keyboard.press('Escape');assert.equal(await page.locator('#profile[open]').count(),0);
 });
 await run('Duo 2025 uses team observations and published members',async()=>{
  await open('ost-2025-duo60','results');await page.locator('[data-result]').first().press('Space');
  const text=await page.locator('#profile-body').innerText();assert.ok(text.includes('Publicerade lagmedlemmar'));assert.ok(text.includes('etapp är inte verifierad'));
  await page.locator('#load-profile-replay').click();await page.locator('#profile .leaflet-container').waitFor();await shot('duo-profile');
  await page.locator('#close-profile').click();
 });
 await run('Ultra 2018 has segments and no borrowed route',async()=>{
  const mark=report.requests.length;await open('ost-2018-ultra60','segments');assert.ok((await page.locator('#view').innerText()).includes('Mediantid'));
  await nav('course');assert.equal(await page.locator('#load-course').count(),0);
  assert.ok(!report.requests.slice(mark).some(x=>x.includes('/courses/')));
 });
 await run('Ultra 2023 preserves distinct observations and time-only segment stats',async()=>{
  await open('ost-2023-ultra60','segments');assert.ok((await page.locator('#view').innerText()).includes('distans saknas'));
  await nav('results');await page.locator('[data-result]').first().click();const text=await page.locator('#profile-body').innerText();assert.ok(text.includes('32 km'));assert.ok(text.includes('Bengtemölla'));await page.keyboard.press('Escape');
 });
 await run('finish-only families and provisional/reconstructed labels',async()=>{
  for(const family of ['trail22','trail14','trail5']){
   await open('ost-2026-'+family,'segments');assert.ok((await page.locator('#view').innerText()).includes('inga publicerade mellantider'));
   await nav('course');const text=await page.locator('#view').innerText();
   if(family==='trail14'){assert.ok(text.includes('Arbetsreferens'));assert.equal(await page.locator('#load-course').count(),0);}
   if(family==='trail5'){assert.ok(text.includes('Rekonstruerad bana'));assert.equal(await page.locator('#goal-hours').inputValue(),'0');assert.equal(await page.locator('#goal-minutes').inputValue(),'35');await page.locator('#load-course').click();await page.locator('#course-map .leaflet-container').waitFor();assert.equal(await page.locator('[data-play]').count(),0);}
  }
  await shot('trail5-course');
  await open('ost-2018-trail22','course');assert.ok((await page.locator('#view').innerText()).includes('inte verifierad'));
 });
 await run('race/year switching, global search independent of filters',async()=>{
  await open('ost-2025-ultra60');await page.locator('[data-filter="sex"]').selectOption('F');
  await page.locator('#lookup').fill('Johan Lantz');await page.locator('#global-search').evaluate(f=>f.requestSubmit());await page.locator('#profile[open]').waitFor();await page.keyboard.press('Escape');
  await page.locator('[data-family="trail22"]').click();await ready();assert.ok((await page.locator('#race-heading').innerText()).includes('2025'));
  assert.equal(await page.locator('[data-filter="sex"]').inputValue(),'');
  await page.locator('#year').selectOption('2026');await ready();assert.ok((await page.locator('#race-heading').innerText()).includes('2026'));
  assert.equal(await page.locator('#year option[value="2020"]').evaluate(el=>el.disabled),true);
  await page.goBack();await ready();assert.ok((await page.locator('#race-heading').innerText()).includes('2025'));
 });
 await run('compare 2, Kartduell, tile failure fallback',async()=>{
  await open('ost-2025-ultra60','compare');
  assert.equal(await page.locator('#compare-options').isHidden(),true);assert.ok((await page.locator('.selection-empty').innerText()).includes('Inga löpare'));
  await page.locator('#compare-search').fill('a');await page.locator('#compare-options [data-add-compare]').first().click();
  await page.locator('#compare-search').fill('a');await page.locator('#compare-options [data-add-compare]').first().click();
  assert.ok((await page.locator('#view').innerText()).includes('Direktjämförelse'));
  assert.equal(await page.locator('.versus article').count(),2);
  await shot('direct-comparison');
  await page.locator('#open-duel').click();await page.locator('#duel .leaflet-container').waitFor();
  expectedTiles=true;await page.route('https://tile.openstreetmap.org/**',route=>route.abort());
  await page.locator('#duel [data-tiles]').click();await page.locator('#duel .route-only').waitFor();
  assert.ok((await page.locator('#duel .map-status').innerText()).includes('Neutral banvy'));
  assert.equal(await page.locator('#duel .leaflet-tile-pane img').count(),0);
  await shot('duel-tile-fallback');await page.locator('#close-duel').click();
 });
 await run('history cancellation, methodology relationships, plan',async()=>{
  await nav('history');await page.waitForFunction(()=>document.querySelector('#view').textContent.includes('Inställt'));
  assert.ok(report.requests.some(p=>p==='/data/history.json'));
  await page.locator('[data-info]').click();assert.equal(await page.locator('[data-info]').getAttribute('aria-expanded'),'true');await page.keyboard.press('Escape');assert.equal(await page.locator('[data-info]').getAttribute('aria-expanded'),'false');
  await nav('course');await page.locator('#goal-hours').fill('7');assert.ok((await page.locator('#plan-output').innerText()).includes('Kalibrerat'));
 });
 await run('responsive all required sizes; no document overflow',async()=>{
  for(const [w,h] of [[1536,1024],[1366,768],[900,900],[390,844]]){
   await page.setViewportSize({width:w,height:h});await open('ost-2025-ultra60');
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth<=2));
   if(w===390)assert.equal(await page.locator('.hero').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length),1);
   await shot('overview-'+w+'x'+h);
   for(const section of ['results','dynamics','segments','course','compare','history','method']){
    await nav(section);if(section==='history')await page.waitForFunction(()=>document.querySelector('#view').textContent.includes('Inställt'));
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth<=2),w+' '+section);
   }
  }
 });
 await run('reduced motion retains manual replay',async()=>{
  await page.emulateMedia({reducedMotion:'reduce'});await open('ost-2025-ultra60','results');await page.locator('[data-result]').first().click();await page.locator('#load-profile-replay').click();await page.locator('#profile .leaflet-container').waitFor();assert.equal(await page.locator('#profile [data-play]').isDisabled(),true);assert.equal(await page.locator('#profile [data-seek]').isEnabled(),true);
 });
 assert.deepEqual(report.errors,[]);
 console.log('PASS no console, page or unexpected network errors');
 }catch(e){report.failure=e.stack;console.error(e);process.exitCode=1;await shot('failure');}
 finally{fs.writeFileSync(path.join(out,'browser-qa.json'),JSON.stringify(report,null,2));await browser.close();server.close();}
})();
