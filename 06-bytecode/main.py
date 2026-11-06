"""Chapter 6 demo: compile a program and print the bytecode."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(6)

from compiler import compile_program, show  # noqa: E402
from parser import parse  # noqa: E402

SOURCE = """\
fn fib(n: Int) -> Int {
    if n < 2 { n } else { fib(n - 1) + fib(n - 2) }
}

fn count(limit: Int) -> Int {
    let mut i = 0;
    while i < limit { i = i + 1; }
    i
}
"""

if __name__ == "__main__":
    print(show(compile_program(parse(SOURCE))))
