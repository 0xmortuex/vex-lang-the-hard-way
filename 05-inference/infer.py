"""Chapter 5: type inference by unification, plus generic functions.

Same job as chapter 4's checker, but types are objects and unknown types are *variables* that
unification fills in. That buys us omitted return types and `fn id[T](x: T) -> T`.
"""

from __future__ import annotations

import syntax as s
from checker import TypeError_


# ---------------------------------------------------------------- types
class Type:
    pass


class TCon(Type):
    def __init__(self, name: str) -> None:
        self.name = name


class TVar(Type):
    """An unknown type. `ref` is set once unification has solved it."""

    count = 0

    def __init__(self) -> None:
        TVar.count += 1
        self.id = TVar.count
        self.ref: Type | None = None


class TParam(Type):
    """A rigid type parameter: inside `fn id[T]`, T is *some* type we know nothing about."""

    def __init__(self, name: str) -> None:
        self.name = name


INT, BOOL, UNIT, NEVER = TCon("Int"), TCon("Bool"), TCon("Unit"), TCon("Never")
NAMED = {"Int": INT, "Bool": BOOL, "Unit": UNIT}


def prune(t: Type) -> Type:
    while isinstance(t, TVar) and t.ref is not None:
        t = t.ref
    return t


def show(t: Type) -> str:
    t = prune(t)
    if isinstance(t, TCon):
        return t.name
    if isinstance(t, TParam):
        return t.name
    return "_"


class Mismatch(Exception):
    pass


def unify(a: Type, b: Type) -> None:
    """Make `a` and `b` the same type, binding variables as needed, or raise Mismatch."""
    a, b = prune(a), prune(b)
    if a is b or a is NEVER or b is NEVER:
        return  # Never fits everywhere
    if isinstance(a, TVar):
        a.ref = b
        return
    if isinstance(b, TVar):
        b.ref = a
        return
    if isinstance(a, TCon) and isinstance(b, TCon) and a.name == b.name:
        return
    raise Mismatch


def substitute(t: Type, mapping: dict[TParam, Type]) -> Type:
    t = prune(t)
    return mapping.get(t, t) if isinstance(t, TParam) else t


class Sig:
    def __init__(self, fn: s.Fn, tparams: list[TParam], params: list[Type], ret: Type, declared: bool) -> None:
        self.fn = fn
        self.tparams = tparams
        self.params = params
        self.ret = ret
        self.declared = declared  # was the return type written down?
        self.state = 0  # 0 not checked, 1 in progress, 2 done

    def show(self) -> str:
        tp = f"[{', '.join(p.name for p in self.tparams)}]" if self.tparams else ""
        ps = ", ".join(show(p) for p in self.params)
        return f"{self.fn.name}{tp}({ps}) -> {show(self.ret)}"


