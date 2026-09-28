#!/usr/bin/env python3
"""Prepare only images consumed by this report. No credentials or account API calls."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.error
import urllib.parse
import urllib.request

from frame_evidence import local_asset, report_image_slots, rendered_work_ids

MAX_BYTES = 8 * 1024 * 1024
PLACEHOLDER = b'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="320" viewBox="0 0 480 320"><rect width="480" height="320" fill="#132331"/><path d="M120 220l80-90 55 65 35-40 70 65z" fill="#476374"/><circle cx="300" cy="100" r="24" fill="#476374"/><text x="240" y="280" text-anchor="middle" font-family="sans-serif" font-size="20" fill="#c6d6df">Image unavailable</text></svg>'


def write_atomic(target: Path, data: bytes):
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as f:
            temporary = Path(f.name)
            f.write(data)
        temporary.replace(target)
    finally:
        if temporary and temporary.exists(): temporary.unlink()


def image_suffix(data: bytes, content_type: str) -> str:
    if not content_type.lower().split(';', 1)[0].strip().startswith('image/'):
        raise ValueError('响应不是图片')
    if data.startswith(b'\xff\xd8\xff'): return '.jpg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'): return '.png'
    if data[:6] in (b'GIF87a', b'GIF89a'): return '.gif'
    if data.startswith(b'RIFF') and data[8:12] == b'WEBP': return '.webp'
    raise ValueError('不支持的图片格式；仅接受 JPEG/PNG/GIF/WebP')


def download_image(url: str, timeout: float):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('图片地址必须为无内嵌凭据的 HTTP/HTTPS 地址')
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.douyin.com/'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES: raise ValueError('图片超过 8 MiB 限制')
        return body, image_suffix(body, response.headers.get('Content-Type', ''))


def localize(payload: dict, site: Path, *, offline=False, timeout=20, fetch=download_image):
    site = site.resolve()
    out = copy.deepcopy(payload)
    # Normalize the avatar to the same top-level field used by publication.
    out['avatar'] = out.get('avatar') or out.get('profile', {}).get('avatar') or ''
    changes = []
    cache = {}
    warnings = out.setdefault('warnings', [])
    asset_dir = site / 'assets' / 'localized'
    if not asset_dir.resolve().is_relative_to(site): raise ValueError('图片输出目录越界')

    def placeholder():
        target = asset_dir / 'unavailable.svg'
        if target.is_symlink(): raise ValueError('占位图路径不能是符号链接')
        write_atomic(target, PLACEHOLDER)
        return target.relative_to(site).as_posix()

    for obj, key, label in report_image_slots(out):
        value = obj[key]
        try:
            local_asset(site, value)
            continue
        except (ValueError, OSError):
            pass
        if value in cache:
            new_value, reason = cache[value]
        else:
            try:
                if not isinstance(value, str) or not value.startswith(('http://', 'https://')):
                    raise ValueError('本地图片缺失或路径不符合 assets/ 约定')
                if offline:
                    raise ValueError('离线模式未下载远程图片')
                body, suffix = fetch(value, timeout)
                # Use content hash: repeated URLs and reruns reuse a stable local file.
                target = asset_dir / (hashlib.sha256(body).hexdigest() + suffix)
                if target.is_symlink(): raise ValueError('图片目标路径不能是符号链接')
                write_atomic(target, body)
                new_value, reason = target.relative_to(site).as_posix(), ''
            except (ValueError, OSError, urllib.error.URLError) as e:
                # Do not print signed URLs, query parameters or service credentials.
                reason = str(e) if isinstance(e, ValueError) else type(e).__name__
                new_value = placeholder()
            cache[value] = (new_value, reason)
        obj[key] = new_value
        changes.append({'image': label, 'localPath': new_value, 'placeholder': bool(reason)})
        if reason:
            warning = f'{label}使用占位图：{reason}。未取得原图，不影响已有文字数据。'
            if warning not in warnings: warnings.append(warning)
    return out, {'renderedWorkIds': sorted(rendered_work_ids(out)), 'changedImages': changes, 'downloadMode': 'offline-placeholders' if offline else 'public-image-download'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True, help='New prepared JSON, never overwrite the source')
    p.add_argument('--site', type=Path, required=True)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--download', action='store_true', help='Fetch only the visible public avatar/covers')
    mode.add_argument('--offline', action='store_true', help='No network: missing/remote images become labeled placeholders')
    p.add_argument('--timeout', type=float, default=20)
    a = p.parse_args()
    if a.output.resolve() == a.data.resolve(): p.error('输出不能覆盖输入；请保存为新的 prepared.json')
    if not 0 < a.timeout <= 120: p.error('timeout 必须在 0 到 120 秒之间')
    try:
        data = json.loads(a.data.read_text(encoding='utf-8-sig'))
        prepared, summary = localize(data, a.site, offline=a.offline, timeout=a.timeout)
        write_atomic(a.output.resolve(), (json.dumps(prepared, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    except (ValueError, OSError) as e:
        raise SystemExit('报告图片准备失败：'+str(e)) from None
    print(json.dumps({'output': str(a.output.resolve()), **summary}, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
