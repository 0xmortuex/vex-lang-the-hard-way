"""Chapter 7 checks. Run: python 07-vm/verify.py"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(7)

import evaluator  # noqa: E402
import vm  # noqa: E402
from ops import INT_MAX, RunError  # noqa: E402

PROGRAMS = [
    "fn main() { print(1 + 2 * 3); }",
    "fn main() { print(10 / 3); print(-10 / 3); print(10 % 3); print(-10 % 3); }",
    "fn main() { print(1 < 2 && 2 < 3); print(1 > 2 || 3 > 2); print(!true); print(1 == 1); print(true != false); }",
    "fn main() { let x = 5; { let x = 6; print(x); } print(x); }",
    "fn main() { let x = 1; let x = x + 1; let x = x * 10; print(x); }",
    "fn main() { let mut i = 0; let mut s = 0; while i < 10 { s = s + i; i = i + 1; } print(s); }",
    "fn main() { print(if 1 < 2 { 10 } else { 20 }); print(if false { 1 } else if true { 2 } else { 3 }); }",
    "fn f(n: Int) -> Int { if n <= 0 { return 0; } n + f(n - 1) } fn main() { print(f(100)); }",
    "fn fib(n: Int) -> Int { if n < 2 { n } else { fib(n - 1) + fib(n - 2) } } fn main() { print(fib(18)); }",
    "fn id(n: Int) -> Int { n } fn main() { print(id(id(id(4)))); }",
    "fn g() { print(1); } fn main() { g(); print(g()); }",
    "fn boom() -> Bool { print(99); true } fn main() { print(false && boom()); print(true || boom()); }",
    "fn gcd(a: Int, b: Int) -> Int { if b == 0 { a } else { gcd(b, a % b) } } fn main() { print(gcd(1071, 462)); }",
    "fn collatz(n: Int) -> Int { let mut steps = 0; let mut x = n; while x != 1 { if x % 2 == 0 { x = x / 2; } else { x = 3 * x + 1; } steps = steps + 1; } steps } fn main() { print(collatz(27)); }",
    "fn main() { let mut i = 0; while i < 3 { let k = i * i; print(k); i = i + 1; } }",
    "fn main() { print({ 1; 2; 3 }); }",
    f"fn main() {{ print({INT_MAX}); print(-{INT_MAX} - 1); }}",
]

FAILING = [
    ("fn main() { print(1 / 0); }", "division by zero"),
    ("fn main() { print(1 % 0); }", "division by zero"),
    (f"fn main() {{ print({INT_MAX} + 1); }}", "integer overflow in `+`"),
    (f"fn main() {{ print(-{INT_MAX} - 2); }}", "integer overflow in `-`"),
    ("fn main() { print(3037000500 * 3037000500); }", "integer overflow in `*`"),
    ("fn f(n: Int) -> Int { f(n + 1) + 1 } fn main() { print(f(0)); }", "stack overflow"),
    ("fn fact(n: Int) -> Int { if n <= 1 { 1 } else { n * fact(n - 1) } } fn main() { print(fact(25)); }", "overflow"),
]


def main() -> None:
    # The VM must agree with the tree walker on everything. This is differential testing in miniature.
    for src in PROGRAMS:
        assert vm.run(src) == evaluator.run(src), src
    assert vm.run("fn main() { print(1 + 2); }") == ["3"]

    for src, fragment in FAILING:
        for runner in (evaluator.run, vm.run):
            try:
                runner(src)
            except RunError as e:
                assert fragment in e.message, (src, e.message)
            else:
                raise AssertionError(f"{src!r} should fail")

    # A stack trace has one entry per active function, innermost first, with the offending offset.
    src = "fn inner(n: Int) -> Int { 10 / n }\nfn middle(n: Int) -> Int { inner(n) + 1 }\nfn main() { print(middle(0)); }\n"
    try:
        vm.run(src)
    except RunError as e:
        assert [name for name, _ in e.trace] == ["inner", "middle", "main"]
        assert src[e.trace[0][1]] == "/"
        assert src[e.trace[1][1]] == "i"  # the call `inner(n)`
        assert e.pos == e.trace[0][1]
    else:
        raise AssertionError("expected a runtime error")

    # Deep (but legal) recursion works on the VM: it does not use the Python stack.
    assert vm.run("fn s(n: Int) -> Int { if n == 0 { 0 } else { n + s(n - 1) } } fn main() { print(s(5000)); }") == ["12502500"]
    print("chapter 7 ok")


if __name__ == "__main__":
    main()
