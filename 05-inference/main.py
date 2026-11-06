"""Chapter 5 demo: inferred return types and generic functions."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(5)

from infer import check  # noqa: E402
from lexer import CompileError  # noqa: E402
from parser import parse  # noqa: E402

PROGRAM = """\
fn double(n: Int) { n * 2 }                         // return type inferred: Int
fn is_even(n: Int) { n % 2 == 0 }                   // Bool
fn fib(n: Int) { if n < 2 { n } else { fib(n - 1) + fib(n - 2) } }   // recursion is fine
fn id[T](x: T) -> T { x }                           // generic
fn pick[T](first: Bool, a: T, b: T) -> T { if first { a } else { b } }
fn main() {
    print(id(5));
    print(id(true));
    print(pick(false, 1, 2));
    print(double(fib(10)));
}
"""

BAD = [
    "fn pick[T](a: T, b: T) -> T { a } fn main() { pick(1, true); }",
    "fn add_one[T](x: T) -> T { x + 1 }",
    "fn f[T](x: T) { f(x) }",
    "fn main() { let x = id(1); } fn id[T](x: T) -> T { x } fn g() -> Bool { id(1) }",
]

if __name__ == "__main__":
    for sig in check(parse(PROGRAM)).values():
        print(sig.show())
    print()
    for src in BAD:
        try:
            check(parse(src))
        except CompileError as e:
            print(f"{src}\n    offset {e.pos}: {e.message}")
