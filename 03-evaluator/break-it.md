# Break It: The Evaluator

## Challenge 1: Use Python's `//`

In `ops.arith`, replace the truncating division with `a // b` (and `a % b` with Python's `%`). Run
`python 03-evaluator/verify.py`. Which line fails, and what is `-7 / 2` now?

**Hint:** Python floors (`-7 // 2 == -4`, `-7 % 3 == 2`); Vex truncates toward zero like C, Rust and Java. Both
are defensible, but a language must pick one and say so: the assertions on `-10 / 3` and `-10 % 3` are the
specification written as code.

## Challenge 2: Remove the overflow check

Make `checked` just `return r`. Which assertions in `verify.py` fail? Run `print(9223372036854775807 + 1);` and
look at the output. Is it wrong, or merely different from what C would print?

**Hint:** Python happily prints `9223372036854775808`, a number that is not an `Int` at all. The
failure is silent: later arithmetic keeps working on a value the language says cannot exist. Checked arithmetic is
a property you only keep by testing the boundary (`INT_MAX + 1`), which is why `verify.py` does.

## Challenge 3: Evaluate both sides of `&&`

In `Evaluator.binary`, evaluate `left` and `right` first for every operator (delete the early `&&` / `||` branches
and let them fall to the generic code, adding `and`/`or` on the results). What does `false && (1 / 0 == 0)` do?

**Hint:** It crashes with `division by zero`, because the right-hand side now runs even though the left already
decides the answer. Short-circuiting is observable behaviour, not an optimisation: programs rely on
`i < len && xs[i] == 0` not indexing out of range.
