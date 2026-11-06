"""Chapter 3: a tree-walking interpreter. Slow, simple, and the reference for the VM in chapter 7."""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable

import syntax as s
from ops import RunError, arith, checked, compare

MAX_DEPTH = 500  # Vex calls; each one costs several Python frames in a tree walker

Value = int | bool | None


class ReturnSignal(Exception):
    def __init__(self, value: Value) -> None:
        self.value = value


class Env:
    """A stack of scopes; inner scopes shadow outer ones."""

    def __init__(self) -> None:
        self.scopes: list[dict[str, Value]] = [{}]

    def define(self, name: str, value: Value) -> None:
        self.scopes[-1][name] = value

    def assign(self, name: str, value: Value) -> None:
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name] = value
                return
        raise AssertionError(f"assignment to unknown variable {name}")  # the checker rules this out

    def get(self, name: str) -> Value:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise AssertionError(f"unknown variable {name}")


class Evaluator:
    def __init__(self, prog: s.Program, out: Callable[[str], None] = print) -> None:
        self.fns = {f.name: f for f in prog.fns}
        self.out = out
        self.depth = 0
        sys.setrecursionlimit(max(sys.getrecursionlimit(), 20_000))

    def run_main(self) -> Value:
        """Run `main` on a thread with a big stack: a tree walker recurses on the *host* stack."""
        outcome: list[tuple[bool, object]] = []

        def target() -> None:
            try:
                outcome.append((True, self.call("main", [], -1)))
            except BaseException as e:  # handed back to the caller's thread below
                outcome.append((False, e))

        old = threading.stack_size(64 * 1024 * 1024)
        try:
            t = threading.Thread(target=target)
            t.start()
            t.join()
        finally:
            threading.stack_size(old)
        ok, value = outcome[0]
        if not ok:
            assert isinstance(value, BaseException)
            raise value
        return value  # type: ignore[return-value]

    def call(self, name: str, args: list[Value], pos: int) -> Value:
        if name == "print":
            self.out(self.show(args[0]))
            return None
        fn = self.fns[name]
        if self.depth >= MAX_DEPTH:
            raise RunError(f"stack overflow (more than {MAX_DEPTH} nested calls)", pos)
        env = Env()
        for p, a in zip(fn.params, args):
            env.define(p.name, a)
        self.depth += 1
        try:
            return self.block(fn.body, env, new_scope=False)
        except ReturnSignal as r:
            return r.value
        finally:
            self.depth -= 1

    @staticmethod
    def show(v: Value) -> str:
        if v is None:
            return "()"
        if isinstance(v, bool):
            return "true" if v else "false"
        return str(v)

    # ---------------------------------------------------------------- statements
    def block(self, b: s.Block, env: Env, new_scope: bool = True) -> Value:
        if new_scope:
            env.scopes.append({})
        try:
            for st in b.stmts:
                self.stmt(st, env)
            return self.eval(b.tail, env) if b.tail is not None else None
        finally:
            if new_scope:
                env.scopes.pop()

    def stmt(self, st: s.Node, env: Env) -> None:
        if isinstance(st, s.Let):
            env.define(st.name, self.eval(st.init, env))
        elif isinstance(st, s.Assign):
            env.assign(st.name, self.eval(st.value, env))
        elif isinstance(st, s.While):
            while self.eval(st.cond, env):
                self.block(st.body, env)
        elif isinstance(st, s.Return):
            raise ReturnSignal(self.eval(st.value, env) if st.value is not None else None)
        elif isinstance(st, s.ExprStmt):
            self.eval(st.expr, env)
        else:
            raise AssertionError(f"unknown statement {st}")

    # ---------------------------------------------------------------- expressions
    def eval(self, e: s.Node, env: Env) -> Value:
        if isinstance(e, s.Num):
            return e.value
        if isinstance(e, s.BoolLit):
            return e.value
        if isinstance(e, s.Var):
            return env.get(e.name)
        if isinstance(e, s.Unary):
            v = self.eval(e.operand, env)
            if e.op == "!":
                return not v
            assert isinstance(v, int)
            try:
                return checked(-v, "-")
            except RunError as err:
                err.pos = e.pos
                raise
        if isinstance(e, s.Binary):
            return self.binary(e, env)
        if isinstance(e, s.Call):
            args = [self.eval(a, env) for a in e.args]
            try:
                return self.call(e.name, args, e.pos)
            except RunError as err:
                if err.pos < 0:
                    err.pos = e.pos
                raise
        if isinstance(e, s.If):
            if self.eval(e.cond, env):
                return self.block(e.then, env)
            if e.els is not None:
                return self.eval(e.els, env)
            return None
        if isinstance(e, s.Block):
            return self.block(e, env)
        return self.eval_extra(e, env)

    def eval_extra(self, e: s.Node, env: Env) -> Value:
        """Extension point: chapter 9 handles `match` and enum constructors here."""
        raise AssertionError(f"cannot evaluate {type(e).__name__}")

    def binary(self, e: s.Binary, env: Env) -> Value:
        if e.op == "&&":
            return bool(self.eval(e.left, env)) and bool(self.eval(e.right, env))
        if e.op == "||":
            return bool(self.eval(e.left, env)) or bool(self.eval(e.right, env))
        a = self.eval(e.left, env)
        b = self.eval(e.right, env)
        assert isinstance(a, int) and isinstance(b, int)
        try:
            if e.op in ("+", "-", "*", "/", "%"):
                return arith(e.op, a, b)
            return compare(e.op, a, b)
        except RunError as err:
            err.pos = e.pos
            raise


def run(text: str) -> list[str]:
    """Parse and run a program; return the lines it printed."""
    from parser import parse

    lines: list[str] = []
    Evaluator(parse(text), lines.append).run_main()
    return lines
