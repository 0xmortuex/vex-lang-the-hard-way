"""Makes the code of chapters 1..N importable, newest chapter first.

Each chapter adds new files (or ships an upgraded version of an old one). A chapter's
`main.py` and `verify.py` call `setup(N)` so that `import lexer` finds chapter 1's lexer
unless a later chapter replaced it.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent


def chapter_dirs() -> list[pathlib.Path]:
    return sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name[:2].isdigit())


def setup(upto: int) -> None:
    dirs = [str(p) for p in chapter_dirs() if int(p.name[:2]) <= upto]
    for d in dirs:
        while d in sys.path:
            sys.path.remove(d)
    sys.path[:0] = list(reversed(dirs))
