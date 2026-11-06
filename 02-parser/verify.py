"""Chapter 2 checks. Run: python 02-parser/verify.py"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(2)

import syntax as s  # noqa: E402
from dump import dump  # noqa: E402
from lexer import CompileError  # noqa: E402
from parser import parse  # noqa: E402


def body(src: str) -> str:
    return dump(parse("fn f() { " + src + " }").fns[0].body)


def main() -> None:
    # Precedence and associativity.
    assert body("1 + 2 * 3") == "{=> (+ 1 (* 2 3))}"
    assert body("1 - 2 - 3") == "{=> (- (- 1 2) 3)}"
    assert body("(1 + 2) * 3") == "{=> (* (+ 1 2) 3)}"
    assert body("a || b && c") == "{=> (|| a (&& b c))}"
    assert body("a < b == c < d") == "{=> (== (< a b) (< c d))}"
    assert body("-a * b") == "{=> (* (- a) b)}"
    assert body("!a && b") == "{=> (&& (! a) b)}"
    assert body("f(1, g(2), 3 + 4)") == "{=> (f 1 (g 2) (+ 3 4))}"

    # Statements and tail expressions.
    assert body("let x = 1; x") == "{(let x 1); => x}"
    assert body("let mut x = 1; x = x + 1;") == "{(let mut x 1); (set x (+ x 1))}"
    assert body("while a { b; }") == "{(while a {b})}"
    assert body("return 1;") == "{(return 1)}"
    assert body("if a { 1 } else if b { 2 } else { 3 }") == "{=> (if a {=> 1} (if b {=> 2} {=> 3}))}"
    assert body("if a { f(); } g()") == "{(if a {(f)}); => (g)}"

    prog = parse("fn id[T](x: T) -> T { x } fn main() {}")
    assert [f.name for f in prog.fns] == ["id", "main"]
    assert prog.fns[0].tparams == ["T"] and prog.fns[0].ret is not None

    # Positions point into the source.
    src = "fn f() { 10 + 20 }"
    expr = parse(src).fns[0].body.tail
    assert isinstance(expr, s.Binary) and src[expr.pos] == "+"

    # Errors carry the offset of the offending token.
    for bad, pos in [
        ("fn f() { let x = ; }", 17),
        ("fn f() { 1 + }", 13),
        ("fn f( { }", 6),
        ("let x = 1;", 0),
        ("fn f() { 1 2 }", 11),
        ("fn f() {", 7),
    ]:
        try:
            parse(bad)
        except CompileError as e:
            assert e.pos == pos, (bad, e.pos, e.message)
        else:
            raise AssertionError(f"{bad!r} should not parse")
    print("chapter 2 ok")


if __name__ == "__main__":
    main()
