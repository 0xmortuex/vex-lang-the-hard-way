# Break It: The Parser

## Challenge 1: Make `-` right-associative

In `parse_expr`, change `self.parse_expr(prec + 1)` to `self.parse_expr(prec)`. Run
`python 02-parser/verify.py`. Which assertions fail, and what does `10 - 4 - 3` evaluate to if you run it
(`python -c` with chapter 3's `run`)?

**Hint:** With `prec` instead of `prec + 1` the recursive call also accepts the *same* operator, so the right side
swallows `4 - 3` and you get `10 - (4 - 3) = 9` instead of `3`. Left- versus right-associativity is exactly one
character here, and a wrong choice is silent until someone subtracts three numbers.

## Challenge 2: Swap two precedence levels

Give `&&` precedence 3 and `==` precedence 2 (swap them). `a == b && c == d` should group as
`(a == b) && (c == d)`. What does it become, and what type error would a user see?

**Hint:** `==` now binds looser than `&&`, so it parses as `a == (b && c) == d` and the checker complains about
comparing a `Bool` with an `Int`, far from the real mistake. Precedence tables are tested best with a handful of
mixed expressions, as `verify.py` does.

## Challenge 3: Let `if` continue as an expression statement

Remove the `block_starts` branch in `parse_stmt` so every statement goes through `parse_expr`. Then parse
`fn f() { if a { } (b + 1) }`. What happens, and why does Rust have the same special case?

**Hint:** After the `if`, `parse_postfix` would see `(` and try to treat the `if` as a function being called
(chapter 2's `parse_postfix` only calls `Var`s, so you get a different error instead: "expected `;`"). Either way
`(b + 1)` is meant to be the next statement. The rule "a statement that starts with a block-like expression ends at
its closing brace" is how Rust, and Vex, avoid it.
