// Draws the reference picture of a BPMN 2.0 file with bpmn-js (the open-source viewer of bpmn.io).
//   node render_bpmn.js model.bpmn out.svg out.png [scale] [x0 y0 width height]
// NODE_PATH must contain bpmn-js and playwright. The optional box cuts out a part of the diagram.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [, , bpmnFile, outSvg, outPng, scaleArg, ...box] = process.argv;
  if (!bpmnFile || !outSvg || !outPng) { console.error('usage: node render_bpmn.js model.bpmn out.svg out.png [scale] [x y w h]'); process.exit(2); }
  const scale = parseFloat(scaleArg || '2');
  const viewerJs = require.resolve('bpmn-js/dist/bpmn-viewer.production.min.js');
  const xml = fs.readFileSync(bpmnFile, 'utf8');
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  await page.setContent('<html><body style="margin:0;background:#fff"><div id="canvas" style="width:3200px;height:1600px"></div></body></html>');
  await page.addScriptTag({ path: viewerJs });
  const result = await page.evaluate(async (xml) => {
    const viewer = new BpmnJS({ container: '#canvas', textRenderer: { defaultStyle: { fontFamily: 'Arial, Helvetica, sans-serif', fontSize: '13px' }, externalStyle: { fontSize: '12px' } } });
    const { warnings } = await viewer.importXML(xml);
    const { svg } = await viewer.saveSVG();
    return { warnings: warnings.map(w => w.message), svg };
  }, xml);
  if (result.warnings.length) { console.error('import warnings:', result.warnings); process.exit(1); }
  let svg = result.svg;
  const m = svg.match(/viewBox="([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)"/);
  let [vx, vy, vw, vh] = m.slice(1).map(Number);
  if (box.length === 4) {
    [vx, vy, vw, vh] = box.map(Number);
    svg = svg.replace(/viewBox="[^"]+"/, `viewBox="${vx} ${vy} ${vw} ${vh}"`).replace(/width="[-\d.]+"/, `width="${vw}"`).replace(/height="[-\d.]+"/, `height="${vh}"`);
  }
  fs.writeFileSync(outSvg, svg);
  const shot = await browser.newPage({ deviceScaleFactor: scale, viewport: { width: Math.ceil(vw), height: Math.ceil(vh) } });
  await shot.setContent(`<html><body style="margin:0;background:#fff">${svg}</body></html>`);
  await shot.locator('svg').first().screenshot({ path: outPng });
  await browser.close();
  console.log(`written ${path.basename(outSvg)}, ${path.basename(outPng)} (${Math.round(vw)} x ${Math.round(vh)} at scale ${scale})`);
})().catch(e => { console.error(e); process.exit(1); });
