"""Chapter 10 checks. Run: python 10-testing/verify.py"""

import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(10)

from diagnostics import diagnose  # noqa: E402
from golden_runner import check_golden  # noqa: E402
from infer import check  # noqa: E402
from parser import parse  # noqa: E402
from testing import Gen, mutate, run_both  # noqa: E402

SEEDS = 300


def main() -> None:
    # 1. Every generated program is well-typed, and both implementations agree on it
    #    (same output, same error message when one fails: overflow, division by zero ...).
    errors = 0
    outputs = 0
    for seed in range(SEEDS):
        src = Gen(random.Random(seed)).program()
        check(parse(src))  # the generator only makes programs the type checker accepts
        walker, machine = run_both(src)
        assert walker == machine, f"seed {seed} disagrees:\n{src}\nwalker={walker}\nvm={machine}"
        errors += walker[1] is not None
        outputs += len(walker[0])
    assert outputs > SEEDS  # the programs really print things
    assert 0 < errors < SEEDS  # some fail at run time, most do not: both paths are exercised

    # 2. The golden files (also runs the enum evaluator).
    passed = check_golden()
    assert passed == ["fib", "gcd", "overflow", "primes", "shapes"], passed

    # 3. Fuzzing: mangled programs give diagnostics or compile, but never raise anything else.
    seeds_ok = 0
    for seed in range(SEEDS):
        rng = random.Random(1000 + seed)
        base = Gen(rng).program()
        text = mutate(rng, base)
        try:
            diagnose(text)
        except Exception as e:  # noqa: BLE001
            raise AssertionError(f"seed {seed} crashed the front end with {type(e).__name__}: {e}\n{text}") from e
        seeds_ok += 1
    assert seeds_ok == SEEDS

    # 4. The generator is deterministic for a given seed (so a failing seed can be replayed).
    assert Gen(random.Random(5)).program() == Gen(random.Random(5)).program()
    print("chapter 10 ok")


if __name__ == "__main__":
    main()
