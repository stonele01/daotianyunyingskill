/** Merge authored findings without manufacturing transcript qualification or rewriting raw evidence. */
import fs from 'node:fs';
import path from 'node:path';
import { parseArgs } from 'node:util';
const { values: o } = parseArgs({ options: {
  input: { type: 'string' }, common: { type: 'string' }, works: { type: 'string' }, output: { type: 'string' }, help: { type: 'boolean' },
} });
if (o.help) { console.log('node build_report.mjs --input analysis-input.json --common authored-common.json --works authored-works.json --output analysis.json'); process.exit(0); }
for (const k of ['input', 'works', 'output']) if (!o[k]) throw Error(`Missing --${k}`);
const read = p => JSON.parse(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''));
const base = read(o.input), common = o.common ? read(o.common) : {}, authored = read(o.works);
const protectedKeys = ['accountId','profile','works','comments','source','selectedWorks','workWindow','updatedAt','followers','displayName','qualifiedWorkIds','coverage','workAnalyses','transcriptSections'];
for (const k of protectedKeys) if (k in common) throw Error(`Common findings cannot replace ${k}`);
const known = new Set((base.works || []).map(w => String(w.awemeId)));
const comments = new Set((base.comments || []).map(c => String(c.commentId)));
for (const v of common.viewpoints || []) for (const id of v.evidenceCommentIds || []) if (!comments.has(String(id))) throw Error(`Unknown comment evidence ${id}`);
const entries = Array.isArray(authored) ? authored.map(a => [String(a.referenceId), a]) : Object.entries(authored);
const byId = new Map((base.workAnalyses || []).map(a => [String(a.referenceId), structuredClone(a)]));
const sections = structuredClone(base.transcriptSections || {});
for (const [id, a] of entries) {
  if (!known.has(id) || (a.referenceId !== undefined && String(a.referenceId) !== id)) throw Error(`Unknown or mismatched work ${id}`);
  const previous = byId.get(id) || {};
  // Qualification comes from the validated input. Authoring cannot invent or upgrade it.
  for (const k of ['sourceKind','transcriptComplete','spokenScriptPath','asrMetadataPath']) {
    if (k in a && a[k] !== previous[k]) throw Error(`Use finalize_analysis.py to establish or change ${id}.${k}`);
  }
  const { sections: authoredSections, ...fields } = a;
  byId.set(id, { ...previous, ...fields, referenceId: id });
  if (authoredSections) sections[id] = authoredSections;
}
const out = { ...base, ...common, workAnalyses: [...byId.values()], transcriptSections: sections };
const target = path.resolve(o.output);
if ([o.input,o.common,o.works].filter(Boolean).some(p => path.resolve(p) === target)) throw Error('Output cannot overwrite an input');
fs.mkdirSync(path.dirname(target), { recursive: true });
const tmp = `${target}.${process.pid}.tmp`;
fs.writeFileSync(tmp, JSON.stringify(out, null, 2) + '\n');
fs.renameSync(tmp, target);
console.log(JSON.stringify({ output: target, works: out.works.length, analyses: out.workAnalyses.length, frameCount: out.workAnalyses.reduce((n,a) => n + (a.frameEvidence || []).length, 0), status: 'merged; publication validates visual fields; transcript qualifications are unchanged' }));
