"""Chapter 5 checks. Run: python 05-inference/verify.py"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(5)

from infer import BOOL, INT, TVar, Mismatch, check, prune, unify  # noqa: E402
from lexer import CompileError  # noqa: E402
from parser import parse  # noqa: E402


def sigs(src: str) -> list[str]:
    return [sig.show() for sig in check(parse(src)).values()]


def bad(src: str, fragment: str) -> None:
    try:
        check(parse(src))
    except CompileError as e:
        assert fragment in e.message, (src, e.message)
        return
    raise AssertionError(f"{src!r} should not type-check")


def main() -> None:
    # Unification itself.
    a, b = TVar(), TVar()
    unify(a, b)
    unify(b, INT)
    assert prune(a) is INT
    try:
        unify(INT, BOOL)
    except Mismatch:
        pass
    else:
        raise AssertionError("Int and Bool must not unify")

    # Inferred return types.
    assert sigs("fn double(n: Int) { n * 2 }") == ["double(Int) -> Int"]
    assert sigs("fn f(n: Int) { n < 3 }") == ["f(Int) -> Bool"]
    assert sigs("fn f() { }") == ["f() -> Unit"]
    assert sigs("fn fib(n: Int) { if n < 2 { n } else { fib(n - 1) + fib(n - 2) } }") == ["fib(Int) -> Int"]
    assert sigs("fn f(n: Int) { if n == 0 { return true; } false }") == ["f(Int) -> Bool"]

    # Functions may be used before they are defined, with return types still inferred.
    assert sigs("fn main() { print(double(2)); } fn double(n: Int) { n * 2 }") == ["main() -> Unit", "double(Int) -> Int"]
    # Mutual recursion: one side declares its type, the other is inferred.
    assert sigs(
        "fn even(n: Int) { if n == 0 { true } else { odd(n - 1) } }"
        "fn odd(n: Int) -> Bool { if n == 0 { false } else { even(n - 1) } }"
    ) == ["even(Int) -> Bool", "odd(Int) -> Bool"]

    # Generics: each call instantiates the type parameters afresh.
    assert sigs("fn id[T](x: T) -> T { x }") == ["id[T](T) -> T"]
    check(parse("fn id[T](x: T) -> T { x } fn main() { print(id(1)); print(id(true)); let b = id(false); if b { } }"))
    check(parse("fn pick[T](c: Bool, a: T, b: T) -> T { if c { a } else { b } } fn main() { print(pick(true, 1, 2)); }"))
    assert sigs("fn id[T](x: T) -> T { x } fn f() { id(id(3)) }") == ["id[T](T) -> T", "f() -> Int"]

    bad("fn pick[T](a: T, b: T) -> T { a } fn main() { pick(1, true); }", "expected `Int`, found `Bool`")
    bad("fn add_one[T](x: T) -> T { x + 1 }", "cannot apply `+` to `T` and `Int`")
    bad("fn f[T](x: T) -> Int { x }", "should return `Int` but its body has type `T`")
    bad("fn f[T](x: T) { f(x) }", "recursive generic function")
    bad("fn id[T](x: T) -> T { x } fn g() -> Bool { id(1) }", "should return `Bool` but its body has type `Int`")
    bad("fn f() -> Int { true }", "should return `Int`")
    bad("fn f(x: Q) { }", "unknown type `Q`")
    bad("fn f() { 1 + true; }", "cannot apply `+`")

    # Everything chapter 4 accepted is still accepted.
    check(parse("fn f(n: Int) -> Int { if n < 1 { return 0; } let mut x = n; while x > 0 { x = x - 1; } x }"))
    print("chapter 5 ok")


if __name__ == "__main__":
    main()
