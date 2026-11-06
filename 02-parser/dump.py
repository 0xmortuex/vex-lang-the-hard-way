"""Chapter 2: print an AST as an s-expression (handy for tests and for seeing what parsed)."""

from __future__ import annotations

import syntax as s


def dump(n: object) -> str:
    if isinstance(n, s.Num):
        return str(n.value)
    if isinstance(n, s.BoolLit):
        return "true" if n.value else "false"
    if isinstance(n, s.Var):
        return n.name
    if isinstance(n, s.Unary):
        return f"({n.op} {dump(n.operand)})"
    if isinstance(n, s.Binary):
        return f"({n.op} {dump(n.left)} {dump(n.right)})"
    if isinstance(n, s.Call):
        return f"({n.name}{''.join(' ' + dump(a) for a in n.args)})"
    if isinstance(n, s.If):
        tail = f" {dump(n.els)}" if n.els is not None else ""
        return f"(if {dump(n.cond)} {dump(n.then)}{tail})"
    if isinstance(n, s.Block):
        parts = [dump(x) for x in n.stmts]
        if n.tail is not None:
            parts.append("=> " + dump(n.tail))
        return "{" + "; ".join(parts) + "}"
    if isinstance(n, s.Let):
        return f"(let{' mut' if n.mutable else ''} {n.name} {dump(n.init)})"
    if isinstance(n, s.Assign):
        return f"(set {n.name} {dump(n.value)})"
    if isinstance(n, s.While):
        return f"(while {dump(n.cond)} {dump(n.body)})"
    if isinstance(n, s.Return):
        return f"(return{' ' + dump(n.value) if n.value is not None else ''})"
    if isinstance(n, s.ExprStmt):
        return dump(n.expr)
    if isinstance(n, s.Fn):
        ps = ", ".join(f"{p.name}: {p.ty.name}" for p in n.params)
        ret = f" -> {n.ret.name}" if n.ret else ""
        return f"fn {n.name}({ps}){ret} {dump(n.body)}"
    if isinstance(n, s.Program):
        return "\n".join(dump(f) for f in n.fns)
    return type(n).__name__
