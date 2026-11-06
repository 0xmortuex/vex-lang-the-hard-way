# Module 01: The Lexer

## The Concept

A compiler does not look at characters. The first step turns the text into **tokens**: the
words and punctuation of the language. After that the parser deals in `if`, `(` and `42`, not in
`i`, `f`, `(`, `4`, `2`.

```
fn fib(n: Int) -> Int { n }

   fn   IDENT(fib)  (  IDENT(n)  :  IDENT(Int)  )  ->  IDENT(Int)  {  IDENT(n)  }
```

This module is short on purpose. A lexer is a loop with a few cases, and almost everything
interesting about it is in what it *remembers*.

## What a token carries

```python
@dataclass
class Token:
    kind: str   # "INT", "IDENT", "EOF", or the keyword / punctuation text itself
    text: str
    pos: int    # offset of the first character in the source
```

`pos` is the whole reason errors can point at things later (module 08 turns it into
`line:column`). Throwing it away "because the parser does not need it" is the classic mistake.
For keywords and punctuation `kind` is the text itself (`"fn"`, `"->"`), so the parser can write
`self.at("->")` instead of comparing two fields.

## The loop

```python
while i < n:
    ch = text[i]
    if ch.isspace():                     i += 1
    elif text.startswith("//", i):       skip to end of line
    elif ch.isdigit():                   read digits  -> INT
    elif ch.isalpha() or ch == "_":      read a word  -> keyword or IDENT
    else:                                try punctuation, longest first
```

Three details that matter:

1. **Longest match first.** `PUNCTUATION` lists `"=="` before `"="` and `"->"` before `"-"`. If `"="` came
   first, `a == b` would lex as two `=` tokens.
2. **Keywords are identifiers that are on a list.** The lexer reads a whole word, then asks
   `word in KEYWORDS`. Reading `letter` character by character against `let` would get it wrong.
3. **`12abc` is an error, not `12` followed by `abc`.** Silent splitting turns typos into confusing
   parse errors three tokens later.

`isalpha()` and `isalnum()` are Unicode-aware, so `değişken` is a valid identifier and Turkish
variable names just work. Source is UTF-8; `pos` counts characters.

## Errors

```python
class CompileError(Exception):
    message: str
    pos: int
    help: str | None
```

Every front-end error in this tutorial is a `CompileError` with a message and a position.
`LexError` is a subclass. Having one error type that all stages share is what lets module 08 render
them all the same way.

## Run it

```
python 01-lexer/main.py       # prints the tokens of a small program, and a lex error
python 01-lexer/verify.py     # chapter 1 ok
```

## The real thing

[`src/vex/lexer.py`](https://github.com/0xmortuex/vex-lang/blob/main/src/vex/lexer.py) does the same loop but also handles
string literals with `{interpolation}` (finding the matching brace while skipping nested strings), numeric
literals with `0x`, `1e3` and `_`, nested block comments, and keeps on lexing after an error so several
lexical mistakes are reported at once.

Next: [02 Parser](../02-parser/)
