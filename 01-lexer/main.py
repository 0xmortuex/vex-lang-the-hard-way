"""Chapter 1 demo: print the tokens of a small program."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(1)

from lexer import LexError, lex  # noqa: E402

SOURCE = """\
fn fib(n: Int) -> Int {
    if n < 2 { n } else { fib(n - 1) + fib(n - 2) }  // recursion
}
"""

if __name__ == "__main__":
    tokens = lex(SOURCE)
    for t in tokens:
        print(f"{t.pos:3d}  {t.kind:<6} {t.text!r}")
    # The lexer rejects characters that are not part of the language.
    try:
        lex("let x = 3 $ 4;")
    except LexError as e:
        print(f"error at offset {e.pos}: {e.message}")
