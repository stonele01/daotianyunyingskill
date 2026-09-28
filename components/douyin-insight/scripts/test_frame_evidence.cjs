/** Isolated browser acceptance. Does not open or operate a user's existing browser. */
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const { parseArgs } = require('node:util');
const { values: o } = parseArgs({ options: {
  site: { type: 'string' }, legacy: { type: 'string' }, baseline: { type: 'string' }, output: { type: 'string' },
  playwright: { type: 'string' }, browser: { type: 'string' }, account: { type: 'string', default: 'demo_frames' }, help: { type: 'boolean' },
} });
if (o.help) {
  console.log('node test_frame_evidence.cjs --site NEW_SITE --legacy OLD_DATA_NEW_TEMPLATE --baseline OLD_DATA_OLD_TEMPLATE --output NEW_RESULT_DIR --playwright MODULE_PATH --browser CHROMIUM_EXE [--account demo_frames]');
  process.exit(0);
}
for (const k of ['site','legacy','baseline','output','playwright','browser']) if (!o[k]) throw Error(`Missing --${k}`);
const { chromium } = require(path.resolve(o.playwright));
const output = path.resolve(o.output);fs.mkdirSync(output,{recursive:true});
const results = { scenarios: [], externalRequests: [], consoleErrors: [], failures: [] };
(async()=>{
  const browser = await chromium.launch({ executablePath: path.resolve(o.browser), headless:true });
  const context = await browser.newContext({ viewport:{width:1440,height:1100}, reducedMotion:'reduce' });
  const inspect = async (site, baseline=false) => {
    const page = await context.newPage(); const errors=[],requests=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    await page.route('**/*', async route=>{
      const url=route.request().url();
      // Baseline's unchanged CDN references get the exact same local bytes for a fair visual comparison.
      if (baseline && /^https?:/.test(url)) {
        const name=url.includes('lucide')?'lucide.min.js':url.includes('gsap')?'gsap.min.js':null;
        if(name)return route.fulfill({path:path.join(o.site,'assets/vendor',name),contentType:'text/javascript'});
      }
      if(/^https?:|^wss?:/.test(url)){requests.push(url);return route.abort();}
      return route.continue();
    });
    await page.goto(pathToFileURL(path.join(site,`${o.account}.html`)).href);
    await page.waitForFunction(()=>document.querySelectorAll('#workAnalyses .analysis').length===3);
    await page.evaluate(()=>document.fonts.ready);
    return {page,errors,requests};
  };
  try {
    const current=await inspect(o.site),page=current.page;
    const expected=JSON.parse(fs.readFileSync(path.join(o.site,'expected.json'),'utf8'));
    const payload=await page.evaluate(()=>JSON.parse(JSON.stringify(pageData)));
    for(const k of ['works','comments','workAnalyses','qualifiedWorkIds','recreationAngles','transcriptSections'])assert.deepEqual(payload[k],expected[k],`Data preservation ${k}`);
    assert.equal(await page.locator('.frame-evidence-badge').count(),3);
    for(const id of ['demo-work-1','demo-work-2','demo-work-3']) {
      await page.locator(`.analysis[data-work="${id}"] .analysis-open`).click();
      assert.equal(await page.locator('.frame-evidence-block').count(),1);
      assert.equal(await page.locator('.evidence-notes-block').count(),1);
      await page.waitForFunction(()=>[...document.querySelectorAll('.frame-evidence-grid img')].every(i=>i.complete&&i.naturalWidth>0));
      assert.equal(await page.locator('.frame-evidence-item').count(),2);
      const badge=await page.locator(`.analysis[data-work="${id}"] .frame-evidence-badge`).innerText();
      assert.equal(badge,'画面证据 2 帧');
      if(id==='demo-work-3')assert.equal(await page.locator('.quote-list').count(),0,'Visual-only evidence must not become transcript-qualified');
      await page.locator('.frame-evidence-zoom').first().click();
      assert.equal(await page.locator('#frameEvidenceLightbox').evaluate(el=>el.open),true);
      await page.waitForFunction(()=>document.querySelector('#frameEvidenceLightbox img').naturalWidth>0);
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#frameEvidenceLightbox').evaluate(el=>el.open),false);
      assert.equal(await page.locator('#drawer').evaluate(el=>el.classList.contains('open')),true);
      assert.equal(await page.evaluate(()=>document.activeElement.classList.contains('frame-evidence-zoom')),true);
      if(id==='demo-work-1') {
        await page.locator('.frame-evidence-block').screenshot({path:path.join(output,'new-frame-gallery.png')});
        await page.locator('.evidence-notes-block').screenshot({path:path.join(output,'new-evidence-notes.png')});
      }
      await page.locator('#close').click();
    }
    assert.equal(await page.evaluate(()=>window.frameInjected),undefined,'Escaped text must not execute');
    await page.setViewportSize({width:390,height:844});
    await page.locator('.analysis[data-work="demo-work-1"] .analysis-open').click();
    await page.locator('.frame-evidence-block').scrollIntoViewIfNeeded();
    await page.locator('.frame-evidence-block').screenshot({path:path.join(output,'new-frame-gallery-mobile.png')});
    const widths=await page.locator('.frame-evidence-grid').evaluate(el=>({width:el.clientWidth,scroll:el.scrollWidth}));
    assert(widths.scroll<=widths.width+1,'Mobile gallery overflow');
    await page.locator('#close').click();
    await page.goto(pathToFileURL(path.join(o.site,'comment-insight-index.html')).href);
    await page.waitForLoadState('load');
    assert.equal(current.requests.length,0);assert.deepEqual(current.errors,[]);
    results.scenarios.push('new fields: first/ordinary/visual-only cards, both blocks, six images, lightbox/Escape/focus, 390px layout, index offline');
    await page.close();
    const legacy=await inspect(o.legacy), baseline=await inspect(o.baseline,true);
    for(const state of ['overview','demo-work-1','demo-work-2','demo-work-3']) {
      if(state!=='overview')for(const p of [legacy.page,baseline.page])await p.locator(`.analysis[data-work="${state}"] .analysis-open`).click();
      assert.equal(await legacy.page.locator('.frame-evidence-block,.evidence-notes-block,.frame-evidence-badge').count(),0);
      const visible=p=>p.evaluate(()=>document.body.innerText);
      assert.equal(await visible(legacy.page),await visible(baseline.page),`Legacy text ${state}`);
      for(const p of [legacy.page,baseline.page]){await p.mouse.move(0,0);await p.evaluate(()=>document.fonts.ready);}
      const a=await legacy.page.screenshot({animations:'disabled',path:path.join(output,`legacy-${state}.png`)});
      const b=await baseline.page.screenshot({animations:'disabled',path:path.join(output,`baseline-${state}.png`)});
      assert(a.equals(b),`Legacy screenshot differs at ${state}`);
      if(state!=='overview')for(const p of [legacy.page,baseline.page])await p.locator('#close').click();
    }
    assert.deepEqual(legacy.errors,[]);assert.deepEqual(legacy.requests,[]);assert.deepEqual(baseline.errors,[]);
    results.scenarios.push('legacy: identical visible text and PNG bytes in overview and all three drawers; no new UI');
    results.passed=true;
  } catch(e) {results.passed=false;results.failures.push(e.stack);process.exitCode=1;}
  finally {await browser.close();fs.writeFileSync(path.join(output,'browser-results.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results,null,2));}
})();
