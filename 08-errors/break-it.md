# Break It: Errors

## Challenge 1: Recovery that does not move

In `RecoveringParser.parse_block`, delete the two lines `if self.i == before: self.advance()`. Then call
`diagnose("fn f() { fn }")` (give it a timeout, or press Ctrl-C). What happens?

**Hint:** A stray `fn` inside a body is not a statement, `sync_stmt` treats `fn` as a restart point and stops
without consuming it, and the loop parses the same bad token again forever. Every error-recovery loop needs a
progress guarantee. `verify.py` feeds `fn f() { fn }` and other garbage to catch this.

## Challenge 2: Keep type-checking after a parse error

In `diagnose`, delete the `if errors: return ...` line so a program with syntax errors is also type-checked.
Run `diagnose("fn main() { let a = ; let b = a + true; }")`. How many messages do you get, and are they all
useful?

**Hint:** The statement `let a = ;` was dropped by recovery, so `a` is undefined and the second statement adds a
bogus "cannot find `a`" next to the real syntax error. Messages caused by an earlier message are noise: users fix
the first one and the rest vanish, but they cost trust.

## Challenge 3: A suggestion for everything

In `suggest`, change `cutoff=0.6` to `cutoff=0.0`. Run `python 08-errors/verify.py`. Which assertion fails, and
what would the compiler now say about a variable called `zzz` in a program that has `total` and `count`?

**Hint:** `suggest("zzz", ["total", "count"])` returns a name instead of `None`, so the user is told
"did you mean `total`?" about something unrelated. A wrong hint is worse than none: it teaches people to ignore
all of them. The cutoff is a tuning knob you test at both ends.
