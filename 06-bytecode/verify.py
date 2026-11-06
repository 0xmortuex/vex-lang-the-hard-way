"""Chapter 6 checks. Run: python 06-bytecode/verify.py"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(6)

from bytecode import Op  # noqa: E402
from compiler import compile_program  # noqa: E402
from parser import parse  # noqa: E402

JUMPS = {Op.JMP, Op.JMP_IF_FALSE, Op.JMP_IF_FALSE_KEEP, Op.JMP_IF_TRUE_KEEP}


def code(src: str, name: str = "f") -> list[tuple[str, object]]:
    return [(op.name, arg) for op, arg in compile_program(parse(src))[name].code]


def main() -> None:
    assert code("fn f(a: Int) -> Int { a + 1 }") == [("LOAD", 0), ("CONST", 1), ("ADD", None), ("RET", None)]
    assert code("fn f() -> Int { 1 + 2 * 3 }") == [
        ("CONST", 1), ("CONST", 2), ("CONST", 3), ("MUL", None), ("ADD", None), ("RET", None),
    ]  # fmt: skip
    assert code("fn f() { }") == [("CONST", None), ("RET", None)]
    assert code("fn f() { let x = 5; x }") == [("CONST", 5), ("STORE", 0), ("LOAD", 0), ("RET", None)]
    assert code("fn f(b: Bool) { !b }")[:2] == [("LOAD", 0), ("NOT", None)]
    assert code("fn f() -> Int { -3 }")[:2] == [("CONST", 3), ("NEG", None)]
    assert code("fn f(n: Int) -> Int { g(n, 2) }")[:3] == [("LOAD", 0), ("CONST", 2), ("CALL", ("g", 2))]

    # An expression statement pushes a value and then pops it again.
    assert code("fn f() { 1; 2 }") == [("CONST", 1), ("POP", None), ("CONST", 2), ("RET", None)]

    # `if` compiles to a conditional jump over the then-branch, and an unconditional jump over the else.
    ops = code("fn f(c: Bool) -> Int { if c { 1 } else { 2 } }")
    assert [o for o, _ in ops] == ["LOAD", "JMP_IF_FALSE", "CONST", "JMP", "CONST", "RET"]
    assert ops[1][1] == 4 and ops[3][1] == 5  # type: ignore[comparison-overlap]

    # `while` jumps back to the condition.
    ops = code("fn f() { let mut i = 0; while i < 3 { i = i + 1; } }")
    names = [o for o, _ in ops]
    assert "JMP" in names and ops[names.index("JMP")][1] == 2

    # && and || short-circuit through the *_KEEP jumps.
    names = [o for o, _ in code("fn f(a: Bool, b: Bool) -> Bool { a && b }")]
    assert names == ["LOAD", "JMP_IF_FALSE_KEEP", "LOAD", "RET"]
    names = [o for o, _ in code("fn f(a: Bool, b: Bool) -> Bool { a || b }")]
    assert names == ["LOAD", "JMP_IF_TRUE_KEEP", "LOAD", "RET"]

    # Shadowing gets a fresh slot, and the initialiser sees the old variable.
    assert code("fn f(x: Int) -> Int { let x = x + 1; x }") == [
        ("LOAD", 0), ("CONST", 1), ("ADD", None), ("STORE", 1), ("LOAD", 1), ("RET", None),
    ]  # fmt: skip

    chunks = compile_program(parse("fn f(a: Int, b: Int) { let c = a; let d = b; }"))
    assert chunks["f"].nparams == 2 and chunks["f"].nlocals == 4

    # Structural invariants over a bigger program: every function ends in RET, jumps stay in range.
    big = """
    fn fib(n: Int) -> Int { if n < 2 { n } else { fib(n - 1) + fib(n - 2) } }
    fn main() { let mut i = 0; while i < 10 && i != 7 { print(fib(i)); i = i + 1; } }
    """
    for chunk in compile_program(parse(big)).values():
        assert chunk.code[-1][0] == Op.RET
        assert len(chunk.pos) == len(chunk.code)
        for op, arg in chunk.code:
            if op in JUMPS:
                assert isinstance(arg, int) and 0 <= arg <= len(chunk.code)
    print("chapter 6 ok")


if __name__ == "__main__":
    main()
