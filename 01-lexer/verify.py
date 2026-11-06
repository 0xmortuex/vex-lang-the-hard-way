"""Chapter 1 checks. Run: python 01-lexer/verify.py"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(1)

from lexer import LexError, lex  # noqa: E402


def kinds(text: str) -> list[str]:
    return [t.kind for t in lex(text)][:-1]


def main() -> None:
    assert kinds("let x = 1;") == ["let", "IDENT", "=", "INT", ";"]
    assert kinds("a == b != c <= d >= e") == ["IDENT", "==", "IDENT", "!=", "IDENT", "<=", "IDENT", ">=", "IDENT"]
    assert kinds("fn f(a: Int) -> Int {}") == ["fn", "IDENT", "(", "IDENT", ":", "IDENT", ")", "->", "IDENT", "{", "}"]
    assert kinds("1 // comment\n2") == ["INT", "INT"]
    assert kinds("") == []
    assert kinds("letter lets let") == ["IDENT", "IDENT", "let"]

    toks = lex("ab  12")
    assert [(t.kind, t.text, t.pos) for t in toks] == [("IDENT", "ab", 0), ("INT", "12", 4), ("EOF", "", 6)]
    assert [(t.text, t.pos) for t in lex("let abc = 7")] == [("let", 0), ("abc", 4), ("=", 8), ("7", 10), ("", 11)]
    assert lex("1_000")[0].text == "1000"
    assert lex("değişken")[0].text == "değişken"  # Unicode identifiers work

    for bad, pos in [("let x = 3 $ 4;", 10), ("12abc", 0), ("@", 0)]:
        try:
            lex(bad)
        except LexError as e:
            assert e.pos == pos, (bad, e.pos)
        else:
            raise AssertionError(f"{bad!r} should not lex")
    print("chapter 1 ok")


if __name__ == "__main__":
    main()
