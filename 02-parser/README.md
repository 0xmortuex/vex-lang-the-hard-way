# Module 02: The Parser

## The Concept

The parser turns a flat list of tokens into a **tree** that says what the program means:
`1 + 2 * 3` is not "five tokens", it is an addition whose right side is a multiplication.

```
tokens:  1  +  2  *  3          tree:      (+ 1 (* 2 3))

                                              +
                                             / \
                                            1   *
                                               / \
                                              2   3
```

`python 02-parser/main.py` prints trees like `(+ 1 (* 2 3))` using `dump.py`, a 40-line s-expression
printer. Reading the printed tree is the fastest way to find out what your parser thinks you wrote.

## The syntax tree (`syntax.py`)

One small dataclass per construct: `Num`, `Var`, `Binary`, `Call`, `If`, `Block`, `Let`, `Assign`, `While`,
`Return`, `Fn`. Every node inherits `pos` (the offset of its first token), which is how module 08 will point at it.

A **block** has statements and an optional tail expression: `{ let x = 1; x + 1 }` has one statement and the
tail `x + 1`, which is the value of the block. No tail means the block's value is `Unit`. That one rule is what
lets `if` be an expression:

```text
let parity = if n % 2 == 0 { 0 } else { 1 };
```

## Recursive descent

Each grammar rule is a method. The rule for a function is `parse_fn`, for a block `parse_block`, for a
statement `parse_stmt`. A rule that contains another rule calls its method. Helper methods do the token work:

```python
def expect(self, kind, what=""):          # consume a token of this kind or raise a ParseError
    if self.at(kind): return self.advance()
    raise ParseError(f"expected `{kind}`{what}, found ...", self.tok.pos)
```

Error messages are written *at the point of failure*, where the parser knows what it was doing
(`expected \`;\` after the \`let\``), not later.

## Operators: the Pratt loop

Expressions are where recursive descent gets awkward: `+` binds looser than `*`, both associate to the left.
The trick is a table of precedences and one loop:

```python
PRECEDENCE = {"||": 1, "&&": 2, "==": 3, "!=": 3, "<": 4, ..., "+": 5, "-": 5, "*": 6, "/": 6, "%": 6}

def parse_expr(self, min_prec=1):
    left = self.parse_unary()
    while True:
        prec = PRECEDENCE.get(self.tok.kind)
        if prec is None or prec < min_prec:
            return left
        op = self.advance()
        right = self.parse_expr(prec + 1)       # +1 => left associative
        left = Binary(op.pos, op.kind, left, right)
```

Trace `1 - 2 - 3`: `left = 1`; see `-` (5), parse the right side with `min_prec = 6`, so it stops at the next `-`,
returns `2`; `left = (1 - 2)`; the loop sees the second `-` and builds `((1 - 2) - 3)`. Associativity is just that
`+ 1`. Unary operators bind tighter than every binary one, so `parse_unary` sits underneath.

The `Binary` node's `pos` is the *operator's* position, so "cannot apply `+` to Int and Bool" will point at the `+`.

## Statements and the semicolon rule

```
let x = e;        return e;        while c { ... }        x = e;        e;        e   (last: the block's value)
```

An expression statement needs `;` unless it is the last thing in the block (then it is the value), or is
block-like (`if`, `{ }`). The parser decides this in `parse_stmt` by looking at what follows the expression:
a `;` (statement), a `}` (tail), or neither (an error, unless the expression was an `if`).

A statement that *starts* with `if` or `{` is complete at its closing brace, so the next token starts a new
statement: otherwise `if c { } (x + 1)` would try to call the `if`.

## Extension hooks

`parse_item` and `parse_primary_extra` do nothing special here. Chapter 9 overrides them to add `enum` and
`match` **without editing this file**. `block_like` and `block_starts` are class attributes for the same reason.
Designing the hook points is cheap now and saves a rewrite later.

## Run it

```
python 02-parser/main.py
python 02-parser/verify.py       # chapter 2 ok
```

## The real thing

[`src/vex/parser.py`](https://github.com/0xmortuex/vex-lang/blob/main/src/vex/parser.py) has the same shape. It adds
patterns, lambdas, string interpolation (it re-lexes the text inside `{...}`), struct literals (with the
"not in an `if` condition" restriction) and panic-mode error recovery, which module 08 previews.

Next: [03 Evaluator](../03-evaluator/)
