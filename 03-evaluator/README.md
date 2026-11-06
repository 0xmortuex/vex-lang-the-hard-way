# Module 03: The Evaluator

## The Concept

The simplest way to run a program: walk the tree and *do* what each node says. `Num(5)` evaluates to `5`,
`Binary("+", a, b)` evaluates both sides and adds them, `Call("fib", args)` runs the function body with the
arguments bound. This is a **tree-walking interpreter**. It is slow, and it is the best possible reference:
when the bytecode VM in module 07 disagrees with it, the VM is wrong.

## Values

Plain Python: an `Int` is an `int`, a `Bool` is a `bool`, `Unit` is `None`.

## Environments

Variables live in a stack of scopes; inner scopes shadow outer ones:

```python
class Env:
    def define(self, name, value): self.scopes[-1][name] = value
    def get(self, name):           for scope in reversed(self.scopes): ...
    def assign(self, name, value): ...  # updates the *innermost scope that already has it*
```

`let` always defines in the innermost scope, `x = e` assigns to wherever `x` already lives. A block pushes a
scope on entry and pops it on exit (a `try/finally`, so an early `return` cannot leak one).

## Control flow

`if` and `while` map onto Python's. `return` is the interesting one: it can happen deep inside nested blocks
and loops, so it is implemented as an exception:

```python
class ReturnSignal(Exception): value

def call(...):
    try:
        return self.block(fn.body, env, new_scope=False)
    except ReturnSignal as r:
        return r.value
```

Using an exception for non-error control flow is a trade-off. It is the shortest correct code for a tree
walker; module 06's bytecode will replace it with a plain `RET` instruction.

`&&` and `||` must **short-circuit**: `false && boom()` never calls `boom`. They are handled before the operands
are evaluated.

## Integer semantics (`ops.py`)

Vex makes the decisions most languages leave implicit, and writes them in one file that both the evaluator and the
VM share:

- `Int` is a signed 64-bit integer, `-9223372036854775808 … 9223372036854775807`.
- `+ - *` and unary `-` that leave that range raise a runtime error: **no wraparound, no saturation, no bignum**.
- `/` truncates toward zero (`-7 / 2 == -3`; Python's `//` would give `-4`), and `%` takes the sign of the left
  operand (`-7 % 3 == -1`).
- `x / 0` and `x % 0` are runtime errors, and so is `INT_MIN / -1`, which would be `2^63`.

```python
def checked(r, op):
    if r > INT_MAX or r < INT_MIN:
        raise RunError(f"integer overflow in `{op}`")
    return r
```

Python integers never overflow, so the check is explicit and happens on every operation that can produce an
out-of-range value. A `RunError` carries the offset of the failing operation (the `Binary` node's `pos`), so
module 08 can render it with a caret.

## Stack depth

Each Vex call costs several Python frames here, so deep recursion would crash the *host* (on some Python versions
with a hard crash, not an exception). The evaluator counts calls and raises `stack overflow (more than 500 nested
calls)` first, raises Python's recursion limit so 500 Vex calls fit, and runs `main` on a thread with a 64 MB stack
so they fit in memory too. All of this is machinery to work around the tree walker's use of the host stack, which
is the main practical reason to want module 07.

## Run it

```
python 03-evaluator/main.py       # fib, a factorial that overflows, and a timing
python 03-evaluator/verify.py     # chapter 3 ok
```

## The real thing

Vex proper has no tree walker: it compiles straight to bytecode. [`src/vex/runtime.py`](https://github.com/0xmortuex/vex-lang/blob/main/src/vex/runtime.py)
and the arithmetic instructions in [`vm.py`](https://github.com/0xmortuex/vex-lang/blob/main/src/vex/vm.py) enforce the same integer rules, and
[docs/types.md](https://github.com/0xmortuex/vex-lang/blob/main/docs/types.md#integers-and-floats) states them as a contract.

Next: [04 Types](../04-types/)
