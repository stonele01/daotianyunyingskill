"""Read-only capability inventory. Does not read credentials or start tools."""
import importlib.util
import argparse
import json
import shutil
import sys
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hypit-entry', type=Path, help='Known existing hypit.mjs path; never scan drives')
    parser.add_argument('--asr-model-dir', type=Path, help='Known local faster-whisper model directory')
    args = parser.parse_args()
    entry = args.hypit_entry.expanduser().resolve() if args.hypit_entry else None
    model = args.asr_model_dir.expanduser().resolve() if args.asr_model_dir else None
    model_files = {name: bool(model and (model/name).is_file() and (model/name).stat().st_size > 0)
                   for name in ('model.bin', 'config.json', 'tokenizer.json')}
    print(json.dumps({
        'python': sys.executable,
        'python_version': sys.version.split()[0],
        'module_check_scope': 'current interpreter only; other configured environments were not searched',
        'executables': {name: shutil.which(name) for name in ('ffmpeg', 'ffprobe', 'hypit', 'node')},
        'explicit_hypit_entry': {'path': str(entry) if entry else None,
                                'exists': entry.is_file() if entry else None,
                                'runtime_verified': False},
        'explicit_asr_model': {'path': str(model) if model else None,
                               'required_files': model_files if model else None,
                               'required_files_present': all(model_files.values()) if model else None,
                               'runtime_verified': False},
        'python_modules': {name: importlib.util.find_spec(name) is not None for name in ('PIL', 'openpyxl', 'pandas')},
        'not_checked': ['browser access', 'login', 'paid APIs', 'ASR service', 'model vision', 'business acceptance'],
    }, ensure_ascii=False, indent=2))
