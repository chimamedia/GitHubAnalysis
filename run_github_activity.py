"""Load a neighboring .env and launch github_activity.py with its arguments.

Requires only Python's standard library. Does not print credentials.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent


def load_env(path: Path) -> dict[str, str]:
    env = os.environ.copy()
    if not path.is_file():
        raise FileNotFoundError(f'.env not found: {path}')
    for number, raw in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:].strip()
        if '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        if value.startswith(('"', "'")) and value.endswith(value[0]) and len(value) >= 2:
            value = value[1:-1]
        if key:
            env[key] = value
    return env


def main() -> int:
    script = BASE / 'github_activity.py'
    if not script.is_file():
        print(f'[ERROR] Missing {script.name}', file=sys.stderr)
        return 1
    try:
        env = load_env(BASE / '.env')
    except (OSError, UnicodeError) as exc:
        print(f'[ERROR] Could not read .env: {exc}', file=sys.stderr)
        return 1
    if not env.get('OPENAI_API_KEY', '').strip():
        print('[ERROR] OPENAI_API_KEY is empty or missing in .env', file=sys.stderr)
        return 1
    print('[OK] OPENAI_API_KEY loaded from .env (key hidden)', flush=True)
    result = subprocess.run([sys.executable, str(script), *sys.argv[1:]], cwd=BASE, env=env, check=False)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
