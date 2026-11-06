"""Run every chapter's verify.py (and its main.py demo) in a fresh interpreter, the way CI does.

Usage: python verify.py            # all chapters
       python verify.py 03 07      # just these
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def run(script: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", cwd=ROOT, timeout=300
    )


def main(argv: list[str]) -> int:
    chapters = sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name[:2].isdigit())
    if argv:
        chapters = [c for c in chapters if c.name[:2] in argv]
    failed = 0
    for chapter in chapters:
        for script in ("verify.py", "main.py"):
            res = run(chapter / script)
            ok = res.returncode == 0 and "Traceback" not in res.stderr
            label = "ok  " if ok else "FAIL"
            print(f"{label} {chapter.name}/{script}")
            if not ok:
                failed += 1
                print(res.stdout[-2000:])
                print(res.stderr[-3000:])
    print(f"\n{'all chapters verified' if not failed else f'{failed} failure(s)'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
