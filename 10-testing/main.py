"""Chapter 10 demo: differential testing, a generated program, fuzzing."""

import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(10)

from diagnostics import diagnose  # noqa: E402
from golden_runner import check_golden  # noqa: E402
from testing import Gen, mutate, run_both  # noqa: E402

if __name__ == "__main__":
    print("a generated program:")
    print(Gen(random.Random(3)).program())
    print()

    agree = errors = 0
    for seed in range(200):
        src = Gen(random.Random(seed)).program()
        walker, machine = run_both(src)
        assert walker == machine, (seed, src, walker, machine)
        agree += 1
        errors += walker[1] is not None
    print(f"tree walker and VM agree on {agree} random programs ({errors} of them end in a runtime error)")

    names = check_golden()
    print("golden files passed:", ", ".join(names))

    base = Gen(random.Random(1)).program()
    clean = sum(1 for seed in range(300) if not diagnose(mutate(random.Random(seed), base)))
    print(f"fuzzed 300 mangled programs: no Python tracebacks ({clean} of them still compile)")
