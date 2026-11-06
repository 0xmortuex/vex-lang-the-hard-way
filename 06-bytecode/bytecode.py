"""Chapter 6: the instruction set and the code container."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class Op(IntEnum):
    CONST = 0  # push arg
    LOAD = 1  # push local[arg]
    STORE = 2  # local[arg] = pop
    POP = 3
    ADD = 4
    SUB = 5
    MUL = 6
    DIV = 7
    MOD = 8
    NEG = 9
    NOT = 10
    EQ = 11
    NE = 12
    LT = 13
    LE = 14
    GT = 15
    GE = 16
    JMP = 17  # pc = arg
    JMP_IF_FALSE = 18  # pop; jump if false
    JMP_IF_FALSE_KEEP = 19  # if top is false jump (keeping it), else pop   (for &&)
    JMP_IF_TRUE_KEEP = 20  # if top is true jump (keeping it), else pop     (for ||)
    CALL = 21  # arg = (function name, argument count)
    RET = 22  # return the top of the stack
    PRINT = 23  # pop and print


@dataclass
class Chunk:
    """The compiled form of one function."""

    name: str
    nparams: int
    nlocals: int = 0
    code: list[tuple[Op, object]] = field(default_factory=list)
    pos: list[int] = field(default_factory=list)  # source offset for each instruction (error messages!)


def disassemble(chunk: Chunk) -> str:
    lines = [f"== {chunk.name} (params={chunk.nparams}, locals={chunk.nlocals}) =="]
    for i, (op, arg) in enumerate(chunk.code):
        shown = "" if arg is None else repr(arg) if op != Op.CALL else f"{arg[0]}/{arg[1]}"  # type: ignore[index]
        if op in (Op.JMP, Op.JMP_IF_FALSE, Op.JMP_IF_FALSE_KEEP, Op.JMP_IF_TRUE_KEEP):
            shown = f"-> {arg:04d}"
        lines.append(f"  {i:04d}  {op.name:<18} {shown}".rstrip())
    return "\n".join(lines)
