"""Chapter 8: a parser that keeps going after a syntax error.

Panic-mode recovery: when a statement (or item) fails to parse, record the error, then skip
tokens until a place where parsing can plausibly restart: just after a `;`, or at a `}` that
closes the block, or at the next `fn`.
"""

from __future__ import annotations

import syntax as s
from lexer import CompileError
from parser import ParseError, Parser


class RecoveringParser(Parser):
    def __init__(self, tokens):  # type: ignore[no-untyped-def]
        super().__init__(tokens)
        self.errors: list[CompileError] = []

    def parse_program(self) -> s.Program:
        prog = s.Program([])
        while not self.at("EOF"):
            start = self.i
            try:
                self.parse_item(prog)
            except ParseError as e:
                self.errors.append(e)
                self.sync_item()
                if self.i == start:
                    self.advance()  # always make progress
        return prog

    def sync_item(self) -> None:
        depth = 0
        while not self.at("EOF"):
            if depth <= 0 and self.at("fn"):
                return
            if self.at("{"):
                depth += 1
            elif self.at("}"):
                depth -= 1
            self.advance()

    def parse_block(self) -> s.Block:
        start = self.expect("{")
        stmts: list[s.Node] = []
        tail: s.Node | None = None
        while not self.at("}"):
            if self.at("EOF"):
                raise ParseError("this block is never closed", start.pos, help="add a matching `}`")
            before = self.i
            try:
                node = self.parse_stmt()
            except ParseError as e:
                self.errors.append(e)
                self.sync_stmt()
                if self.i == before:
                    self.advance()
                continue
            if isinstance(node, s.ExprStmt) and not node.semi and self.at("}"):
                tail = node.expr
                break
            stmts.append(node)
        self.expect("}")
        return s.Block(start.pos, stmts, tail)

    def sync_stmt(self) -> None:
        depth = 0
        while not self.at("EOF"):
            if depth == 0 and self.at(";"):
                self.advance()
                return
            if depth == 0 and (self.at("}") or self.at("fn")):
                return
            if self.at("{"):
                depth += 1
            elif self.at("}"):
                depth -= 1
            self.advance()
