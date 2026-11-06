"""Chapter 7: the virtual machine. A loop that executes the bytecode from chapter 6."""

from __future__ import annotations

from collections.abc import Callable

from bytecode import Chunk, Op
from ops import RunError, arith, checked, compare

MAX_DEPTH = 10_000

Value = int | bool | None

ARITH = {Op.ADD: "+", Op.SUB: "-", Op.MUL: "*", Op.DIV: "/", Op.MOD: "%"}
COMPARE = {Op.EQ: "==", Op.NE: "!=", Op.LT: "<", Op.LE: "<=", Op.GT: ">", Op.GE: ">="}


class Frame:
    """One function activation: which code, where we are in it, its locals and its operand stack."""

    __slots__ = ("chunk", "pc", "locals", "stack")

    def __init__(self, chunk: Chunk, args: list[Value]) -> None:
        self.chunk = chunk
        self.pc = 0
        self.locals: list[Value] = args + [None] * (chunk.nlocals - len(args))
        self.stack: list[Value] = []


class VM:
    def __init__(self, chunks: dict[str, Chunk], out: Callable[[str], None] = print) -> None:
        self.chunks = chunks
        self.out = out

    def run_main(self) -> Value:
        return self.run(self.chunks["main"])

    def run(self, entry: Chunk) -> Value:
        frames = [Frame(entry, [])]
        try:
            return self.loop(frames)
        except RunError as err:
            # Turn the frame stack into a stack trace; each frame's pc points just past the instruction.
            err.trace = [(f.chunk.name, f.chunk.pos[f.pc - 1]) for f in reversed(frames)]
            if err.pos < 0 and err.trace:
                err.pos = err.trace[0][1]
            raise

    def loop(self, frames: list[Frame]) -> Value:
        frame = frames[-1]
        while True:
            op, arg = frame.chunk.code[frame.pc]
            frame.pc += 1
            stack = frame.stack
            if op == Op.CONST:
                stack.append(arg)  # type: ignore[arg-type]
            elif op == Op.LOAD:
                stack.append(frame.locals[arg])  # type: ignore[index]
            elif op == Op.STORE:
                frame.locals[arg] = stack.pop()  # type: ignore[index]
            elif op == Op.POP:
                stack.pop()
            elif op in ARITH:
                b = stack.pop()
                a = stack.pop()
                assert isinstance(a, int) and isinstance(b, int)
                stack.append(arith(ARITH[op], a, b))
            elif op == Op.NEG:
                v = stack.pop()
                assert isinstance(v, int)
                stack.append(checked(-v, "-"))
            elif op == Op.NOT:
                stack.append(not stack.pop())
            elif op in COMPARE:
                b = stack.pop()
                a = stack.pop()
                assert isinstance(a, int) and isinstance(b, int)  # bools are ints in Python
                stack.append(compare(COMPARE[op], a, b))
            elif op == Op.JMP:
                frame.pc = arg  # type: ignore[assignment]
            elif op == Op.JMP_IF_FALSE:
                if not stack.pop():
                    frame.pc = arg  # type: ignore[assignment]
            elif op == Op.JMP_IF_FALSE_KEEP:
                if not stack[-1]:
                    frame.pc = arg  # type: ignore[assignment]
                else:
                    stack.pop()
            elif op == Op.JMP_IF_TRUE_KEEP:
                if stack[-1]:
                    frame.pc = arg  # type: ignore[assignment]
                else:
                    stack.pop()
            elif op == Op.CALL:
                name, n = arg  # type: ignore[misc]
                args = stack[len(stack) - n :]
                del stack[len(stack) - n :]
                if len(frames) >= MAX_DEPTH:
                    raise RunError(f"stack overflow (more than {MAX_DEPTH} nested calls)")
                frame = Frame(self.chunks[name], args)
                frames.append(frame)
            elif op == Op.RET:
                result = stack.pop()
                frames.pop()
                if not frames:
                    return result
                frame = frames[-1]
                frame.stack.append(result)
            elif op == Op.PRINT:
                self.out(self.show(stack.pop()))
            else:
                raise AssertionError(f"unknown opcode {op}")

    @staticmethod
    def show(v: Value) -> str:
        if v is None:
            return "()"
        if isinstance(v, bool):
            return "true" if v else "false"
        return str(v)


def run(text: str) -> list[str]:
    """Parse, compile and run a program on the VM; return the lines it printed."""
    from compiler import compile_program
    from parser import parse

    lines: list[str] = []
    VM(compile_program(parse(text)), lines.append).run_main()
    return lines
