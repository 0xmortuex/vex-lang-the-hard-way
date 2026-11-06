# Break It: Testing

## Challenge 1: Plant a bug in the VM and find it

In `vm.py`, inside the `elif op in ARITH:` branch, add a special case before the call to `arith`:
`if op == Op.MOD: stack.append(a % b); continue` (Python's modulo takes the sign of the divisor, Vex's takes the sign
of the dividend). Run `python 10-testing/verify.py`. How many seeds does it take to notice, and what does the
failure message print?

**Hint:** Any generated program that takes a remainder of a negative number disagrees; the message shows the seed, the
whole program and both results, so you can paste it into a file and debug it. Now plant the same bug in
`ops.arith` instead, where *both* implementations share it. Does differential testing notice? (No: shared code is
invisible to it, which is why chapter 3's hand-written `-10 % 3` assertion exists.)

## Challenge 2: A generator that rarely fails

In `Gen.int_expr`, remove `"/"` and `"%"` from the operator choices and delete `4611686018427387904` and
`9223372036854775807` from `INT_CONSTS`. Run `python 10-testing/main.py` and compare the "end in a runtime error" count
with the 87 you started with.

**Hint:** It drops to 0 of 200: every generated program now succeeds, so the error paths of both implementations are barely
exercised even though the suite stays green. Measure what your generator actually produces, not just whether tests
pass.

## Challenge 3: Make the fuzz test fail on purpose

In `RecoveringParser.sync_item` (chapter 8), delete the `self.advance()` at the end of its loop body. Run
`python 10-testing/verify.py` with a timeout of a few seconds. What happens, and why is a *timeout* the right way
for a fuzz test to fail?

**Hint:** The parser stops making progress on some mangled input and the run never finishes. A fuzz harness that
waits forever tells you something is wrong; real fuzzers add a per-input time limit so they can also tell you
*which* input. Try wrapping `diagnose(text)` in a `signal.alarm(5)` (Unix) or a thread with a timeout.
