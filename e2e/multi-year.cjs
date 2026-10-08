const http=require('http');
const fs=require('fs');
const path=require('path');
const {chromium}=require('playwright');

const root=path.resolve(__dirname,'../docs');
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.webp':'image/webp','.png':'image/png','.svg':'image/svg+xml','.mp3':'audio/mpeg'};
const server=http.createServer((req,res)=>{
  const url=new URL(req.url,'http://127.0.0.1'),pathname=decodeURIComponent(url.pathname==='/'?'/index.html':url.pathname);
  const file=path.resolve(root,'.'+pathname);
  if(!file.startsWith(root)){res.writeHead(403);res.end();return}
  fs.readFile(file,(err,data)=>{if(err){res.writeHead(404);res.end('not found');return}res.writeHead(200,{'content-type':types[path.extname(file)]||'application/octet-stream'});res.end(data)});
});

(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const port=server.address().port,browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:900,height:900}});
  const errors=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error'&&!m.text().includes('tile.openstreetmap.org'))errors.push(m.text())});page.on('requestfailed',req=>{const url=req.url();if(!url.includes('tile.openstreetmap.org')&&!url.endsWith('/assets/kustlinjens-steg.mp3'))errors.push('network: '+url)});
  try{
    await page.goto(`http://127.0.0.1:${port}/`,{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>document.querySelector('#load-status')?.textContent.includes('upplaga klar'));
    await page.waitForSelector('#multi-year-year');
    if(await page.locator('#multi-year-year').inputValue()!=='2026')throw Error('Year selector should default to latest year');
    if(await page.locator('#multi-year-comparison').isVisible())throw Error('Historical search must not create its own visible panel');
    await page.locator('#multi-year-year').selectOption('all');
    if(!await page.locator('#multi-year-comparison').isVisible())throw Error('All-years search did not become visible in the same panel');
    if(await page.locator('#duel-current-picker').isVisible())throw Error('Current-edition picker did not hide');

    await page.locator('#multi-year-search').fill('Christian Malmström');
    await page.waitForFunction(()=>document.querySelectorAll('#multi-year-suggestions [data-multi-year-add]').length>=2);
    const first2024=page.locator('#multi-year-suggestions [data-multi-year-add]').filter({hasText:'2024'}).first();
    if(!await first2024.count())throw Error('Expected 2024 Christian Malmström result');
    await first2024.click();

    await page.locator('#multi-year-search').fill('Christian Malmström');
    await page.waitForFunction(()=>document.querySelectorAll('#multi-year-suggestions [data-multi-year-add]').length>=1);
    const second2022=page.locator('#multi-year-suggestions [data-multi-year-add]').filter({hasText:'2022'}).first();
    if(!await second2022.count())throw Error('Expected 2022 Christian Malmström result');
    await second2022.click();

    const chips=await page.locator('#multi-year-selected').innerText();
    if(!chips.includes('2024')||!chips.includes('2022'))throw Error('Selected years missing: '+chips);
    const compactLabels=await page.locator('#multi-year-selected button span').allTextContents();
    if(JSON.stringify(compactLabels)!==JSON.stringify(['Christian Malmström · 2024','Christian Malmström · 2022']))throw Error('Runner chips must show only name and year: '+JSON.stringify(compactLabels));
    if(await page.locator('#multi-year-selected button i').count())throw Error('Runner chip ordinal numbers must not be visible');
    if(await page.locator('#open-multi-year-comparison').isDisabled())throw Error('Comparison button remained disabled');
    await page.locator('#open-multi-year-comparison').click();
    await page.waitForSelector('#multi-year-dialog[open]');
    const body=await page.locator('#multi-year-dialog-body').innerText();
    if(!body.includes('Christian Malmström'))throw Error('Runner missing from comparison');
    if(!body.includes('Passagegap är avstängt'))throw Error('Distinct course versions were not safely degraded');
    if(body.includes('A snabbare med')||body.includes('B snabbare med'))throw Error('Incompatible 2024/2022 courses were directly ranked');
    await page.waitForFunction(()=>document.querySelectorAll('#multi-year-route-svg path[stroke-width="3.8"]').length===2);
    // Visual acceptance: the wide dialog keeps title safely inset and all seven
    // replay controls baseline-aligned, without horizontal overflow at mobile widths.
    for(const width of [1440,1140,900,390]){
      await page.setViewportSize({width,height:900});
      const layout=await page.evaluate(()=>{
        const dialog=document.querySelector('#multi-year-dialog'),head=dialog.querySelector('.dialog-toolbar'),title=head.querySelector('h2'),root=document.querySelector('#multi-year-map-root'),controls=root.querySelector('.multi-year-map-controls');
        const rect=el=>{const r=el.getBoundingClientRect();return{x:r.x,y:r.y,left:r.left,right:r.right,bottom:r.bottom,width:r.width}};
        return{width:window.innerWidth,dialog:rect(dialog),title:rect(title),map:rect(root),controls:rect(controls),
          play:rect(root.querySelector('[data-map-play]')),duration:rect(root.querySelector('[data-map-duration]')),
          camera:rect(root.querySelector('[data-map-camera]')),music:rect(root.querySelector('[data-map-music]')),
          volume:rect(root.querySelector('[data-map-volume]')),clock:rect(root.querySelector('[data-map-time]')),
          scrollbar:dialog.scrollWidth-dialog.clientWidth,docScrollbar:document.documentElement.scrollWidth-window.innerWidth};
      });
      if(layout.title.left-layout.dialog.left<15)throw Error('Title clips modal left margin: '+JSON.stringify(layout));
      if(layout.dialog.width>width+1||layout.scrollbar>2||layout.docScrollbar>2)throw Error('Horizontal overflow: '+JSON.stringify(layout));
      if(width>=1140){
        if(layout.dialog.width<width-70)throw Error('Historical dialog is too narrow: '+JSON.stringify(layout));
        const bottoms=[layout.play.bottom,layout.duration.bottom,layout.camera.bottom,layout.music.bottom,layout.clock.bottom];
        if(Math.max(...bottoms)-Math.min(...bottoms)>7)throw Error('Replay controls not baseline aligned: '+JSON.stringify(layout));
      }
    }
    await page.setViewportSize({width:900,height:900});
    const legends=(await page.locator('#multi-year-map-root .multi-year-route-option').allInnerTexts()).join(' | ');
    if(!legends.includes('2024')||!legends.includes('2022'))throw Error('Both year-specific routes must be distinguished');
    await page.locator('#multi-year-map-root [data-map-range]').evaluate(node=>{node.value='3600';node.dispatchEvent(new Event('input',{bubbles:true}))});
    if(!await page.locator('#multi-year-map-root [data-map-marker]').count())throw Error('Source-backed positions missing');
    // Frozen Comparison 2.0 replay standard: 120s, Follow both, full-course,
    // adaptive smooth camera, music at 30% with toggle and pause lifecycle.
    const camera=page.locator('#multi-year-map-root [data-map-camera]');
    if(await camera.inputValue()!=='both')throw Error('Default replay camera must follow both runners');
    if(await page.locator('#multi-year-map-root [data-map-duration]').inputValue()!=='120')throw Error('Default replay duration must be 120s');
    if(!await page.locator('#multi-year-map-root [data-map-music]').count())throw Error('Race soundtrack controls missing');
    if(await page.locator('#multi-year-map-root [data-map-volume]').inputValue()!=='0.3')throw Error('Initial soundtrack volume is not 30 percent');
    await page.evaluate(()=>{
      window.__stableReplayScene=document.querySelector('#multi-year-route-svg [data-map-scene]');
      window.__stableReplayTiles=document.querySelector('#multi-year-route-svg [data-map-tiles]');
      window.__stableReplayMarkers=document.querySelector('#multi-year-route-svg [data-map-markers]');
    });
    await camera.selectOption('full');
    const initialScene=await page.locator('#multi-year-route-svg [data-map-scene]').getAttribute('transform');
    await camera.selectOption('both');
    const followingScene=await page.locator('#multi-year-route-svg [data-map-scene]').getAttribute('transform');
    if(initialScene===followingScene)throw Error('Follow-both does not update camera framing');
    await page.locator('#multi-year-map-root [data-map-zoom="1"]').click();
    const zoomedScene=await page.locator('#multi-year-route-svg [data-map-scene]').getAttribute('transform');
    if(zoomedScene===followingScene)throw Error('Zoom-in failed to update map transformation');
    await camera.selectOption('leader');
    if(await camera.inputValue()!=='leader')throw Error('Follow-furthest mode unavailable');
    await page.locator('#multi-year-map-root [data-map-fit]').click();
    if(await camera.inputValue()!=='full')throw Error('Fit must choose whole-course mode');
    await camera.selectOption('both');
    const music=page.locator('#multi-year-map-root [data-map-music]');
    const oldMute=await music.getAttribute('aria-pressed');
    await music.click();
    if(await music.getAttribute('aria-pressed')===oldMute)throw Error('Soundtrack mute toggle did not work');
    await page.locator('#multi-year-map-root [data-map-volume]').evaluate(node=>{node.value='0.55';node.dispatchEvent(new Event('input',{bubbles:true}))});
    if(await page.locator('#multi-year-map-root [data-map-volume]').inputValue()!=='0.55')throw Error('Soundtrack volume did not change');
    await music.click();
    await page.locator('#multi-year-map-root [data-map-play]').click();
    await page.waitForFunction(()=>document.querySelector('#multi-year-map-root [data-map-play]')?.textContent==='Pausa');
    await page.locator('#multi-year-map-root [data-map-play]').click();
    if(await page.locator('#multi-year-map-root [data-map-play]').innerText()!=='Spela')throw Error('Pause did not stop replay');
    await page.locator('#multi-year-map-root [data-map-reset]').click();
    if(await page.locator('#multi-year-map-root [data-map-time]').innerText()!=='0:00:00')throw Error('Reset did not restore zero clock');
    // Regression: selecting Stefan in 2025 must persist when switching to 2026
    // to add Matilda, and must still be there after switching back to 2025.
    await page.locator('#close-multi-year-dialog').click();
    await page.reload({waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>document.querySelector('#load-status')?.textContent.includes('upplaga klar'));
    await page.locator('#multi-year-year').selectOption('2025');
    await page.locator('#multi-year-search').fill('Stefan Bengtsson');
    await page.waitForFunction(()=>document.querySelectorAll('#multi-year-suggestions [data-multi-year-add]').length>0);
    await page.locator('#multi-year-suggestions [data-multi-year-add]').filter({hasText:'Stefan Bengtsson'}).first().click();
    await page.locator('#multi-year-year').selectOption('2026');
    if(!await page.locator('#multi-year-comparison').isVisible())throw Error('The historical selector must remain visible after switching back to the active year');
    if(!(await page.locator('#multi-year-selected').innerText()).includes('Stefan Bengtsson'))throw Error('Stefan disappeared on 2026');
    await page.locator('#multi-year-search').fill('Matilda Gend');
    await page.waitForFunction(()=>document.querySelectorAll('#multi-year-suggestions [data-multi-year-add]').length>0);
    await page.locator('#multi-year-suggestions [data-multi-year-add]').filter({hasText:'Matilda Gend'}).first().click();
    await page.locator('#multi-year-year').selectOption('2025');
    const persisted=await page.locator('#multi-year-selected').innerText();
    if(!persisted.includes('Stefan Bengtsson')||!persisted.includes('Matilda Gend'))throw Error('Cross-year selection disappeared on return to 2025: '+persisted);
    if(await page.locator('#open-multi-year-comparison').isDisabled())throw Error('Cross-year comparison disabled after year change');
    await page.locator('#open-multi-year-comparison').click();
    await page.waitForFunction(()=>document.querySelectorAll('#multi-year-route-svg path[stroke-width="3.8"]').length===2);
    await page.locator('#close-multi-year-dialog').click();
    console.log('PASS ÖST Stefan 2025 + Matilda 2026 persist across year changes');

    // The original same-edition picker must not lose its already selected
    // result when changing into the cross-edition search.
    await page.reload({waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>document.querySelector('#load-status')?.textContent.includes('upplaga klar'));
    await page.locator('#duel-search').fill('Matilda Gend');
    await page.locator('#duel-suggestions [data-duel-add]').first().click();
    await page.locator('#multi-year-year').selectOption('2025');
    const bridged=await page.locator('#multi-year-selected').innerText();
    if(!bridged.includes('Matilda Gend')||!bridged.includes('2026'))throw Error('Original picker selection was not transferred into the shared history list: '+bridged);
    await page.locator('#multi-year-search').fill('Stefan Bengtsson');
    await page.waitForFunction(()=>document.querySelectorAll('#multi-year-suggestions [data-multi-year-add]').length>0);
    await page.locator('#multi-year-suggestions [data-multi-year-add]').filter({hasText:'Stefan Bengtsson'}).first().click();
    if(!(await page.locator('#multi-year-selected').innerText()).includes('Matilda Gend'))throw Error('Original selection vanished after adding an older result');

    if(errors.length)throw Error('Browser errors: '+errors.join(' | '));
    console.log('PASS ÖST multi-year comparison and picker persistence');
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve))}
})().catch(error=>{console.error(error);process.exitCode=1});
