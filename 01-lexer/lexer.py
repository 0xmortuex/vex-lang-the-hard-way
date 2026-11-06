"""Chapter 1: turn source text into tokens."""

from __future__ import annotations

from dataclasses import dataclass

KEYWORDS = {"fn", "let", "mut", "if", "else", "while", "return", "true", "false", "enum", "match"}

# Longest first, so "==" is tried before "=" and "->" before "-".
PUNCTUATION = [
    "==", "!=", "<=", ">=", "&&", "||", "->", "=>",
    "+", "-", "*", "/", "%", "<", ">", "=", "!", "(", ")", "{", "}", "[", "]", ",", ";", ":", "|", ".",
]  # fmt: skip


class CompileError(Exception):
    """Every error the front end reports: a message, a character offset, optional extras."""

    def __init__(self, message: str, pos: int, help: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.pos = pos
        self.help = help


class LexError(CompileError):
    pass


@dataclass
class Token:
    kind: str  # "INT", "IDENT", "EOF", or the keyword / punctuation text itself
    text: str
    pos: int  # offset of the first character in the source


def lex(text: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
        elif text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
        elif ch.isdigit():
            start = i
            while i < n and (text[i].isdigit() or text[i] == "_"):
                i += 1
            if i < n and (text[i].isalpha() or text[i] == "_"):
                raise LexError("a number cannot be followed by letters", start)
            tokens.append(Token("INT", text[start:i].replace("_", ""), start))
        elif ch.isalpha() or ch == "_":
            start = i
            while i < n and (text[i].isalnum() or text[i] == "_"):
                i += 1
            word = text[start:i]
            tokens.append(Token(word if word in KEYWORDS else "IDENT", word, start))
        else:
            for p in PUNCTUATION:
                if text.startswith(p, i):
                    tokens.append(Token(p, p, i))
                    i += len(p)
                    break
            else:
                raise LexError(f"unexpected character {ch!r}", i)
    tokens.append(Token("EOF", "", n))
    return tokens
