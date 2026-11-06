# Module 10: Testing a Language

## The Concept

Unit tests check the cases you thought of. A language implementation fails on the ones you did not: the
program with three nested `if`s and a shadowed variable, the number that is exactly `INT_MAX`, the stray `fn` in the
middle of a function body. This chapter is about three techniques that find those. The generator in this very
chapter found a real bug in chapter 2's parser while it was being written: a statement `if c { } (x + 1)` was parsed
as a call of the `if`.

## 1. Differential testing

You have two implementations of one language: the tree walker (module 3) and the VM (module 7). They must agree
on every program. So generate programs and compare:

```python
walker, machine = run_both(src)        # each is (printed lines, error message or None)
assert walker == machine
```

When they disagree one of them is wrong, and you do not need to know the right answer in advance. This is how
you test code whose correct output is hard to state. It also keeps both honest about *errors*: `INT_MAX + 1` must
fail with the same message on both, `1 / 0` too.

## 2. Generating programs

`testing.Gen` produces random but **well-typed** programs: integer expressions over parameters and locals,
`if` expressions, bounded `while` loops, calls to earlier functions. Two design choices make it useful:

- **It only generates what the checker accepts.** `verify.py` type-checks every generated program; if the
  generator and the checker disagree, that is a bug in one of them.
- **It terminates by construction.** Loops have constant bounds and functions only call earlier ones, so there is no
  recursion and no infinite loop. Tests that can hang are tests nobody runs.

It deliberately includes overflowing constants (`9223372036854775807`), division and modulo by values that can be
zero, so **87 of every 200 programs end in a runtime error** and both error paths are exercised. A generator whose
programs always succeed tests half a language.

Everything is seeded: a failing seed is a one-line reproduction (`Gen(random.Random(seed)).program()`).

## 3. Fuzzing the front end

Take a valid program, mangle it (delete a character, insert a token, truncate it), and feed it to `diagnose`. The
property: it returns diagnostics or accepts the program, **but never raises a Python exception**.

```python
for seed in range(300):
    text = mutate(rng, base)
    diagnose(text)            # any exception other than a reported CompileError fails the test
```

This is the test that catches parser loops like the one in module 8's `break-it.md` (Vex's own parser had one during
development; its error corpus exposed it). A compiler that prints a Python traceback on a typo has failed at its one job.

## 4. Golden files

`golden/*.vx` each have an `.out` with the exact expected output (a final `error: ...` line if the run ends in a
runtime error). They run on both the walker and the VM. They are the regression tests: slow to write, cheap to run,
and exactly right for "this output must never change by accident". The enum example runs on the enum evaluator.

## What to test, in order of value

1. Differential agreement between implementations (when you have two).
2. "Never crash" properties over mangled input.
3. Golden outputs of realistic programs.
4. Precise unit tests of the corner cases you already know (the specification as code, like the
   integer-semantics assertions in module 3).

## Run it

```
python 10-testing/main.py         # one generated program, then the three kinds of check with counts
python 10-testing/verify.py       # chapter 10 ok
python verify.py                  # the whole tutorial
```

## The real thing

[vex-lang's tests](https://github.com/0xmortuex/vex-lang/tree/main/tests) use all four: a corpus of 146 programs each
with an expected error code and `line:col`, golden outputs for the examples, a random-arithmetic property test against
Python reference semantics (`test_fuzz.py`), and 550 token-soup and mutation fuzz cases asserting only Vex diagnostics
ever come out.

That is the end. You have a lexer, parser, interpreter, checker, inferencer, compiler, VM, a diagnostics layer, algebraic
data types and a test harness. The next language is your own.
