"""Chapter 9: the parser, extended through the two hooks chapter 2 left open."""

from __future__ import annotations

import syntax as s
import syntax_enums as se
from lexer import KEYWORDS, Token
from parser import ParseError, Parser


class EnumParser(Parser):
    block_like = (s.If, s.Block, se.Match)  # `match` may end a statement without `;`
    block_starts = ("if", "{", "match")

    def parse_item(self, prog: s.Program) -> None:
        if self.at("enum"):
            prog.extra.append(self.parse_enum())
        else:
            super().parse_item(prog)

    def parse_enum(self) -> se.EnumDecl:
        start = self.expect("enum")
        name = self.expect("IDENT", " (the enum name)")
        self.expect("{")
        variants: list[se.Variant] = []
        while not self.at("}"):
            v = self.expect("IDENT", " (a variant name)")
            fields: list[s.TypeRef] = []
            if self.eat("("):
                while not self.at(")"):
                    fields.append(self.parse_type())
                    if not self.eat(","):
                        break
                self.expect(")")
            variants.append(se.Variant(v.pos, v.text, fields))
            if not self.eat(","):
                break
        self.expect("}", " after the variants")
        return se.EnumDecl(start.pos, name.text, variants)

    def parse_primary_extra(self) -> s.Node | None:
        if not self.at("match"):
            return None
        start = self.advance()
        scrut = self.parse_expr()
        self.expect("{")
        arms: list[se.Arm] = []
        while not self.at("}"):
            pat = self.parse_pattern()
            self.expect("=>", " after the pattern")
            body = self.parse_expr()
            arms.append(se.Arm(pat.pos, pat, body))
            if not self.eat(",") and not isinstance(body, s.Block):
                break
        self.expect("}", " to close the match")
        return se.Match(start.pos, scrut, arms)

    def parse_pattern(self) -> s.Node:
        t: Token = self.tok
        if t.kind == "INT":
            self.advance()
            return se.PLit(t.pos, int(t.text))
        if t.kind == "-":
            self.advance()
            n = self.expect("INT")
            return se.PLit(t.pos, -int(n.text))
        if t.kind in ("true", "false"):
            self.advance()
            return se.PLit(t.pos, t.kind == "true")
        if t.kind == "IDENT":
            self.advance()
            if t.text == "_":
                return se.PWild(t.pos)
            if self.eat("("):
                args: list[s.Node] = []
                while not self.at(")"):
                    args.append(self.parse_pattern())
                    if not self.eat(","):
                        break
                self.expect(")")
                return se.PCtor(t.pos, t.text, args)
            # An uppercase name is a variant; a lowercase one binds a new variable.
            return se.PCtor(t.pos, t.text, []) if t.text[:1].isupper() else se.PVar(t.pos, t.text)
        found = "end of file" if t.kind == "EOF" else f"`{t.text}`"
        if t.kind in KEYWORDS:
            found = f"keyword {found}"
        raise ParseError(f"expected a pattern, found {found}", t.pos)
