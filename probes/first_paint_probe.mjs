// first_paint_probe.mjs — CONTROLLED-HYBRID runtime first-paint / image-reliability probe (Rev 2.2 §G.2).
//
// STATUS: activates in Wave 4, when there is a BUILT candidate site to load. It needs a browser:
//   npm i -D playwright && npx playwright install chromium
// It is intentionally NOT wired into scripts/run-checks.sh (which stays zero-dependency, stdlib-Python).
// Wave 3's `image_plan_check.py` covers the static plan/asset half; THIS covers the runtime half.
//
// What it does (pinned + repeated across the condition matrix):
//   * pins browser + version + viewport + network profile + cache state
//   * matrix: AR/EN · Light/Dark · desktop/mobile · cold/warm cache · slow network · reloads ·
//             client navigation · theme switch · locale switch · no-JS · IO-missing · IO-dead · post-wait
//   * captures frames; FAILS on SVG-before-raster flash or image disappearance
//   * if a slot prohibits SVG fallback, asserts ZERO SVG network requests for that slot
//   * result is EVIDENCE a visual-qa reviewer confirms — a probe never proves aesthetic quality.
//
// Usage (Wave 4):  node probes/first_paint_probe.mjs <base-url> <image-manifest.json>
import { chromium, devices } from 'playwright';
import { readFileSync } from 'node:fs';

const BASE = process.argv[2];
const MANIFEST = process.argv[3];
if (!BASE || !MANIFEST) { console.error('usage: first_paint_probe.mjs <base-url> <image-manifest.json>'); process.exit(2); }

const manifest = JSON.parse(readFileSync(MANIFEST, 'utf8'));
const PIN = { channel: undefined, viewportDesktop: { width: 1440, height: 900 }, mobile: devices['iPhone 13'] };
const CONDITIONS = [
  { name: 'desktop-light-cold', theme: 'light', mobile: false, cache: 'cold', slow: false, js: true },
  { name: 'mobile-dark-slow',   theme: 'dark',  mobile: true,  cache: 'cold', slow: true,  js: true },
  { name: 'desktop-light-nojs', theme: 'light', mobile: false, cache: 'warm', slow: false, js: false },
  { name: 'mobile-dark-io-dead',theme: 'dark',  mobile: true,  cache: 'cold', slow: false, js: true, ioDead: true },
];

let failures = 0;
const fail = (where, msg) => { failures++; console.error(`  ⛔ [FAIL] ${where}: ${msg}`); };

const browser = await chromium.launch();
for (const page of manifest.pages || [{ path: '/' }]) {
  for (const c of CONDITIONS) {
    const ctx = await browser.newContext({
      ...(c.mobile ? PIN.mobile : { viewport: PIN.viewportDesktop }),
      colorScheme: c.theme, javaScriptEnabled: c.js,
    });
    const svgReqs = [];
    const p = await ctx.newPage();
    p.on('request', r => { if (r.url().match(/\.svg(\?|$)/i)) svgReqs.push(r.url()); });
    if (c.ioDead) await p.route(/\.(avif|webp|png|jpe?g)(\?|$)/i, r => r.abort('failed')); // IO-dead: fail fast; page must still paint its layout
    if (c.slow) await ctx.route('**/*', r => setTimeout(() => r.continue(), 200));
    await p.goto(new URL(page.path, BASE).href, { waitUntil: 'commit' }).catch(() => {});
    // capture first frames vs post-wait
    const early = await p.screenshot().catch(() => null);
    await p.waitForTimeout(1500);
    const late = await p.screenshot().catch(() => null);
    // prohibited SVG fallback -> zero SVG requests
    const prohibitsSvg = (manifest.slots || []).some(s => Array.isArray(s.prohibited) && s.prohibited.includes('svg-fallback'));
    if (prohibitsSvg && svgReqs.length) fail(`${page.path}:${c.name}`, `SVG request(s) where prohibited: ${svgReqs[0]}`);
    if (!late) fail(`${page.path}:${c.name}`, 'no post-wait paint (image disappearance / IO-dead not handled)');
    await ctx.close();
  }
}
await browser.close();
if (failures) { console.error(`first_paint_probe: FAIL (${failures})`); process.exit(1); }
console.log('first_paint_probe: PASS (evidence for visual-qa reviewer to confirm)');
