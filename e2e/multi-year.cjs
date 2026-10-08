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
  const errors=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
  try{
    await page.goto(`http://127.0.0.1:${port}/`,{waitUntil:'networkidle'});
    await page.waitForSelector('#multi-year-year');
    if(await page.locator('#multi-year-year').inputValue()!=='all')throw Error('Multi-year selector did not default to all years');

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
    if(await page.locator('#open-multi-year-comparison').isDisabled())throw Error('Comparison button remained disabled');
    await page.locator('#open-multi-year-comparison').click();
    await page.waitForSelector('#multi-year-dialog[open]');
    const body=await page.locator('#multi-year-dialog-body').innerText();
    if(!body.includes('Christian Malmström'))throw Error('Runner missing from comparison');
    if(!body.includes('Passagegap är avstängt'))throw Error('Distinct course versions were not safely degraded');
    if(body.includes('A snabbare med')||body.includes('B snabbare med'))throw Error('Incompatible 2024/2022 courses were directly ranked');
    if(errors.length)throw Error('Browser errors: '+errors.join(' | '));
    console.log('PASS ÖST multi-year comparison');
  }finally{await browser.close();await new Promise(resolve=>server.close(resolve))}
})().catch(error=>{console.error(error);process.exitCode=1});
