"""Local video evidence only: FFmpeg PTS sampling, originals, optional labeled views/audio.

No network, model calls, OCR, ASR, installs or changes to the source file.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess


def run(args, timeout=300):
    result = subprocess.run(args, capture_output=True, encoding='utf-8', errors='replace', timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:] or 'Command failed')
    return result


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def labeled_views(out, entries):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return {'status': 'unavailable', 'reason': 'Pillow not installed; use originals and manifest'}
    folder = out / 'labeled'
    folder.mkdir()
    pages = []
    tiles = []
    for item in entries:
        with Image.open(out / item['file']) as source:
            original = source.convert('RGB')
        canvas = Image.new('RGB', (original.width, original.height + 40), 'white')
        canvas.paste(original, (0, 40))
        ImageDraw.Draw(canvas).text((10, 12), f"SOURCE t={item['source_time_seconds']:.6f}s", fill='black')
        target = folder / Path(item['file']).name
        canvas.save(target)
        item['labeled_file'] = target.relative_to(out).as_posix()
        thumb = original.copy()
        thumb.thumbnail((480, 480))
        tile = Image.new('RGB', (480, 512), 'white')
        tile.paste(thumb, ((480 - thumb.width) // 2, 32))
        ImageDraw.Draw(tile).text((8, 10), f"SOURCE t={item['source_time_seconds']:.6f}s", fill='black')
        tiles.append(tile)
    for start in range(0, len(tiles), 12):
        group = tiles[start:start + 12]
        sheet = Image.new('RGB', (1920, math.ceil(len(group) / 4) * 512), '#dddddd')
        for j, tile in enumerate(group):
            sheet.paste(tile, ((j % 4) * 480, (j // 4) * 512))
        filename = f'overview-{start // 12 + 1:03d}.jpg'
        sheet.save(out / filename, quality=92)
        pages.append(filename)
    return {'status': 'created', 'pages': pages, 'warning': 'Overview is for location only; read small text from original frames'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--end', type=float)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--every', type=float, default=2)
    group.add_argument('--every-frame', action='store_true')
    parser.add_argument('--max-frames', type=int, default=120)
    parser.add_argument('--audio', action='store_true', help='Extract entire first audio stream to PCM WAV, not ASR')
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    if not source.is_file():
        parser.error('Source must be a local file')
    if not math.isfinite(args.start) or args.start < 0 or not math.isfinite(args.every) or args.every <= 0:
        parser.error('Times must be finite; start >= 0 and every > 0')
    if args.end is not None and (not math.isfinite(args.end) or args.end <= args.start):
        parser.error('end must be finite and greater than start')
    if not 1 <= args.max_frames <= 1000:
        parser.error('max-frames must be between 1 and 1000; split larger work into windows')
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:
        parser.error('Requires existing ffmpeg and ffprobe; nothing was installed')
    out = args.out.resolve()
    if out.exists():
        parser.error('Output must be a new directory; refusing to overwrite evidence')
    probe = json.loads(run([ffprobe, '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(source)]).stdout)
    videos = [s for s in probe['streams'] if s['codec_type'] == 'video' and not s.get('disposition', {}).get('attached_pic')]
    if not videos:
        parser.error('No video stream found')
    video = videos[0]
    out.mkdir(parents=True)
    write_json(out / 'probe.json', probe)
    result = {'status': 'in_progress', 'source_file': str(source), 'source_sha256': digest(source),
              'clock': 'seconds from first decoded video frame, setpts=PTS-STARTPTS',
              'original_video_start_time': video.get('start_time'),
              'requested': {'start': args.start, 'end': args.end, 'interval_convention': '[start, end)', 'every': None if args.every_frame else args.every,
                            'every_frame': args.every_frame, 'max_frames': args.max_frames},
              'frames': [], 'audio': {'status': 'not_requested'},
              'limits': ['Does not recognize text or speech', 'Sparse samples do not establish continuous motion',
                         'Audio and external transcript clocks must be aligned separately']}
    try:
        raw = out / 'frames'
        raw.mkdir()
        # Tiny tolerance avoids floating-point inclusion/exclusion at exact decimal boundaries.
        # It is far smaller than a frame interval, and does not change recorded source timestamps.
        lower = f'gte(t,{args.start}-0.000000001)'
        window = lower if args.end is None else f'{lower}*lt(t,{args.end}-0.000000001)'
        selection = window if args.every_frame else f'{window}*(isnan(prev_selected_t)+gte(t-prev_selected_t,{args.every}-0.000000001))'
        vf = f"setpts=PTS-STARTPTS,select='{selection}',showinfo"
        command = [ffmpeg, '-hide_banner', '-nostdin', '-n', '-i', str(source), '-map', f"0:{video['index']}",
                   '-vf', vf, '-fps_mode', 'vfr', '-frames:v', str(args.max_frames), str(raw / '%06d.png')]
        execution = run(command)
        (out / 'ffmpeg-frames.log').write_text(execution.stderr, encoding='utf-8')
        pts = [float(x) for x in re.findall(r'\bn:\s*\d+\s+pts:\s*[-\d]+\s+pts_time:([\d.eE+-]+)', execution.stderr)]
        images = sorted(raw.glob('*.png'))
        if not images or len(pts) < len(images):
            raise RuntimeError('No frames in range or missing frame timestamps; do not infer successful coverage')
        # FFmpeg may run filter lookahead; only pair timestamps with files actually written.
        for i, (path, timestamp) in enumerate(zip(images, pts)):
            dest = raw / f'{i+1:06d}-t{timestamp:.6f}s.png'
            path.rename(dest)
            result['frames'].append({'file': dest.relative_to(out).as_posix(), 'source_time_seconds': timestamp})
        result['possibly_capped'] = len(images) >= args.max_frames
        result['observed_sample_range'] = [pts[0], pts[len(images)-1]]
        result['views'] = labeled_views(out, result['frames'])
        if args.audio:
            audios = [s for s in probe['streams'] if s['codec_type'] == 'audio']
            if audios:
                audio = audios[0]
                run([ffmpeg, '-hide_banner', '-nostdin', '-n', '-i', str(source), '-map', f"0:{audio['index']}",
                     '-vn', '-c:a', 'pcm_s16le', str(out / 'audio.wav')])
                result['audio'] = {'status': 'extracted', 'file': 'audio.wav', 'original_audio_start_time': audio.get('start_time'),
                                   'clock': 'WAV local time; reconcile start times before syncing', 'speech_status': 'not_checked'}
            else:
                result['audio'] = {'status': 'no_audio_stream', 'speech_status': 'not_checked'}
        if digest(source) != result['source_sha256']:
            raise RuntimeError('Source changed during extraction; evidence must be rebuilt from a stable file')
        result['status'] = 'complete'
    except Exception as error:
        result['status'] = 'failed'
        result['error'] = str(error)
        write_json(out / 'manifest.json', result)
        print(json.dumps({'status': 'failed', 'manifest': str(out / 'manifest.json'), 'error': str(error)}, ensure_ascii=False))
        return 1
    write_json(out / 'manifest.json', result)
    print(json.dumps({'status': result['status'], 'manifest': str(out / 'manifest.json'),
                      'frames': len(result['frames']), 'possibly_capped': result['possibly_capped']}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