# ---------------------------------------------------------------- the checker
class Inferencer:
    def __init__(self, prog: s.Program) -> None:
        self.prog = prog
        self.sigs: dict[str, Sig] = {}
        self.scopes: list[dict[str, tuple[Type, bool]]] = []
        self.ret: Type = UNIT
        self.tparams: dict[str, TParam] = {}

    def fail(self, message: str, pos: int, help: str | None = None) -> TypeError_:
        return TypeError_(message, pos, help)

    def unify_at(self, expected: Type, actual: Type, pos: int) -> None:
        try:
            unify(expected, actual)
        except Mismatch:
            raise self.fail(f"expected `{show(expected)}`, found `{show(actual)}`", pos) from None

    def convert(self, t: s.TypeRef, tparams: dict[str, TParam]) -> Type:
        if t.name in tparams:
            return tparams[t.name]
        if t.name in NAMED:
            return NAMED[t.name]
        raise self.fail(f"unknown type `{t.name}`", t.pos, "the types are Int, Bool and Unit, or a type parameter")

    # ---------------------------------------------------------------- program
    def check_program(self) -> dict[str, Sig]:
        for fn in self.prog.fns:
            if fn.name in self.sigs or fn.name == "print":
                raise self.fail(f"`{fn.name}` is defined more than once", fn.pos)
            tps = {n: TParam(n) for n in fn.tparams}
            params = [self.convert(p.ty, tps) for p in fn.params]
            declared = fn.ret is not None
            ret = self.convert(fn.ret, tps) if fn.ret is not None else TVar()
            self.sigs[fn.name] = Sig(fn, list(tps.values()), params, ret, declared)
        for sig in self.sigs.values():
            self.ensure(sig)
        return self.sigs

    def ensure(self, sig: Sig) -> None:
        if sig.state != 0:
            return
        saved = (self.scopes, self.ret, self.tparams)
        sig.state = 1
        fn = sig.fn
        self.tparams = {p.name: p for p in sig.tparams}
        self.scopes = [{p.name: (t, False) for p, t in zip(fn.params, sig.params)}]
        self.ret = sig.ret
        body = self.block(fn.body, new_scope=False)
        where = fn.body.tail.pos if fn.body.tail is not None else fn.body.pos
        try:
            unify(sig.ret, body)
        except Mismatch:
            raise self.fail(f"function `{fn.name}` should return `{show(sig.ret)}` but its body has type "
                            f"`{show(body)}`", where) from None
        if isinstance(prune(sig.ret), TVar):
            sig.ret = UNIT  # nothing constrained it: a function with an empty body
        sig.state = 2
        self.scopes, self.ret, self.tparams = saved

    # ---------------------------------------------------------------- statements
    def lookup(self, name: str, pos: int) -> tuple[Type, bool]:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        names = [n for scope in self.scopes for n in scope] + list(self.sigs)
        raise TypeError_(f"cannot find `{name}` in this scope", pos, candidates=names)

    def block(self, b: s.Block, new_scope: bool = True) -> Type:
        if new_scope:
            self.scopes.append({})
        diverges = False
        for st in b.stmts:
            if self.stmt(st) is NEVER:
                diverges = True
        result = self.expr(b.tail) if b.tail is not None else (NEVER if diverges else UNIT)
        if new_scope:
            self.scopes.pop()
        return result

    def stmt(self, st: s.Node) -> Type:
        if isinstance(st, s.Let):
            t = self.expr(st.init)
            if st.ty is not None:
                declared = self.convert(st.ty, self.tparams)
                self.unify_at(declared, t, st.init.pos)
                t = declared
            self.scopes[-1][st.name] = (t, st.mutable)
            return UNIT
        if isinstance(st, s.Assign):
            t, mutable = self.lookup(st.name, st.pos)
            if not mutable:
                raise self.fail(f"cannot assign to `{st.name}`, it is not `mut`", st.pos, f"declare it with `let mut {st.name}`")
            self.unify_at(t, self.expr(st.value), st.value.pos)
            return UNIT
        if isinstance(st, s.While):
            self.expect(st.cond, BOOL)
            self.block(st.body)
            return UNIT
        if isinstance(st, s.Return):
            t = self.expr(st.value) if st.value is not None else UNIT
            self.unify_at(self.ret, t, st.value.pos if st.value else st.pos)
            return NEVER
        if isinstance(st, s.ExprStmt):
            return NEVER if self.expr(st.expr) is NEVER else UNIT
        raise AssertionError(f"unknown statement {st}")

    # ---------------------------------------------------------------- expressions
    def expect(self, e: s.Node, want: Type) -> Type:
        got = self.expr(e)
        self.unify_at(want, got, e.pos)
        return got

    def expr(self, e: s.Node) -> Type:
        if isinstance(e, s.Num):
            return INT
        if isinstance(e, s.BoolLit):
            return BOOL
        if isinstance(e, s.Var):
            return self.lookup(e.name, e.pos)[0]
        if isinstance(e, s.Unary):
            want = BOOL if e.op == "!" else INT
            self.expect(e.operand, want)
            return want
        if isinstance(e, s.Binary):
            return self.binary(e)
        if isinstance(e, s.Call):
            return self.call(e)
        if isinstance(e, s.If):
            self.expect(e.cond, BOOL)
            then = self.block(e.then)
            if e.els is None:
                self.unify_at(UNIT, then, e.then.pos)
                return UNIT
            other = self.expr(e.els)
            try:
                unify(then, other)
            except Mismatch:
                raise self.fail(f"the branches have different types: `{show(then)}` and `{show(other)}`", e.els.pos) from None
            return other if prune(then) is NEVER else then
        if isinstance(e, s.Block):
            return self.block(e)
        return self.expr_extra(e)

    def expr_extra(self, e: s.Node) -> Type:
        raise AssertionError(f"cannot check {type(e).__name__}")

    def binary(self, e: s.Binary) -> Type:
        if e.op in ("&&", "||"):
            self.expect(e.left, BOOL)
            self.expect(e.right, BOOL)
            return BOOL
        left = self.expr(e.left)
        right = self.expr(e.right)
        try:
            unify(left, right)
        except Mismatch:
            raise self.fail(f"cannot apply `{e.op}` to `{show(left)}` and `{show(right)}`", e.pos) from None
        if e.op in ("==", "!="):
            t = prune(left)
            if isinstance(t, TParam) or (isinstance(t, TCon) and t.name not in ("Int", "Bool", "Never")):
                raise self.fail(f"cannot compare `{show(t)}` values with `{e.op}`", e.pos)
            return BOOL
        self.unify_at(INT, left, e.left.pos)
        return INT if e.op in ("+", "-", "*", "/", "%") else BOOL

    def call(self, e: s.Call) -> Type:
        if e.name == "print":
            if len(e.args) != 1:
                raise self.fail("`print` takes exactly one argument", e.pos)
            self.expr(e.args[0])
            return UNIT
        sig = self.sigs.get(e.name)
        if sig is None:
            raise TypeError_(f"cannot find function `{e.name}`", e.pos, candidates=list(self.sigs))
        if not sig.declared and sig.state == 0:
            self.ensure(sig)  # we need its return type: infer the callee's body first
        elif not sig.declared and sig.state == 1 and sig.tparams:
            raise self.fail(f"recursive generic function `{e.name}` needs a declared return type", e.pos,
                            f"write `-> Type` after the parameters of `{e.name}`")  # fmt: skip
        if len(sig.params) != len(e.args):
            raise self.fail(f"`{e.name}` takes {len(sig.params)} argument(s) but {len(e.args)} were given", e.pos)
        # Instantiate: every type parameter becomes a fresh variable for this call.
        mapping: dict[TParam, Type] = {p: TVar() for p in sig.tparams}
        for p, a in zip(sig.params, e.args):
            self.expect(a, substitute(p, mapping))
        return substitute(sig.ret, mapping)


def check(prog: s.Program) -> dict[str, Sig]:
    return Inferencer(prog).check_program()
