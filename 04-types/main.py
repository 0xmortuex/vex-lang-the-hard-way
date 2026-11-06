"""Chapter 4 demo: type-check programs, good and bad."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(4)

from checker import check  # noqa: E402
from lexer import CompileError  # noqa: E402
from parser import parse  # noqa: E402

GOOD = """\
fn fib(n: Int) -> Int { if n < 2 { n } else { fib(n - 1) + fib(n - 2) } }
fn even(n: Int) -> Bool { n % 2 == 0 }
fn main() { let mut i = 0; while i < 3 { print(fib(i)); i = i + 1; } }
"""

BAD = [
    "fn f() -> Int { true }",
    "fn f(n: Int) -> Bool { n + 1 }",
    "fn f() { let x = 1; x = 2; }",
    "fn f() { if 1 { } }",
    "fn f() -> Int { g(1) } fn g() -> Int { 1 }",
    "fn f() -> Int { y }",
]

if __name__ == "__main__":
    for name, (params, ret) in check(parse(GOOD)).items():
        print(f"{name}({', '.join(params)}) -> {ret}")
    print()
    for src in BAD:
        try:
            check(parse(src))
        except CompileError as e:
            print(f"{src!r}\n    offset {e.pos}: {e.message}")
