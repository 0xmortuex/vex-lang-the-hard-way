"""Chapter 3: Vex's integer semantics, in one place, shared by the evaluator and (chapter 7) the VM.

Int is a signed 64-bit integer. Arithmetic never wraps: an out-of-range result is a runtime error.
Division truncates toward zero and the remainder takes the sign of the left operand.
"""

from __future__ import annotations

INT_MIN = -(2**63)
INT_MAX = 2**63 - 1


class RunError(Exception):
    """A runtime error: message plus the source offset of the operation that failed."""

    def __init__(self, message: str, pos: int = -1) -> None:
        super().__init__(message)
        self.message = message
        self.pos = pos
        self.trace: list[tuple[str, int]] = []  # (function name, source offset), innermost first; the VM fills it


def checked(r: int, op: str) -> int:
    if r > INT_MAX or r < INT_MIN:
        raise RunError(f"integer overflow in `{op}`")
    return r


def arith(op: str, a: int, b: int) -> int:
    if op == "+":
        return checked(a + b, op)
    if op == "-":
        return checked(a - b, op)
    if op == "*":
        return checked(a * b, op)
    if b == 0:
        raise RunError("division by zero")
    q = abs(a) // abs(b)  # Python's // floors; Vex truncates toward zero
    if op == "/":
        return checked(-q if (a < 0) != (b < 0) else q, op)
    if op == "%":
        r = abs(a) % abs(b)
        return -r if a < 0 else r
    raise AssertionError(op)


def compare(op: str, a: int, b: int) -> bool:
    return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b, "==": a == b, "!=": a != b}[op]
