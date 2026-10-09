// Run against a production server on port 3000: node scripts/check-landing.mjs
import assert from "node:assert/strict";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { chromium } from "playwright";

const base = process.env.LANDING_CHECK_URL || "http://localhost:3000";
const out = new URL("../../../docs/screens/", import.meta.url);
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true });
const results = { viewports: [], motion: [], routes: {} };
try {
  for (const width of [390, 768, 1024, 1440, 1920]) {
    const page = await browser.newPage({ viewport: { width, height: 844 } });
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
    const session = await page.context().newCDPSession(page);
    await session.send("Network.enable");
    await session.send("Network.setCacheDisabled", { cacheDisabled: true });
    await page.addInitScript(() => {
      window.landingVitals = { lcp: 0, cls: 0 };
      new PerformanceObserver((list) => { for (const e of list.getEntries()) window.landingVitals.lcp = e.startTime; }).observe({ type: "largest-contentful-paint", buffered: true });
      new PerformanceObserver((list) => { for (const e of list.getEntries()) if (!e.hadRecentInput) window.landingVitals.cls += e.value; }).observe({ type: "layout-shift", buffered: true });
    });
    await page.goto(base, { waitUntil: "networkidle" });
    await page.waitForTimeout(1200);
    const measurements = await page.evaluate(() => {
      const entries = [...performance.getEntriesByType("navigation"), ...performance.getEntriesByType("resource")];
      const badTargets = [...document.querySelectorAll("a,button,summary")].filter((e) => {
        const r = e.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && (r.width < 44 || r.height < 44);
      }).map((e) => ({ text: e.textContent.trim().slice(0, 30), width: e.getBoundingClientRect().width, height: e.getBoundingClientRect().height }));
      const headline = document.querySelector("h1").getBoundingClientRect();
      const overlap = [...document.querySelectorAll(".hero-card")].filter((e) => {
        const r = e.getBoundingClientRect();
        return r.width > 0 && r.left < headline.right && r.right > headline.left && r.top < headline.bottom && r.bottom > headline.top;
      }).length;
      return { width: innerWidth, scrollWidth: document.documentElement.scrollWidth, h1: document.querySelectorAll("h1").length, iframes: document.querySelectorAll("iframe").length, requests: entries.length, transferredKB: +(entries.reduce((n, e) => n + e.transferSize, 0) / 1024).toFixed(1), ...window.landingVitals, badTargets, headlineCardOverlap: overlap };
    });
    assert.equal(measurements.h1, 1);
    assert.equal(measurements.iframes, 0);
    assert.ok(measurements.scrollWidth <= width);
    assert.equal(measurements.headlineCardOverlap, 0);
    assert.equal(measurements.badTargets.length, 0);
    assert.equal(errors.length, 0);
    const max = await page.evaluate(() => document.documentElement.scrollHeight);
    if (width === 390 || width === 1440) {
      await page.screenshot({ path: new URL(`12c-hero-${width}.png`, out).pathname.replace(/^\/(\w:)/, "$1") });
      for (let y = 0; y < max; y += 600) { await page.evaluate((value) => scrollTo({ top: value, behavior: "instant" }), y); await page.waitForTimeout(100); }
      await page.waitForTimeout(1300);
      assert.equal(await page.locator(".landing-reveal:not(.is-revealed)").count(), 0);
      await page.evaluate(() => scrollTo({ top: 0, behavior: "instant" }));
      await page.waitForTimeout(150);
      await page.screenshot({ path: new URL(`12c-after-${width}.png`, out).pathname.replace(/^\/(\w:)/, "$1"), fullPage: true });
      for (const [name, selector] of Object.entries({ mood: ".mood-carousel", charts: "#features", faq: "#faq", contact: "#contact", blog: "#insights" })) {
        const target = page.locator(selector).first();
        await target.scrollIntoViewIfNeeded();
        if (name === "faq") await target.locator("summary").first().click();
        await page.waitForTimeout(500);
        await target.screenshot({ path: new URL(`12c-${name}-${width}.png`, out).pathname.replace(/^\/(\w:)/, "$1") });
      }
      const carousel = page.locator(".mood-carousel");
      const before = await carousel.evaluate((e) => e.scrollLeft);
      await carousel.evaluate((e) => e.scrollBy({ left: 300, behavior: "instant" }));
      await page.waitForTimeout(300);
      measurements.carouselScrolls = (await carousel.evaluate((e) => e.scrollLeft)) > before;
      assert.ok(measurements.carouselScrolls);
      await page.emulateMedia({ reducedMotion: "reduce" });
      const running = await page.evaluate(() => [...document.querySelectorAll("main *")].filter((e) => getComputedStyle(e).animationName !== "none").map((e) => e.className));
      measurements.reducedMotionAnimations = running;
      assert.equal(running.length, 0);
      Object.assign(measurements, await page.evaluate(() => {
        const entries = [...performance.getEntriesByType("navigation"), ...performance.getEntriesByType("resource")];
        return { wholePageRequests: entries.length, wholePageTransferredKB: +(entries.reduce((n, e) => n + e.transferSize, 0) / 1024).toFixed(1) };
      }));
      assert.ok(measurements.wholePageRequests < 25);
      assert.ok(measurements.wholePageTransferredKB < 700);
    }
    results.viewports.push({ ...measurements, errors });
    await page.close();
  }
  for (const width of [390, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 844 }, isMobile: width === 390, hasTouch: width === 390 });
    const page = await context.newPage();
    const cdp = await context.newCDPSession(page);
    await cdp.send("Network.enable");
    await cdp.send("Network.setCacheDisabled", { cacheDisabled: true });
    await cdp.send("Network.emulateNetworkConditions", { offline: false, latency: 150, downloadThroughput: 200000, uploadThroughput: 93750 });
    await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
    await cdp.send("LayerTree.enable");
    let layers = [];
    cdp.on("LayerTree.layerTreeDidChange", (e) => { layers = e.layers || []; });
    // Record native timeline events; screenshot readback can distort throttled frame timing.
    await cdp.send("Tracing.start", { categories: "devtools.timeline,cc,blink.user_timing", transferMode: "ReturnAsStream" });
    await page.addInitScript(() => {
      window.motionCheck = { tasks: [], frames: [], cls: 0, scrolling: false, last: 0 };
      new PerformanceObserver((list) => { for (const e of list.getEntries()) window.motionCheck.tasks.push({ duration: e.duration, scroll: window.motionCheck.scrolling }); }).observe({ type: "longtask", buffered: true });
      new PerformanceObserver((list) => { for (const e of list.getEntries()) if (!e.hadRecentInput) window.motionCheck.cls += e.value; }).observe({ type: "layout-shift", buffered: true });
      const frame = (now) => { const state = window.motionCheck; if (state.scrolling && state.last) state.frames.push(now - state.last); state.last = now; requestAnimationFrame(frame); };
      requestAnimationFrame(frame);
    });
    await page.goto(base, { waitUntil: "networkidle" });
    await page.waitForTimeout(1500);
    const heroLayerCount = layers.filter((e) => e.drawsContent).length;
    let heroContentLayers = 0;
    for (const layer of layers.filter((e) => e.drawsContent && e.backendNodeId)) {
      try {
        const { object } = await cdp.send("DOM.resolveNode", { backendNodeId: layer.backendNodeId });
        const { result } = await cdp.send("Runtime.callFunctionOn", { objectId: object.objectId, functionDeclaration: "function(){ return this.nodeType === 1 && !!this.closest('#hero'); }", returnByValue: true });
        if (result.value) heroContentLayers += 1;
        await cdp.send("Runtime.releaseObject", { objectId: object.objectId });
      } catch { /* Detached nodes can disappear between layer events. */ }
    }
    await page.evaluate(() => { window.motionCheck.scrolling = true; });
    const distance = await page.evaluate(() => document.documentElement.scrollHeight - innerHeight);
    await cdp.send("Input.synthesizeScrollGesture", { x: Math.floor(width / 2), y: 650, yDistance: -distance, speed: 1500, gestureSourceType: "mouse" });
    await page.evaluate(() => { window.motionCheck.scrolling = false; });
    const stats = await page.evaluate(() => {
      const s = window.motionCheck;
      return { scrollLongTasks: s.tasks.filter((e) => e.scroll && e.duration > 50).length, totalBlockingTimeMs: Math.round(s.tasks.reduce((n, e) => n + Math.max(0, e.duration - 50), 0)), sampledFrames: s.frames.length, jankyFramePercent: +(100 * s.frames.filter((e) => e > 34).length / Math.max(1, s.frames.length)).toFixed(2), cls: s.cls, finalScrollY: scrollY };
    });
    results.motion.push({ width, cpuThrottle: 4, network: "Slow 4G: 1.6Mbps / 150ms", ...stats, initialContentLayers: heroLayerCount, heroContentLayers });
    const traceReady = new Promise((resolve) => cdp.once("Tracing.tracingComplete", resolve));
    await cdp.send("Tracing.end");
    const { stream } = await traceReady;
    let trace = "";
    for (;;) {
      const chunk = await cdp.send("IO.read", { handle: stream });
      trace += chunk.base64Encoded ? Buffer.from(chunk.data, "base64").toString() : chunk.data;
      if (chunk.eof) break;
    }
    await cdp.send("IO.close", { handle: stream });
    await writeFile(new URL(`12c-performance-${width}.json`, out), trace);
    await context.close();
  }
  for (const path of ["/login", "/signup", "/faq", "/docs", "/privacy", "/terms", "/landing/blog/index.html", "/landing/blog/persistent-memory-human-ai-collaboration/index.html", "/landing/blog/open-loops-accountability/index.html", "/landing/blog/zero-knowledge-memory-architecture/index.html"]) {
    results.routes[path] = (await fetch(base + path)).status;
    assert.equal(results.routes[path], 200);
  }
  const noJS = await browser.newPage({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
  await noJS.goto(base, { waitUntil: "networkidle" });
  results.noJS = await noJS.evaluate(() => ({ dimWords: [...document.querySelectorAll(".about-word")].filter((e) => getComputedStyle(e).opacity !== "1").length, hiddenReveals: [...document.querySelectorAll(".landing-reveal")].filter((e) => getComputedStyle(e).opacity === "0").length }));
  assert.equal(results.noJS.dimWords, 0);
  assert.equal(results.noJS.hiddenReveals, 0);
  await noJS.close();
  for (const width of [390, 1440]) {
    const page = await browser.newPage({ viewport: { width: width * 2, height: 844 } });
    const old = await readFile(new URL(`12c-old-${width}.png`, out));
    const current = await readFile(new URL(`12c-after-${width}.png`, out));
    await page.setContent(`<style>body{margin:0;background:#0a0a0a;display:flex;align-items:start}img{width:${width}px;height:auto}</style><img src="data:image/png;base64,${old.toString("base64")}"><img src="data:image/png;base64,${current.toString("base64")}">`);
    await page.screenshot({ path: new URL(`12c-compare-${width}.png`, out).pathname.replace(/^\/(\w:)/, "$1"), fullPage: true });
    await page.close();
  }
  await writeFile(new URL("12c-checks.json", out), JSON.stringify(results, null, 2));
  console.log(JSON.stringify(results, null, 2));
} finally {
  await browser.close();
}
