"""Chapter 9: evaluate enums and `match`, by extending chapter 3's evaluator."""

from __future__ import annotations

from collections.abc import Callable

import syntax as s
import syntax_enums as se
from evaluator import Env, Evaluator, Value
from ops import RunError


class Variant:
    def __init__(self, name: str, fields: list[object]) -> None:
        self.name = name
        self.fields = fields


class EnumEvaluator(Evaluator):
    def __init__(self, prog: s.Program, out: Callable[[str], None] = print) -> None:
        super().__init__(prog, out)
        self.variants = {v.name for d in prog.extra if isinstance(d, se.EnumDecl) for v in d.variants}

    @staticmethod
    def show(v: Value) -> str:  # type: ignore[override]
        if isinstance(v, Variant):
            return v.name if not v.fields else f"{v.name}({', '.join(EnumEvaluator.show(f) for f in v.fields)})"  # type: ignore[arg-type]
        return Evaluator.show(v)

    def eval(self, e: s.Node, env: Env) -> Value:
        if isinstance(e, s.Var) and e.name in self.variants:
            return Variant(e.name, [])  # type: ignore[return-value]
        if isinstance(e, s.Call) and e.name in self.variants:
            return Variant(e.name, [self.eval(a, env) for a in e.args])  # type: ignore[return-value]
        return super().eval(e, env)

    def eval_extra(self, e: s.Node, env: Env) -> Value:
        if isinstance(e, se.Match):
            value = self.eval(e.scrut, env)
            for arm in e.arms:
                env.scopes.append({})
                try:
                    if self.matches(arm.pat, value, env):
                        return self.eval(arm.body, env)
                finally:
                    env.scopes.pop()
            raise RunError("no match arm matched", e.pos)  # the exhaustiveness check makes this unreachable
        return super().eval_extra(e, env)

    def matches(self, p: s.Node, v: object, env: Env) -> bool:
        if isinstance(p, se.PWild):
            return True
        if isinstance(p, se.PVar):
            env.define(p.name, v)  # type: ignore[arg-type]
            return True
        if isinstance(p, se.PLit):
            return v == p.value and type(v) is type(p.value)
        assert isinstance(p, se.PCtor) and isinstance(v, Variant)
        return p.name == v.name and all(self.matches(sp, fv, env) for sp, fv in zip(p.args, v.fields))


def run(text: str) -> list[str]:
    """Parse (with enums), type-check, and evaluate a program."""
    from enums import check
    from lexer import lex
    from parser_enums import EnumParser

    prog = EnumParser(lex(text)).parse_program()
    check(prog)
    lines: list[str] = []
    EnumEvaluator(prog, lines.append).run_main()
    return lines
