"""Chapter 2: a recursive-descent parser with a Pratt loop for binary operators."""

from __future__ import annotations

import syntax as s
from lexer import CompileError, Token, lex

# Binary operators: higher number binds tighter. All are left-associative.
PRECEDENCE = {
    "||": 1, "&&": 2,
    "==": 3, "!=": 3,
    "<": 4, "<=": 4, ">": 4, ">=": 4,
    "+": 5, "-": 5,
    "*": 6, "/": 6, "%": 6,
}  # fmt: skip


class ParseError(CompileError):
    pass


class Parser:
    # Expressions that may end a statement without a `;`. Chapter 9 adds `match` to this tuple.
    block_like: tuple[type, ...] = (s.If, s.Block)
    block_starts: tuple[str, ...] = ("if", "{")  # a statement that starts with one of these ends at its `}`

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.i = 0

    # ---------------------------------------------------------------- helpers
    @property
    def tok(self) -> Token:
        return self.tokens[self.i]

    def at(self, kind: str) -> bool:
        return self.tok.kind == kind

    def advance(self) -> Token:
        t = self.tok
        if t.kind != "EOF":
            self.i += 1
        return t

    def eat(self, kind: str) -> Token | None:
        return self.advance() if self.at(kind) else None

    def expect(self, kind: str, what: str = "") -> Token:
        if self.at(kind):
            return self.advance()
        found = "end of file" if self.at("EOF") else f"`{self.tok.text}`"
        raise ParseError(f"expected `{kind}`{what}, found {found}", self.tok.pos)

    # ---------------------------------------------------------------- items
    def parse_program(self) -> s.Program:
        prog = s.Program([])
        while not self.at("EOF"):
            self.parse_item(prog)
        return prog

    def parse_item(self, prog: s.Program) -> None:
        """Extension point: chapter 9 overrides this to accept `enum` declarations."""
        if self.at("fn"):
            prog.fns.append(self.parse_fn())
        else:
            raise ParseError(f"expected `fn`, found `{self.tok.text}`", self.tok.pos)

    def parse_fn(self) -> s.Fn:
        start = self.expect("fn")
        name = self.expect("IDENT", " (the function name)")
        tparams: list[str] = []
        if self.eat("["):
            while not self.at("]"):
                tparams.append(self.expect("IDENT").text)
                if not self.eat(","):
                    break
            self.expect("]")
        self.expect("(")
        params: list[s.Param] = []
        while not self.at(")"):
            pname = self.expect("IDENT", " (a parameter name)")
            self.expect(":", f" (parameter `{pname.text}` needs a type)")
            params.append(s.Param(pname.pos, pname.text, self.parse_type()))
            if not self.eat(","):
                break
        self.expect(")")
        ret = self.parse_type() if self.eat("->") else None
        return s.Fn(start.pos, name.text, tparams, params, ret, self.parse_block())

    def parse_type(self) -> s.TypeRef:
        t = self.expect("IDENT", " (a type name)")
        return s.TypeRef(t.pos, t.text)

    # ---------------------------------------------------------------- statements
    def parse_block(self) -> s.Block:
        start = self.expect("{")
        stmts: list[s.Node] = []
        tail: s.Node | None = None
        while not self.at("}"):
            if self.at("EOF"):
                raise ParseError("this block is never closed", start.pos, help="add a matching `}`")
            node = self.parse_stmt()
            if isinstance(node, s.ExprStmt) and not node.semi and self.at("}"):
                tail = node.expr
                break
            stmts.append(node)
        self.expect("}")
        return s.Block(start.pos, stmts, tail)

    def parse_stmt(self) -> s.Node:
        t = self.tok
        if t.kind == "let":
            self.advance()
            mutable = self.eat("mut") is not None
            name = self.expect("IDENT", " (a variable name)")
            ty = self.parse_type() if self.eat(":") else None
            self.expect("=", " (every `let` needs a value)")
            init = self.parse_expr()
            self.expect(";", " after the `let`")
            return s.Let(t.pos, name.text, mutable, ty, init)
        if t.kind == "return":
            self.advance()
            value = None if self.at(";") else self.parse_expr()
            self.expect(";", " after `return`")
            return s.Return(t.pos, value)
        if t.kind == "while":
            self.advance()
            cond = self.parse_expr()
            return s.While(t.pos, cond, self.parse_block())
        # `if ... { }` or `{ ... }` at the start of a statement is a complete statement: what follows
        # (even `(` or `-`) begins the next one. So parse just the primary, not a longer expression.
        expr = self.parse_primary() if t.kind in self.block_starts else self.parse_expr()
        if self.at("=") and isinstance(expr, s.Var):
            self.advance()
            value = self.parse_expr()
            self.expect(";", " after the assignment")
            return s.Assign(t.pos, expr.name, value)
        if self.eat(";"):
            return s.ExprStmt(t.pos, expr, semi=True)
        if self.at("}") or isinstance(expr, self.block_like):
            return s.ExprStmt(t.pos, expr, semi=False)  # no `;`: a block value, or an `if` statement
        raise ParseError(f"expected `;` or `}}`, found `{self.tok.text}`", self.tok.pos)

    # ---------------------------------------------------------------- expressions
    def parse_expr(self, min_prec: int = 1) -> s.Node:
        left = self.parse_unary()
        while True:
            op = self.tok.kind
            prec = PRECEDENCE.get(op)
            if prec is None or prec < min_prec:
                return left
            tok = self.advance()
            right = self.parse_expr(prec + 1)  # +1 makes the operator left-associative
            left = s.Binary(tok.pos, op, left, right)

    def parse_unary(self) -> s.Node:
        t = self.tok
        if t.kind in ("-", "!"):
            self.advance()
            return s.Unary(t.pos, t.kind, self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self) -> s.Node:
        e = self.parse_primary()
        while self.at("(") and isinstance(e, s.Var):
            self.advance()
            args: list[s.Node] = []
            while not self.at(")"):
                args.append(self.parse_expr())
                if not self.eat(","):
                    break
            self.expect(")", " after the arguments")
            e = s.Call(e.pos, e.name, args)
        return e

    def parse_primary(self) -> s.Node:
        t = self.tok
        if t.kind == "INT":
            self.advance()
            return s.Num(t.pos, int(t.text))
        if t.kind in ("true", "false"):
            self.advance()
            return s.BoolLit(t.pos, t.kind == "true")
        if t.kind == "IDENT":
            self.advance()
            return s.Var(t.pos, t.text)
        if t.kind == "(":
            self.advance()
            e = self.parse_expr()
            self.expect(")")
            return e
        if t.kind == "if":
            return self.parse_if()
        if t.kind == "{":
            return self.parse_block()
        extra = self.parse_primary_extra()
        if extra is not None:
            return extra
        found = "end of file" if t.kind == "EOF" else f"`{t.text}`"
        raise ParseError(f"expected an expression, found {found}", t.pos)

    def parse_primary_extra(self) -> s.Node | None:
        """Extension point: chapter 9 adds `match` here."""
        return None

    def parse_if(self) -> s.If:
        start = self.expect("if")
        cond = self.parse_expr()
        then = self.parse_block()
        els: s.Node | None = None
        if self.eat("else"):
            els = self.parse_if() if self.at("if") else self.parse_block()
        return s.If(start.pos, cond, then, els)


def parse(text: str) -> s.Program:
    return Parser(lex(text)).parse_program()
