"""Validate optional visual evidence and local report images, before publication."""
from __future__ import annotations
import math
import re
from pathlib import Path

ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
FILE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*\.(?:jpg|jpeg|png|webp)$", re.I)

def local_asset(site: Path, value: str) -> Path:
    if not isinstance(value, str) or not value.startswith('assets/') or any(c in value for c in ('\\', ':', '?', '#', '%')):
        raise ValueError(f'Only local assets/ image paths are allowed: {value!r}')
    if '..' in value.split('/'):
        raise ValueError('Asset path traversal')
    p = (site / value).resolve()
    if not p.is_relative_to(site.resolve()) or not p.is_file():
        raise ValueError(f'Missing or escaped local asset: {value}')
    return p

def validate_visual_evidence(payload: dict, site: Path | None = None) -> list[str]:
    errors = []
    works = {str(w.get('awemeId')): w for w in payload.get('works', [])}
    seen = set()
    for a in payload.get('workAnalyses', []):
        wid = str(a.get('referenceId') or a.get('reference_id') or '')
        if wid in seen: errors.append(f'Duplicate work analysis: {wid}')
        seen.add(wid)
        if not any(k in a for k in ('frameEvidence','evidenceNotes','uncertainties','verification')): continue
        try:
            if not ID.fullmatch(wid) or wid not in works: raise ValueError('Unknown or invalid work ID')
            frames = a.get('frameEvidence', [])
            if not isinstance(frames, list): raise ValueError('frameEvidence must be an array')
            files = set()
            duration = works[wid].get('durationSeconds')
            if not duration and works[wid].get('durationMs'): duration = works[wid]['durationMs'] / 1000
            for f in frames:
                if not isinstance(f, dict): raise ValueError('Frame must be an object')
                t = f.get('t')
                if isinstance(t, bool) or not isinstance(t, (int,float)) or not math.isfinite(t) or t < 0: raise ValueError('Frame time must be nonnegative seconds')
                if duration and t >= float(duration): raise ValueError('Frame time outside work duration')
                file = f.get('file', '')
                if not isinstance(file, str) or not FILE.fullmatch(file) or file in files: raise ValueError('Invalid or duplicate frame filename')
                files.add(file)
                for k in ('label','caption'):
                    if not isinstance(f.get(k), str) or not f[k].strip(): raise ValueError(f'Frame {k} required')
                if 'sub' in f and not isinstance(f['sub'], str): raise ValueError('sub must be a string')
                if site is not None: local_asset(site, f'assets/frames/{wid}/{file}')
            notes = a.get('evidenceNotes', [])
            if not isinstance(notes, list): raise ValueError('evidenceNotes must be an array')
            for note in notes:
                if not isinstance(note, dict) or any(not isinstance(note.get(k),str) or not note[k].strip() for k in ('claim','evidence','source')): raise ValueError('Evidence note needs claim/evidence/source')
            unknown = a.get('uncertainties', [])
            if not isinstance(unknown, list) or any(not isinstance(s, str) for s in unknown): raise ValueError('uncertainties must be a string array')
            v = a.get('verification', {})
            if not isinstance(v, dict) or not isinstance(v.get('asrModels', []), list) or any(not isinstance(s,str) for s in v.get('asrModels', [])) or not isinstance(v.get('frameChecks', ''), str): raise ValueError('Invalid verification')
        except (ValueError, TypeError) as e:
            errors.append(f'{wid}: {e}')
    return errors

def rendered_work_ids(payload: dict) -> set[str]:
    """Mirror report.html image consumers, including initial DOM and reachable drawers.

    The initial qualified cards can request images before being trimmed/reordered.
    The final selected cards include metadata-only works. The interaction top four
    are computed from works, then their parent is overwritten later in the template.
    Include these transient image nodes too. They are NOT read from viralWorks/latestWorks.
    Those latter arrays do not
    render images in the current template. Keep the browser coverage test in sync
    if image consumers in the template change.
    """
    works = payload.get('works', [])
    known = {str(w.get('awemeId')) for w in works}
    qualified = set(map(str, payload.get('qualifiedWorkIds', [])))
    analyzed = {str(a.get('referenceId') or a.get('reference_id')) for a in payload.get('workAnalyses', [])}
    selected = {str(w.get('awemeId')) for w in payload.get('selectedWorks', [])}

    def score(work):
        nums = []
        for key in ('diggCount', 'commentCount', 'collectCount', 'shareCount'):
            value = work.get(key)
            if value is None or value == '': return -1
            try:
                if isinstance(value, str):
                    s = value.strip()
                    n = float(int(s, 0)) if s.lower().startswith(('0x', '0b', '0o')) else float(s or '0')
                else: n = float(value)
            except (TypeError, ValueError, OverflowError): return -1
            if not math.isfinite(n) or n < 0: return -1
            nums.append(n)
        return sum(nums)

    # Python and JS both preserve input order for equal totals.
    top = {str(w.get('awemeId')) for w in sorted(works, key=score, reverse=True)[:4]}
    return known & ((qualified & analyzed) | selected | top)


def report_image_slots(payload: dict):
    """Yield mutable object, field and readable label for actual image consumers."""
    avatar = payload.get('avatar') or payload.get('profile', {}).get('avatar')
    if avatar:
        if payload.get('avatar'):
            yield payload, 'avatar', '账号头像'
        else:
            yield payload['profile'], 'avatar', '账号头像'
    visible = rendered_work_ids(payload)
    for w in payload.get('works', []):
        if str(w.get('awemeId')) in visible and w.get('cover'):
            yield w, 'cover', f"作品 {w.get('awemeId')} 的封面"


def validate_report_images(payload: dict, site: Path) -> None:
    for obj, key, label in report_image_slots(payload):
        try:
            local_asset(site, obj[key])
        except (ValueError, OSError) as error:
            if isinstance(obj[key], str) and obj[key].startswith(('http:', 'https:', '//')):
                detail = '仍为远程图片；请先运行 localize_assets.py 准备本地图片'
            else:
                detail = '本地图片不存在或路径不合法；请检查 assets/ 相对路径，或运行 localize_assets.py'
            raise ValueError(f'{label}：{detail}') from error
