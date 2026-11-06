"""Chapter 2 demo: parse a program and show the tree."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(2)

from dump import dump  # noqa: E402
from lexer import CompileError  # noqa: E402
from parser import parse  # noqa: E402

SOURCE = """\
fn fib(n: Int) -> Int {
    if n < 2 { n } else { fib(n - 1) + fib(n - 2) }
}

fn main() {
    let mut total = 0;
    let mut i = 0;
    while i < 5 { total = total + fib(i); i = i + 1; }
    print(total * 2 + 1);
}
"""

if __name__ == "__main__":
    print(dump(parse(SOURCE)))
    print()
    print("precedence:", dump(parse("fn f() { 1 + 2 * 3 - 4 }").fns[0].body))
    try:
        parse("fn f() { let x = ; }")
    except CompileError as e:
        print(f"error at offset {e.pos}: {e.message}")
