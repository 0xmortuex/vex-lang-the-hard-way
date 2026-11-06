"""Chapter 3 demo: run programs with the tree-walking interpreter."""

import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(3)

from evaluator import run  # noqa: E402
from ops import RunError  # noqa: E402

FIB = """\
fn fib(n: Int) -> Int {
    if n < 2 { n } else { fib(n - 1) + fib(n - 2) }
}
fn main() {
    let mut i = 0;
    while i <= 10 { print(fib(i)); i = i + 1; }
}
"""

FACTORIAL = """\
fn fact(n: Int) -> Int { if n <= 1 { 1 } else { n * fact(n - 1) } }
fn main() { print(fact(20)); print(fact(21)); }
"""

if __name__ == "__main__":
    print("fib 0..10:", run(FIB))
    try:
        run(FACTORIAL)
    except RunError as e:
        print(f"runtime error at offset {e.pos}: {e.message}")
    start = time.perf_counter()
    run("fn fib(n: Int) -> Int { if n < 2 { n } else { fib(n - 1) + fib(n - 2) } } fn main() { print(fib(20)); }")
    print(f"fib(20) took {time.perf_counter() - start:.2f}s in the tree walker")
