const fs = require('node:fs'), vm = require('node:vm');
const html = fs.readFileSync(0, 'utf8');
let scripts = 0;
for (const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi)) {
  if (!/\bsrc\s*=|application\/(?:ld\+)?json/i.test(m[1]) && m[2].trim()) {
    new vm.Script(m[2], { filename: 'report-inline.js' }); scripts++;
  }
}
console.log(JSON.stringify({ inlineScriptsParsed: scripts }));
