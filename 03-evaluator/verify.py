"""Chapter 3 checks. Run: python 03-evaluator/verify.py"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(3)

from evaluator import run  # noqa: E402
from ops import INT_MAX, INT_MIN, RunError, arith  # noqa: E402


def out(body: str, defs: str = "") -> list[str]:
    return run(defs + " fn main() { " + body + " }")


def raises(body: str, fragment: str, defs: str = "") -> None:
    try:
        out(body, defs)
    except RunError as e:
        assert fragment in e.message, (body, e.message)
    else:
        raise AssertionError(f"{body!r} should fail with {fragment!r}")


def main() -> None:
    assert out("print(1 + 2 * 3);") == ["7"]
    assert out("print(10 / 3); print(-10 / 3); print(10 % 3); print(-10 % 3);") == ["3", "-3", "1", "-1"]
    assert out("print(1 < 2 && 2 < 3); print(!true);") == ["true", "false"]
    assert out("let x = 5; { let x = 6; print(x); } print(x);") == ["6", "5"]
    assert out("let mut i = 0; let mut s = 0; while i < 5 { s = s + i; i = i + 1; } print(s);") == ["10"]
    assert out("print(if 1 < 2 { 10 } else { 20 });") == ["10"]
    assert out("print(if false { 1 } else if true { 2 } else { 3 });") == ["2"]
    assert out("print(g());", "fn g() { return 7; }") == ["7"]
    assert out("print(f(10));", "fn f(n: Int) -> Int { if n <= 0 { return 0; } n + f(n - 1) }") == ["55"]
    assert out("print({ 1; 2 });") == ["2"]
    assert out("print(());" if False else "print(h());", "fn h() { }") == ["()"]

    # Short-circuiting: the right side must not run when the left decides.
    defs = "fn boom() -> Bool { 1 / 0 == 0 }"
    assert out("print(false && boom()); print(true || boom());", defs) == ["false", "true"]

    # Fibonacci, the classic.
    fib = "fn fib(n: Int) -> Int { if n < 2 { n } else { fib(n - 1) + fib(n - 2) } }"
    assert out("print(fib(15));", fib) == ["610"]

    # Checked 64-bit arithmetic.
    assert out(f"print({INT_MAX} - 1 + 1);") == [str(INT_MAX)]
    raises(f"print({INT_MAX} + 1);", "integer overflow in `+`")
    raises(f"print(0 - {INT_MAX} - 2);", "integer overflow in `-`")
    raises("print(4611686018427387904 * 2);", "integer overflow in `*`")
    raises("print(-(0 - 9223372036854775807 - 1));", "integer overflow in `-`")
    raises("print(1 / 0);", "division by zero")
    raises("print(1 % 0);", "division by zero")
    raises("print(f(0));", "stack overflow", "fn f(n: Int) -> Int { f(n + 1) + 1 }")
    assert arith("/", INT_MIN, 1) == INT_MIN
    try:
        arith("/", INT_MIN, -1)
    except RunError as e:
        assert "overflow" in e.message
    else:
        raise AssertionError("INT_MIN / -1 must overflow")

    # Errors know where they happened.
    try:
        out("print(1 / 0);")
    except RunError as e:
        assert e.pos == (" fn main() { print(1 / 0); }").index("/")
    print("chapter 3 ok")


if __name__ == "__main__":
    main()
