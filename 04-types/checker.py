"""Chapter 4: a type checker where the programmer writes every type (no inference yet).

Types are plain strings: "Int", "Bool", "Unit", plus "Never" for expressions that never
produce a value (`return`). Chapter 5 replaces this with real type objects and unification.
"""

from __future__ import annotations

import syntax as s
from lexer import CompileError

PRIMITIVES = {"Int", "Bool", "Unit"}


class TypeError_(CompileError):
    def __init__(self, message: str, pos: int, help: str | None = None, candidates: list[str] | None = None) -> None:
        super().__init__(message, pos, help)
        self.candidates = candidates or []  # names that were in scope: chapter 8 uses them for "did you mean"


def compatible(a: str, b: str) -> bool:
    """`Never` fits anywhere: code after `return` is never reached, so its type does not matter."""
    return a == b or a == "Never" or b == "Never"


class Checker:
    def __init__(self, prog: s.Program) -> None:
        self.prog = prog
        self.sigs: dict[str, tuple[list[str], str]] = {}
        self.scopes: list[dict[str, tuple[str, bool]]] = []  # name -> (type, mutable)
        self.ret = "Unit"

    def error(self, message: str, pos: int, help: str | None = None) -> TypeError_:
        return TypeError_(message, pos, help)

    def type_of_ref(self, t: s.TypeRef) -> str:
        if t.name not in PRIMITIVES:
            raise self.error(f"unknown type `{t.name}`", t.pos, "the types are Int, Bool and Unit")
        return t.name

    # ---------------------------------------------------------------- program
    def check_program(self) -> dict[str, tuple[list[str], str]]:
        for fn in self.prog.fns:
            if fn.name in self.sigs or fn.name == "print":
                raise self.error(f"`{fn.name}` is defined more than once", fn.pos)
            if fn.tparams:
                raise self.error("generic functions arrive in chapter 5", fn.pos)
            params = [self.type_of_ref(p.ty) for p in fn.params]
            ret = self.type_of_ref(fn.ret) if fn.ret else "Unit"
            self.sigs[fn.name] = (params, ret)
        for fn in self.prog.fns:
            self.check_fn(fn)
        return self.sigs

    def check_fn(self, fn: s.Fn) -> None:
        params, self.ret = self.sigs[fn.name]
        self.scopes = [{p.name: (t, False) for p, t in zip(fn.params, params)}]
        body = self.block(fn.body, new_scope=False)
        if not compatible(body, self.ret):
            where = fn.body.tail.pos if fn.body.tail is not None else fn.body.pos
            raise self.error(f"function `{fn.name}` should return `{self.ret}` but its body has type `{body}`", where)

    # ---------------------------------------------------------------- statements
    def lookup(self, name: str, pos: int) -> tuple[str, bool]:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        names = [n for scope in self.scopes for n in scope] + list(self.sigs)
        raise TypeError_(f"cannot find `{name}` in this scope", pos, candidates=names)

    def block(self, b: s.Block, new_scope: bool = True) -> str:
        if new_scope:
            self.scopes.append({})
        diverges = False
        for st in b.stmts:
            if self.stmt(st) == "Never":
                diverges = True
        result = self.expr(b.tail) if b.tail is not None else ("Never" if diverges else "Unit")
        if new_scope:
            self.scopes.pop()
        return result

    def stmt(self, st: s.Node) -> str:
        if isinstance(st, s.Let):
            t = self.expr(st.init)
            if st.ty is not None:
                declared = self.type_of_ref(st.ty)
                if not compatible(declared, t):
                    raise self.error(f"expected `{declared}`, found `{t}`", st.init.pos)
                t = declared
            self.scopes[-1][st.name] = (t, st.mutable)
            return "Unit"
        if isinstance(st, s.Assign):
            t, mutable = self.lookup(st.name, st.pos)
            if not mutable:
                raise self.error(f"cannot assign to `{st.name}`, it is not `mut`", st.pos,
                                 f"declare it with `let mut {st.name}`")  # fmt: skip
            v = self.expr(st.value)
            if not compatible(t, v):
                raise self.error(f"expected `{t}`, found `{v}`", st.value.pos)
            return "Unit"
        if isinstance(st, s.While):
            self.expect(st.cond, "Bool")
            self.block(st.body)
            return "Unit"
        if isinstance(st, s.Return):
            t = self.expr(st.value) if st.value is not None else "Unit"
            if not compatible(t, self.ret):
                raise self.error(f"expected `{self.ret}`, found `{t}`", st.value.pos if st.value else st.pos)
            return "Never"
        if isinstance(st, s.ExprStmt):
            return "Never" if self.expr(st.expr) == "Never" else "Unit"
        raise AssertionError(f"unknown statement {st}")

    # ---------------------------------------------------------------- expressions
    def expect(self, e: s.Node, want: str) -> str:
        got = self.expr(e)
        if not compatible(want, got):
            raise self.error(f"expected `{want}`, found `{got}`", e.pos)
        return got

    def expr(self, e: s.Node) -> str:
        if isinstance(e, s.Num):
            return "Int"
        if isinstance(e, s.BoolLit):
            return "Bool"
        if isinstance(e, s.Var):
            return self.lookup(e.name, e.pos)[0]
        if isinstance(e, s.Unary):
            want = "Bool" if e.op == "!" else "Int"
            self.expect(e.operand, want)
            return want
        if isinstance(e, s.Binary):
            return self.binary(e)
        if isinstance(e, s.Call):
            return self.call(e)
        if isinstance(e, s.If):
            self.expect(e.cond, "Bool")
            then = self.block(e.then)
            if e.els is None:
                if not compatible(then, "Unit"):
                    raise self.error(f"`if` without `else` must have type Unit, not `{then}`", e.then.pos,
                                     "add an `else` branch")  # fmt: skip
                return "Unit"
            other = self.expr(e.els)
            if not compatible(then, other):
                raise self.error(f"the branches have different types: `{then}` and `{other}`", e.els.pos)
            return other if then == "Never" else then
        if isinstance(e, s.Block):
            return self.block(e)
        return self.expr_extra(e)

    def expr_extra(self, e: s.Node) -> str:
        raise AssertionError(f"cannot check {type(e).__name__}")

    def binary(self, e: s.Binary) -> str:
        if e.op in ("&&", "||"):
            self.expect(e.left, "Bool")
            self.expect(e.right, "Bool")
            return "Bool"
        left = self.expr(e.left)
        right = self.expr(e.right)
        if not compatible(left, right):
            raise self.error(f"cannot apply `{e.op}` to `{left}` and `{right}`", e.pos)
        if e.op in ("==", "!="):
            if left not in ("Int", "Bool", "Never"):
                raise self.error(f"cannot compare `{left}` values with `{e.op}`", e.pos)
            return "Bool"  # Int == Int and Bool == Bool are both fine
        if left != "Int":
            raise self.error(f"`{e.op}` needs Int operands, found `{left}`", e.left.pos)
        return "Int" if e.op in ("+", "-", "*", "/", "%") else "Bool"

    def call(self, e: s.Call) -> str:
        if e.name == "print":
            if len(e.args) != 1:
                raise self.error("`print` takes exactly one argument", e.pos)
            self.expr(e.args[0])
            return "Unit"
        if e.name not in self.sigs:
            raise TypeError_(f"cannot find function `{e.name}`", e.pos, candidates=list(self.sigs))
        params, ret = self.sigs[e.name]
        if len(params) != len(e.args):
            raise self.error(f"`{e.name}` takes {len(params)} argument(s) but {len(e.args)} were given", e.pos)
        for p, a in zip(params, e.args):
            self.expect(a, p)
        return ret


def check(prog: s.Program) -> dict[str, tuple[list[str], str]]:
    return Checker(prog).check_program()
