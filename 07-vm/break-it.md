# Break It: The VM

## Challenge 1: Return into the wrong frame

In `Op.RET`, push the result onto the *callee's* stack (`stack.append(result)`) instead of the caller's, before
popping the frame. Run `python 07-vm/verify.py`. Which program fails first and what is the symptom?

**Hint:** The caller never receives its value; it pops from an empty stack and Python raises `IndexError`. Calls
and returns are where stack machines go wrong, so the programs in `verify.py` call functions inside
expressions (`fib(n - 1) + fib(n - 2)`) and check the answers.

## Challenge 2: Skip the overflow check in the VM only

In `Op.ADD` and friends, call `a + b` directly instead of `arith`. The tree walker still checks. Run
`python 07-vm/verify.py`. Which assertion catches the disagreement, and what does the VM print for `INT_MAX + 1`?

**Hint:** The "FAILING" loop runs every failing program on both implementations; the VM prints
`9223372036854775808` where the walker raises. Having an independent second implementation is what turns
"the VM forgot a check" into a failing test instead of a bug report.

## Challenge 3: Lower the depth limit and recurse

Set `MAX_DEPTH = 100` and run `vm.run("fn s(n: Int) -> Int { if n == 0 { 0 } else { n + s(n - 1) } } fn main() { print(s(500)); }")`.
Is the error a Python traceback or a Vex error? Look at `err.trace`.

**Hint:** A `RunError("stack overflow ...")` with a trace of 100 frames. The VM checks its own limit, so
runaway recursion is a diagnosable Vex error instead of a crash of the host. The check happens *before* pushing
the frame that would exceed the limit.
