# Break It: The Type Checker

## Challenge 1: Forget that `Never` fits everywhere

Make `compatible` just `return a == b`. Run `python 04-types/verify.py`. Which program no longer type-checks, and
why is it a perfectly good program?

**Hint:** `fn f(n: Int) -> Int { if n < 1 { return 0; } n }`. A block whose statement is `return 0;` has type
`Never` for that statement, and the `if` without an else needs `Unit`, so without the `Never` rule the checker
rejects valid code. Bottom types are the oil in a type checker: nothing works without them and nobody sees them.

## Challenge 2: Check function bodies in source order, signatures as you go

In `check_program`, move the `self.sigs[fn.name] = ...` line into the second loop (just before
`self.check_fn(fn)`), so each signature is registered right before its body is checked. Which test fails?

**Hint:** A function that calls one defined *below* it fails with "cannot find function". Mutual recursion
becomes impossible. Two passes (declare everything, then check everything) is the standard fix, and it is the
reason `check_program` has two loops.

## Challenge 3: Let `==` compare anything

Delete the `left not in ("Int", "Bool", "Never")` check from `binary`. Then feed chapter 3's evaluator
(`from evaluator import run`) the program `fn g() { } fn main() { print(g() == g()); }`, which compares two
`Unit` values. What happens, and which layer should have caught it?

**Hint:** The checker accepts the program and the evaluator hits a failed `assert isinstance(a, int)`: a Python
error instead of a Vex diagnostic. Every operation the evaluator or VM cannot execute must be ruled out by the
checker. The two layers have to agree on the language.
