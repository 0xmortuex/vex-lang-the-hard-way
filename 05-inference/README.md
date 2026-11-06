# Module 05: Inference

## The Concept

In module 04 the programmer wrote every type. Inference lets the compiler **work out the types you did not
write**, and it is smaller than its reputation. The whole idea:

1. When you do not know a type yet, make up a fresh **variable** for it.
2. Every constraint ("these two must be equal") is a call to `unify(a, b)`.
3. `unify` fills in variables until the types match, or fails with a mismatch.

```
fn double(n: Int) { n * 2 }          the return type is unknown:   ?r
                                      the body has type Int:        unify(?r, Int)   =>   ?r := Int
```

## Types as objects

```python
class TCon(Type):   name        # Int, Bool, Unit, Never
class TVar(Type):   ref         # unknown; `ref` is set once solved
class TParam(Type): name        # a *rigid* type parameter, from `fn id[T]`
```

`prune(t)` follows `ref` links to the current answer. `unify`:

```python
def unify(a, b):
    a, b = prune(a), prune(b)
    if a is b or a is NEVER or b is NEVER:  return
    if isinstance(a, TVar): a.ref = b; return        # solve the variable
    if isinstance(b, TVar): b.ref = a; return
    if both TCon with the same name: return
    raise Mismatch
```

That is the entire algorithm for this language. (With composite types like `List[T]` it recurses into the
parts, and checks that a variable is not being solved to a type containing itself, the *occurs check*. Real Vex
does both; see below.)

## What it buys: omitted return types

```
fn fib(n: Int) { if n < 2 { n } else { fib(n - 1) + fib(n - 2) } }      ->     fib(Int) -> Int
```

`fib`'s result starts as a variable. Its body returns `n`, an `Int`, so the variable becomes `Int`; the
recursive call `fib(n - 1)` sees the same variable and is consistent. If `f` calls `g` and `g`'s return type is
not known yet, the checker **checks `g` first** (`ensure`), on demand, so definition order does not matter.
`Sig.state` (0, 1, 2) tracks "not started / in progress / done" to cut cycles.

## Generics, the honest version

```
fn id[T](x: T) -> T { x }
fn pick[T](c: Bool, a: T, b: T) -> T { if c { a } else { b } }
```

Two ideas:

- **Inside** the function, `T` is a `TParam`: *some* type we know nothing about. It unifies only with
  itself, so `x + 1` is rejected (`cannot apply + to T and Int`) and the function is checked once for all
  possible `T`.
- **At each call**, every parameter is replaced by a fresh `TVar` (`instantiate`). `id(1)` solves its variable
  to `Int`, `id(true)` gets a different variable and solves it to `Bool`. `pick(true, 1, false)` fails because
  one variable cannot be both.

```python
mapping = {p: TVar() for p in sig.tparams}             # fresh variables for this call
for param, arg in zip(sig.params, e.args):
    self.expect(arg, substitute(param, mapping))
return substitute(sig.ret, mapping)
```

Vex only generalises **declared** type parameters. A `let` never becomes polymorphic by itself, which is why
there is no "let-polymorphism" machinery to explain (the full Hindley-Milner algorithm has it; Vex trades it for
simpler, more predictable errors).

A generic function that calls itself *without* a declared return type is rejected with a pointed message: the
result type would have to be known to instantiate the recursive call.

## Run it

```
python 05-inference/main.py       # inferred signatures, then four rejected programs
python 05-inference/verify.py     # chapter 5 ok
```

## The real thing

[`src/vex/vtypes.py`](https://github.com/0xmortuex/vex-lang/blob/main/src/vex/vtypes.py) is this chapter at full size: the same
`prune` / `unify` / `subst`, plus tuple, function and generic nominal types, the occurs check, and an error type that
unifies silently so one mistake does not cause ten messages. [`checker.py`](https://github.com/0xmortuex/vex-lang/blob/main/src/vex/checker.py)
adds *deferred constraints* ("this must be numeric") for operators whose operand type is still a variable.

Next: [06 Bytecode](../06-bytecode/)
