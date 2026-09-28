"""Use an already-installed faster-whisper and a complete local model, without downloads."""
import argparse
import dataclasses
import json
import os
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audio', type=Path)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--language', default='zh')
    parser.add_argument('--vad', action='store_true')
    args = parser.parse_args()
    audio = args.audio.resolve(strict=True)
    model = args.model_dir.resolve(strict=True)
    out = args.out.resolve()
    if not audio.is_file() or not model.is_dir():
        parser.error('Requires a local audio file and model directory')
    if not all((model/name).is_file() for name in ['model.bin', 'config.json', 'tokenizer.json']):
        parser.error('Local model is incomplete; no download will be attempted')
    if out.exists():
        parser.error('Refusing to overwrite an existing transcription')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        parser.error('This Python lacks faster-whisper; select an existing environment, nothing was installed')
    start = time.monotonic()
    engine = WhisperModel(str(model), device='cpu', compute_type='int8', local_files_only=True, cpu_threads=4)
    segments, info = engine.transcribe(str(audio), language=args.language, beam_size=5,
                                      word_timestamps=True, vad_filter=args.vad, condition_on_previous_text=False)
    rows = [dataclasses.asdict(s) for s in segments]
    result = {'status': 'machine_transcription_unverified', 'needs_listening_review': True,
              'audio_file': str(audio), 'model_directory': str(model), 'offline': True,
              'language_hint': args.language, 'vad_filter': args.vad, 'duration_seconds': info.duration,
              'duration_after_vad': info.duration_after_vad, 'segments': rows,
              'elapsed_seconds': time.monotonic()-start,
              'limits': ['Empty text is not proof of no voice', 'Nonempty text may be hallucinated',
                         'Audio-local times require alignment with the source video']}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({'status': result['status'], 'segments': len(rows), 'output': str(out)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
