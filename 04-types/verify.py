"""Chapter 4 checks. Run: python 04-types/verify.py"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(4)

from checker import check  # noqa: E402
from lexer import CompileError  # noqa: E402
from parser import parse  # noqa: E402


def ok(src: str) -> dict[str, tuple[list[str], str]]:
    return check(parse(src))


def bad(src: str, fragment: str) -> CompileError:
    try:
        check(parse(src))
    except CompileError as e:
        assert fragment in e.message, (src, e.message)
        return e
    raise AssertionError(f"{src!r} should not type-check")


def main() -> None:
    sigs = ok("fn add(a: Int, b: Int) -> Int { a + b } fn main() { print(add(1, 2)); }")
    assert sigs == {"add": (["Int", "Int"], "Int"), "main": ([], "Unit")}

    ok("fn f(n: Int) -> Int { if n < 1 { return 0; } n }")  # `return` has type Never, which fits
    ok("fn f() -> Bool { let b = 1 < 2; b && !b }")
    ok("fn f() -> Int { let mut x = 1; x = x + 1; x }")
    ok("fn f(a: Bool, b: Bool) -> Bool { a == b }")
    ok("fn main() { print(later()); } fn later() -> Int { 1 }")  # use before definition
    ok("fn f() { while true { } }")

    bad("fn f() -> Int { true }", "should return `Int`")
    bad("fn f() { 1 + true; }", "cannot apply `+` to `Int` and `Bool`")
    bad("fn f() { true + true; }", "needs Int operands")
    bad("fn f() { let x = 1; x = 2; }", "not `mut`")
    bad("fn f() { let mut x = 1; x = true; }", "expected `Int`, found `Bool`")
    bad("fn f() { if 1 { } }", "expected `Bool`, found `Int`")
    bad("fn f() { if true { 1 } }", "`if` without `else`")
    bad("fn f() -> Int { if true { 1 } else { false } }", "different types")
    bad("fn f() { while 1 { } }", "expected `Bool`")
    bad("fn f() { return 1; }", "expected `Unit`, found `Int`")
    bad("fn f(a: Int) { f(1, 2); }", "takes 1 argument")
    bad("fn f(a: Int) { f(true); }", "expected `Int`, found `Bool`")
    bad("fn f() { g(); }", "cannot find function `g`")
    bad("fn f() -> Int { y }", "cannot find `y`")
    bad("fn f(x: Float) { }", "unknown type `Float`")
    bad("fn f() { } fn f() { }", "defined more than once")
    bad("fn id[T](x: T) -> T { x }", "chapter 5")
    bad("fn f() { let x: Bool = 1; }", "expected `Bool`, found `Int`")

    # Unknown names carry the names in scope so chapter 8 can suggest a fix.
    e = bad("fn f(total: Int) -> Int { totl }", "cannot find `totl`")
    assert "total" in e.candidates  # type: ignore[attr-defined]

    # The type of a block with a diverging statement is Never, so it fits any return type.
    ok("fn f() -> Int { return 1; }")
    print("chapter 4 ok")


if __name__ == "__main__":
    main()
