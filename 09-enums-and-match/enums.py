"""Chapter 9: type-check enums and `match`, by extending chapter 5's inferencer."""

from __future__ import annotations

import syntax as s
import syntax_enums as se
from checker import TypeError_
from exhaustive import missing
from infer import INT, NEVER, UNIT, BOOL, Inferencer, Mismatch, TCon, TParam, Type, prune, show, unify


class EnumInferencer(Inferencer):
    def __init__(self, prog: s.Program) -> None:
        super().__init__(prog)
        self.enums: dict[str, se.EnumDecl] = {}
        self.variants: dict[str, tuple[str, list[Type]]] = {}  # variant name -> (enum name, field types)
        self.families: dict[str, list[tuple[str, int]]] = {}  # variant name -> all siblings (name, arity)

    def convert(self, t: s.TypeRef, tparams: dict[str, TParam]) -> Type:
        if t.name in self.enums:
            return TCon(t.name)
        return super().convert(t, tparams)

    def check_program(self):  # type: ignore[no-untyped-def]
        decls = [d for d in self.prog.extra if isinstance(d, se.EnumDecl)]
        for d in decls:  # first register every enum name, so variants can mention any enum
            if d.name in self.enums:
                raise self.fail(f"`{d.name}` is defined more than once", d.pos)
            self.enums[d.name] = d
        for d in decls:
            siblings = [(v.name, len(v.fields)) for v in d.variants]
            for v in d.variants:
                if v.name in self.variants:
                    raise self.fail(f"variant `{v.name}` is defined more than once", v.pos,
                                    "variant names must be unique across all enums in this tutorial")  # fmt: skip
                self.variants[v.name] = (d.name, [self.convert(f, {}) for f in v.fields])
                self.families[v.name] = siblings
        return super().check_program()

    # ---------------------------------------------------------------- expressions
    def expr(self, e: s.Node) -> Type:
        if isinstance(e, s.Var) and e.name in self.variants and not any(e.name in sc for sc in self.scopes):
            enum, fields = self.variants[e.name]
            if fields:
                raise self.fail(f"variant `{e.name}` needs {len(fields)} argument(s)", e.pos,
                                f"write `{e.name}({', '.join('...' for _ in fields)})`")  # fmt: skip
            return TCon(enum)
        return super().expr(e)

    def call(self, e: s.Call) -> Type:
        if e.name in self.variants:
            enum, fields = self.variants[e.name]
            if len(fields) != len(e.args):
                raise self.fail(f"variant `{e.name}` takes {len(fields)} argument(s) but {len(e.args)} were given", e.pos)
            for f, a in zip(fields, e.args):
                self.expect(a, f)
            return TCon(enum)
        return super().call(e)

    def expr_extra(self, e: s.Node) -> Type:
        if isinstance(e, se.Match):
            return self.match(e)
        return super().expr_extra(e)

    def match(self, e: se.Match) -> Type:
        scrut = self.expr(e.scrut)
        result: Type | None = None
        for arm in e.arms:
            self.scopes.append({})
            self.pattern(arm.pat, scrut)
            body = self.expr(arm.body)
            self.scopes.pop()
            if result is None or prune(result) is NEVER:
                result = body
            else:
                try:
                    unify(result, body)
                except Mismatch:
                    raise self.fail(f"match arms have different types: `{show(result)}` and `{show(body)}`", arm.body.pos) from None
        w = missing([a.pat for a in e.arms], self.families)
        if w is not None:
            raise self.fail("non-exhaustive `match`", e.scrut.pos,
                            f"pattern `{w}` is not covered; add an arm for it or a catch-all `_`")  # fmt: skip
        return result if result is not None else NEVER

    def pattern(self, p: s.Node, ty: Type) -> None:
        if isinstance(p, se.PWild):
            return
        if isinstance(p, se.PVar):
            self.scopes[-1][p.name] = (ty, False)
        elif isinstance(p, se.PLit):
            self.unify_at(ty, BOOL if isinstance(p.value, bool) else INT, p.pos)
        elif isinstance(p, se.PCtor):
            if p.name not in self.variants:
                raise TypeError_(f"cannot find variant `{p.name}`", p.pos, candidates=list(self.variants))
            enum, fields = self.variants[p.name]
            self.unify_at(ty, TCon(enum), p.pos)
            if len(fields) != len(p.args):
                raise self.fail(f"variant `{p.name}` has {len(fields)} field(s) but the pattern has {len(p.args)}", p.pos)
            for sub, ft in zip(p.args, fields):
                self.pattern(sub, ft)
        else:
            raise AssertionError(f"unknown pattern {p}")


def check(prog: s.Program):  # type: ignore[no-untyped-def]
    return EnumInferencer(prog).check_program()


__all__ = ["EnumInferencer", "check", "UNIT"]
