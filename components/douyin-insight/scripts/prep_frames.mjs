/** Local video -> timestamped review sheets + selected report frames. No downloads. */
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { parseArgs } from 'node:util';

const { values: o } = parseArgs({ options: {
  video: { type: 'string' }, 'work-id': { type: 'string' }, site: { type: 'string' },
  evidence: { type: 'string' }, select: { type: 'string' }, every: { type: 'string', default: '1' },
  dense: { type: 'string', multiple: true }, 'max-frames': { type: 'string', default: '600' },
  ffmpeg: { type: 'string', default: 'ffmpeg' }, ffprobe: { type: 'string', default: 'ffprobe' },
  help: { type: 'boolean' },
} });
if (o.help) {
  console.log('node prep_frames.mjs --video local.mp4 --work-id ID --site SITE --evidence NEW_DIR [--every 1] [--dense 2:4:0.25] [--select annotations.json]');
  process.exit(0);
}
function fail(s) { throw Error(s); }
for (const k of ['video', 'work-id', 'site', 'evidence']) if (!o[k]) fail(`Missing --${k}`);
if (!/^[A-Za-z0-9_-]{1,80}$/.test(o['work-id'])) fail('Invalid work ID');
const video = path.resolve(o.video), review = path.resolve(o.evidence), site = path.resolve(o.site);
if (!fs.statSync(video).isFile()) fail('Video must be a local file');
if (fs.existsSync(review)) fail('Evidence directory exists; choose a new directory');
const every = Number(o.every), cap = Number(o['max-frames']);
if (!(every > 0) || !Number.isFinite(every) || !Number.isInteger(cap) || cap < 1 || cap > 2000) fail('Invalid interval or frame cap (1..2000)');
const run = (exe, args) => {
  const r = spawnSync(exe, args, { encoding: 'utf8', maxBuffer: 128 * 1024 * 1024, windowsHide: true });
  if (r.error || r.status !== 0) fail(`${exe}: ${r.error?.message || r.stderr}`);
  return r.stdout;
};
const probe = JSON.parse(run(o.ffprobe, ['-v', 'error', '-select_streams', 'v:0', '-show_frames', '-show_format', '-show_entries', 'frame=best_effort_timestamp_time:format=duration', '-of', 'json', video]));
const pts = probe.frames.map(f => Number(f.best_effort_timestamp_time));
if (!pts.length || pts.some(x => !Number.isFinite(x))) fail('No reliable source frame timestamps');
const times = pts.map(t => t - pts[0]), duration = Number(probe.format.duration);
if (!(duration > 0) || times.some((t, i) => i > 0 && t < times[i - 1])) fail('Invalid timeline');
const chosen = new Map();
function add(t, annotation) {
  if (typeof t !== 'number' || !Number.isFinite(t) || t < 0 || t > times.at(-1)) fail(`Time outside decodable video: ${t}`);
  // First source frame at/after the requested time. Report actual time, not the requested estimate.
  let lo = 0, hi = times.length - 1;
  while (lo < hi) { const m = (lo + hi) >> 1; if (times[m] + 1e-7 < t) lo = m + 1; else hi = m; }
  const prev = chosen.get(lo);
  if (annotation && prev?.annotation) fail(`Two selections resolve to the same source frame: ${t}`);
  chosen.set(lo, { n: lo, t: times[lo], sourcePts: pts[lo], ...(prev || {}), ...(annotation ? { annotation, requestedTime: t } : {}) });
}
for (let t = 0; t <= times.at(-1); t += every) { add(t); if (chosen.size > cap) fail('Overview exceeds --max-frames; use a larger --every'); }
for (const range of o.dense || []) {
  const [start, end, step = 0.25] = range.split(':').map(Number);
  if (!(start >= 0 && end > start && end <= duration && step > 0 && step < every)) fail('Dense range must be start:end:step, step < --every');
  for (let t = start; t < end && t <= times.at(-1); t += step) { add(t); if (chosen.size > cap) fail('Dense sampling exceeds --max-frames'); }
}
const annotations = o.select ? JSON.parse(fs.readFileSync(o.select, 'utf8').replace(/^\uFEFF/, '')) : [];
if (!Array.isArray(annotations)) fail('Selection must be an array of {t,label,caption,sub?}');
for (const a of annotations) {
  if (!a || typeof a.label !== 'string' || !a.label.trim() || typeof a.caption !== 'string' || !a.caption.trim() || (a.sub !== undefined && typeof a.sub !== 'string')) fail('Selection needs reviewed label/caption and optional subtitle');
  add(a.t, a);
}
if (chosen.size > cap) fail('Selections exceed --max-frames');
const framesDir = path.join(site, 'assets', 'frames', o['work-id']);
if (annotations.length && fs.existsSync(framesDir)) fail('Frame output already exists; choose a fresh site directory');
fs.mkdirSync(review, { recursive: true });
const rows = [...chosen.values()].sort((a, b) => a.n - b.n);
const expression = rows.map(r => `eq(n,${r.n})`).join('+');
run(o.ffmpeg, ['-v', 'error', '-i', video, '-map', '0:v:0', '-vf', `select='${expression}'`, '-fps_mode', 'vfr', '-start_number', '0', path.join(review, 'raw-%05d.png')]);
if (annotations.length) fs.mkdirSync(framesDir, { recursive: true });
const selected = [];
for (const [i, r] of rows.entries()) {
  const raw = path.join(review, `raw-${String(i).padStart(5, '0')}.png`);
  const thumb = path.join(review, `thumb-${String(i).padStart(5, '0')}.jpg`);
  run(o.ffmpeg, ['-v', 'error', '-i', raw, '-vf', `scale=320:240:force_original_aspect_ratio=decrease,pad=320:264:(ow-iw)/2:0:black,drawtext=text='${r.t.toFixed(3)} s':x=8:y=242:fontsize=16:fontcolor=white`, '-frames:v', '1', '-q:v', '3', thumb]);
  r.raw = path.basename(raw);
  if (r.annotation) {
    const file = `t${r.t.toFixed(6).replace(/0+$/, '').replace(/\.$/, '')}.jpg`;
    run(o.ffmpeg, ['-v', 'error', '-i', raw, '-vf', "scale=w='min(880,iw)':h=-2", '-frames:v', '1', '-q:v', '3', path.join(framesDir, file)]);
    selected.push({ t: r.t, file, label: r.annotation.label, caption: r.annotation.caption, ...(r.annotation.sub !== undefined ? { sub: r.annotation.sub } : {}) });
  }
}
run(o.ffmpeg, ['-v', 'error', '-framerate', '1', '-start_number', '0', '-i', path.join(review, 'thumb-%05d.jpg'), '-vf', 'tile=4x5:padding=4:margin=4:color=black', '-fps_mode', 'vfr', '-q:v', '3', path.join(review, 'contact-%03d.jpg')]);
const manifest = { workId: o['work-id'], source: video, durationSeconds: duration, sourceOriginPts: pts[0], every, dense: o.dense || [], quality: 'ffmpeg JPEG q=3 (approximate quality; not a literal percent)', samples: rows, frameEvidence: selected };
fs.writeFileSync(path.join(review, 'frames.json'), JSON.stringify(manifest, null, 2) + '\n');
if (selected.length) fs.writeFileSync(path.join(framesDir, 'frames.json'), JSON.stringify({ workId: o['work-id'], frameEvidence: selected }, null, 2) + '\n');
console.log(JSON.stringify({ sampled: rows.length, selected: selected.length, evidence: review, framesDirectory: selected.length ? framesDir : null }));
