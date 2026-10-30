// Run: node tests/analytics/privacy.cjs. No real provider calls.
const ts = require('typescript');
const fs = require('fs');
const vm = require('vm');
const assert = require('node:assert/strict');
const context = {exports: {}, URL};
vm.runInNewContext(ts.transpile(fs.readFileSync('lib/analytics-privacy.ts', 'utf8'), {module: ts.ModuleKind.CommonJS}), context);
const sanitize = context.exports.sanitizeAnalyticsEvent;
assert.equal(sanitize({type:'pageview',url:'https://miryn-ai.vercel.app/?token=secret#email'}).url, 'https://miryn-ai.vercel.app/');
for (const path of ['/chat?conversation=secret','/owner/analytics','/reset-password?token=secret','/people/private']) {
  assert.equal(sanitize({type:'pageview',url:'https://miryn-ai.vercel.app'+path}), null);
}
assert.equal(sanitize({type:'event',url:'https://miryn-ai.vercel.app/'}), null);
assert.equal(sanitize({type:'pageview',url:'https://example.com/'}), null);
console.log('7 privacy sanitizer checks passed');
