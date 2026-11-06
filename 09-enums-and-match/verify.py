"""Chapter 9 checks. Run: python 09-enums-and-match/verify.py"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(9)

import syntax_enums as se  # noqa: E402
from eval_enums import run  # noqa: E402
from exhaustive import missing  # noqa: E402
from lexer import CompileError, lex  # noqa: E402
from parser_enums import EnumParser  # noqa: E402

PRELUDE = "enum Shape { Circle(Int), Rect(Int, Int), Dot } enum Light { Red, Yellow, Green } "


def bad(src: str, fragment: str) -> CompileError:
    try:
        run(PRELUDE + src)
    except CompileError as e:
        assert fragment in e.message or fragment in (e.help or ""), (src, e.message, e.help)
        return e
    raise AssertionError(f"{src!r} should be rejected")


def pat(src: str) -> object:
    parser = EnumParser(lex(src))
    return parser.parse_pattern()


def main() -> None:
    # Parsing.
    p = pat("Rect(w, 0)")
    assert isinstance(p, se.PCtor) and p.name == "Rect" and isinstance(p.args[0], se.PVar) and isinstance(p.args[1], se.PLit)
    assert isinstance(pat("Dot"), se.PCtor) and isinstance(pat("x"), se.PVar) and isinstance(pat("_"), se.PWild)

    # Evaluating.
    assert run(PRELUDE + "fn main() { print(Circle(3)); print(Dot); print(Rect(1, 2)); }") == ["Circle(3)", "Dot", "Rect(1, 2)"]
    src = PRELUDE + """
    fn area(s: Shape) -> Int { match s { Circle(r) => 3 * r * r, Rect(w, h) => w * h, Dot => 0 } }
    fn next(l: Light) -> Light { match l { Red => Green, Green => Yellow, Yellow => Red } }
    fn sign(n: Int) -> Int { match n { 0 => 0, 1 => 1, _ => if n < 0 { -1 } else { 1 } } }
    fn yes(b: Bool) -> Int { match b { true => 1, false => 0 } }
    fn pair(a: Bool, b: Bool) -> Int { match a { true => match b { true => 3, false => 2 }, false => 1 } }
    fn main() {
        print(area(Circle(2))); print(area(Rect(3, 4))); print(area(Dot));
        print(next(Red)); print(next(next(Red)));
        print(sign(-7)); print(sign(0)); print(sign(5));
        print(yes(true) + yes(false));
        print(pair(true, false));
        let s = Rect(2, 5);
        print(match s { Rect(w, h) => w + h, _ => 0 });
    }
    """
    assert run(src) == ["12", "12", "0", "Green", "Yellow", "-1", "0", "1", "1", "2", "7"]

    # Exhaustiveness, with a witness for what is missing.
    families = {"Circle": [("Circle", 1), ("Rect", 2), ("Dot", 0)], "Rect": [("Circle", 1), ("Rect", 2), ("Dot", 0)],
                "Dot": [("Circle", 1), ("Rect", 2), ("Dot", 0)]}  # fmt: skip
    assert missing([se.PCtor(0, "Circle", [se.PWild(0)]), se.PCtor(0, "Dot", [])], families) == "Rect(_, _)"
    assert missing([se.PWild(0)], families) is None
    assert missing([se.PLit(0, True)], {}) == "false"
    assert missing([se.PLit(0, 1), se.PLit(0, 2)], {}) == "_"

    bad("fn f(l: Light) -> Int { match l { Red => 1, Yellow => 2 } }", "non-exhaustive")
    e = bad("fn f(l: Light) -> Int { match l { Red => 1, Yellow => 2 } }", "Green")
    assert "pattern `Green` is not covered" in (e.help or "")
    bad("fn f(s: Shape) -> Int { match s { Circle(_) => 1 } }", "non-exhaustive")
    bad("fn f(n: Int) -> Int { match n { 1 => 1, 2 => 2 } }", "non-exhaustive")
    bad("fn f(b: Bool) -> Int { match b { true => 1 } }", "non-exhaustive")

    # Type errors around enums.
    bad("fn f() -> Int { Circle(1) }", "should return `Int`")
    bad("fn f() -> Shape { Circle(true) }", "expected `Int`, found `Bool`")
    bad("fn f() -> Shape { Circle() }", "takes 1 argument")
    bad("fn f() -> Shape { Circle }", "needs 1 argument")
    bad("fn f(s: Shape) -> Int { match s { Triangle(x) => 1, _ => 0 } }", "cannot find variant `Triangle`")
    bad("fn f(s: Shape) -> Int { match s { Circle(a, b) => 1, _ => 0 } }", "has 1 field(s) but the pattern has 2")
    bad("fn f(s: Shape) -> Int { match s { Red => 1, _ => 0 } }", "expected `Shape`, found `Light`")
    bad("fn f(n: Int) -> Int { match n { true => 1, _ => 0 } }", "expected `Int`, found `Bool`")
    bad("fn f(s: Shape) -> Int { match s { Dot => 1, _ => true } }", "different types")
    bad("fn f(a: Shape, b: Shape) -> Bool { a == b }", "cannot compare `Shape`")
    bad("enum A { X } enum B { X } fn main() { }", "defined more than once")

    # Everything from earlier chapters still works through the extended pipeline.
    assert run("fn fib(n: Int) -> Int { if n < 2 { n } else { fib(n - 1) + fib(n - 2) } } fn main() { print(fib(12)); }") == ["144"]
    print("chapter 9 ok")


if __name__ == "__main__":
    main()
