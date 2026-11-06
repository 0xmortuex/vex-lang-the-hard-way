"""Chapter 7 demo: run the same program on the tree walker and on the VM, and time both."""

import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(7)

import evaluator  # noqa: E402
import vm  # noqa: E402
from ops import RunError  # noqa: E402

FIB = """\
fn fib(n: Int) -> Int { if n < 2 { n } else { fib(n - 1) + fib(n - 2) } }
fn main() { print(fib(22)); }
"""

BOOM = """\
fn inner(n: Int) -> Int { 10 / n }
fn middle(n: Int) -> Int { inner(n) + 1 }
fn main() { print(middle(0)); }
"""

if __name__ == "__main__":
    for name, mod in [("tree walker", evaluator), ("bytecode VM", vm)]:
        start = time.perf_counter()
        out = mod.run(FIB)
        print(f"{name:12} fib(22) = {out[0]}   {time.perf_counter() - start:.2f}s")
    try:
        vm.run(BOOM)
    except RunError as e:
        print(f"runtime error: {e.message}")
        for fn, pos in e.trace:
            print(f"  in {fn} at offset {pos}")
