"""Chapter 6: compile the syntax tree to stack bytecode.

The one rule that makes this easy: **every expression leaves exactly one value on the stack.**
(Unit is the value `None`.) A statement that does not want the value follows it with POP.
"""

from __future__ import annotations

import syntax as s
from bytecode import Chunk, Op, disassemble

BINARY = {
    "+": Op.ADD, "-": Op.SUB, "*": Op.MUL, "/": Op.DIV, "%": Op.MOD,
    "==": Op.EQ, "!=": Op.NE, "<": Op.LT, "<=": Op.LE, ">": Op.GT, ">=": Op.GE,
}  # fmt: skip


class FnCompiler:
    def __init__(self, fn: s.Fn) -> None:
        self.chunk = Chunk(fn.name, len(fn.params))
        self.scopes: list[dict[str, int]] = [{}]  # name -> local slot, one dict per block
        for p in fn.params:
            self.declare(p.name)
        self.pos = fn.pos

    def declare(self, name: str) -> int:
        slot = self.chunk.nlocals  # every variable gets its own slot, even when shadowed
        self.chunk.nlocals += 1
        self.scopes[-1][name] = slot
        return slot

    def resolve(self, name: str) -> int:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise AssertionError(f"unknown variable {name}")  # the checker rules this out

    def emit(self, op: Op, arg: object = None) -> int:
        self.chunk.code.append((op, arg))
        self.chunk.pos.append(self.pos)
        return len(self.chunk.code) - 1

    def patch(self, at: int) -> None:
        """Point the jump at index `at` to the next instruction to be emitted."""
        op, _ = self.chunk.code[at]
        self.chunk.code[at] = (op, len(self.chunk.code))

    # ---------------------------------------------------------------- statements
    def block(self, b: s.Block, new_scope: bool = True) -> None:
        if new_scope:
            self.scopes.append({})
        for st in b.stmts:
            self.stmt(st)
        if b.tail is not None:
            self.expr(b.tail)
        else:
            self.emit(Op.CONST, None)
        if new_scope:
            self.scopes.pop()

    def stmt(self, st: s.Node) -> None:
        self.pos = st.pos
        if isinstance(st, s.Let):
            self.expr(st.init)  # compile the initialiser *before* declaring: `let x = x + 1` sees the old x
            self.emit(Op.STORE, self.declare(st.name))
        elif isinstance(st, s.Assign):
            self.expr(st.value)
            self.emit(Op.STORE, self.resolve(st.name))
        elif isinstance(st, s.While):
            top = len(self.chunk.code)
            self.expr(st.cond)
            exit_jump = self.emit(Op.JMP_IF_FALSE)
            self.block(st.body)
            self.emit(Op.POP)
            self.emit(Op.JMP, top)
            self.patch(exit_jump)
        elif isinstance(st, s.Return):
            if st.value is not None:
                self.expr(st.value)
            else:
                self.emit(Op.CONST, None)
            self.pos = st.pos
            self.emit(Op.RET)
        elif isinstance(st, s.ExprStmt):
            self.expr(st.expr)
            self.emit(Op.POP)
        else:
            raise AssertionError(f"unknown statement {st}")

    # ---------------------------------------------------------------- expressions
    def expr(self, e: s.Node) -> None:
        saved = self.pos
        self.pos = e.pos
        self.expr_inner(e)
        self.pos = saved

    def expr_inner(self, e: s.Node) -> None:
        if isinstance(e, s.Num):
            self.emit(Op.CONST, e.value)
        elif isinstance(e, s.BoolLit):
            self.emit(Op.CONST, e.value)
        elif isinstance(e, s.Var):
            self.emit(Op.LOAD, self.resolve(e.name))
        elif isinstance(e, s.Unary):
            self.expr(e.operand)
            self.emit(Op.NOT if e.op == "!" else Op.NEG)
        elif isinstance(e, s.Binary):
            if e.op in ("&&", "||"):
                self.expr(e.left)
                jump = self.emit(Op.JMP_IF_FALSE_KEEP if e.op == "&&" else Op.JMP_IF_TRUE_KEEP)
                self.expr(e.right)
                self.patch(jump)
            else:
                self.expr(e.left)
                self.expr(e.right)
                self.emit(BINARY[e.op])
        elif isinstance(e, s.Call):
            for a in e.args:
                self.expr(a)
            if e.name == "print":
                self.emit(Op.PRINT)
                self.emit(Op.CONST, None)  # print returns Unit, like every expression it leaves a value
            else:
                self.emit(Op.CALL, (e.name, len(e.args)))
        elif isinstance(e, s.If):
            self.expr(e.cond)
            else_jump = self.emit(Op.JMP_IF_FALSE)
            self.block(e.then)
            end_jump = self.emit(Op.JMP)
            self.patch(else_jump)
            if e.els is not None:
                self.expr(e.els)
            else:
                self.emit(Op.CONST, None)
            self.patch(end_jump)
        elif isinstance(e, s.Block):
            self.block(e)
        else:
            self.expr_extra(e)

    def expr_extra(self, e: s.Node) -> None:
        raise AssertionError(f"cannot compile {type(e).__name__}")


def compile_fn(fn: s.Fn) -> Chunk:
    c = FnCompiler(fn)
    c.block(fn.body, new_scope=False)
    c.emit(Op.RET)
    return c.chunk


def compile_program(prog: s.Program) -> dict[str, Chunk]:
    return {fn.name: compile_fn(fn) for fn in prog.fns}


def show(chunks: dict[str, Chunk]) -> str:
    return "\n\n".join(disassemble(c) for c in chunks.values())
