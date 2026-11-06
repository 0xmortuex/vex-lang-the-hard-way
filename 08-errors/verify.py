"""Chapter 8 checks. Run: python 08-errors/verify.py"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(8)

import vm  # noqa: E402
from diagnostics import Source, diagnose, render, render_runtime_error, suggest  # noqa: E402
from ops import RunError  # noqa: E402


def main() -> None:
    # Offsets become line:column, tabs and multiple lines included.
    src = Source("f.vx", "ab\ncd\n\nef")
    assert src.line_col(0) == (1, 1)
    assert src.line_col(4) == (2, 2)
    assert src.line_col(7) == (4, 1)
    assert src.line_text(2) == "cd"

    # A rendered error has the location, the line and a caret under the right column.
    text = render(Source("f.vx", "fn f() {\n    oops\n}\n"), "error", "bad", 13, "try this")
    lines = text.splitlines()
    assert lines[0] == "error: bad"
    assert lines[1].endswith("--> f.vx:2:5")
    assert lines[3] == "2 |     oops"
    assert lines[4] == "  |     ^"
    assert lines[5].endswith("= help: try this")

    # Suggestions.
    assert suggest("totl", ["total", "count"]) == "total"
    assert suggest("zzz", ["total", "count"]) is None
    assert suggest("same", ["same"]) is None

    # No problems, no output.
    assert diagnose("fn main() { print(1); }") == []

    # One mistake, one error, pointing at the right place.
    out = diagnose("fn main() {\n    let total = 1;\n    print(totl);\n}\n", "t.vx")
    assert len(out) == 1
    assert "t.vx:3:11" in out[0] and "did you mean `total`?" in out[0]

    # Several syntax errors are reported in one go (the parser resynchronises).
    out = diagnose("fn main() {\n    let a = ;\n    let b = 2;\n    let c = 3 +;\n}\n")
    assert len(out) == 2 and "2:13" in out[0] and "4:16" in out[1]

    # ...even across functions, and a broken function does not hide the next one.
    out = diagnose("fn a( { }\nfn b() { let x = ; }\nfn main() { }\n")
    assert len(out) == 2, out

    # Several type errors are reported too, one per function at most, in source order.
    out = diagnose(
        "fn a() -> Int { true }\n"
        "fn b() -> Bool { 1 }\n"
        "fn c() { zzz; }\n"
        "fn fine() -> Int { 1 }\n"
    )
    assert len(out) == 3
    assert "a" in out[0] and "should return `Int`" in out[0]
    assert "should return `Bool`" in out[1] and "cannot find `zzz`" in out[2]

    # A function that failed to type-check does not cause follow-up errors in its callers.
    out = diagnose("fn bad() { 1 + true; }\nfn main() { bad(); }\n")
    assert len(out) == 1, out

    # Lexical errors are reported too.
    out = diagnose("fn main() { let x = 3 $ 4; }")
    assert len(out) == 1 and "unexpected character" in out[0]

    # Runtime errors get the same treatment, plus a stack trace.
    prog = "fn inner(n: Int) -> Int { 10 / n }\nfn main() {\n    print(inner(0));\n}\n"
    try:
        vm.run(prog)
    except RunError as e:
        text = render_runtime_error(Source("p.vx", prog), e)
        assert "runtime error: division by zero" in text
        assert "p.vx:1:30" in text
        assert "in inner at p.vx:1:30" in text and "in main at p.vx:3:11" in text
    else:
        raise AssertionError("expected a runtime error")

    # Garbage never produces a Python traceback, only diagnostics.
    for junk in ["fn f() { fn }", "}}}}", "fn", "fn f(", "((((", "fn f() { { { {", "fn f() { let }", "fn 1() {}", "@@@"]:
        diagnose(junk)
    print("chapter 8 ok")


if __name__ == "__main__":
    main()
