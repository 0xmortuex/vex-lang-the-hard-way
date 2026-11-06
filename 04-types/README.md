# Module 04: Types

## The Concept

The evaluator happily runs `1 + true` and crashes halfway through a program with a Python assertion. A
**type checker** walks the same tree *before* anything runs and proves that kind of mistake cannot happen.

This chapter is the simple version: the programmer writes every type, and the checker verifies the program
agrees with itself. No guessing, no inference. (Module 05 adds that.) It is worth building first because
everything else is a refinement of the same walk.

## Types

Just strings: `"Int"`, `"Bool"`, `"Unit"`, plus `"Never"`.

`Never` is the type of an expression that does not produce a value, like a block ending in `return`. It
**fits anywhere**: `if c { return 0; } else { 5 }` has branches of type `Never` and `Int`, and the `if` is an
`Int`. `compatible(a, b)` is the whole subtyping story:

```python
def compatible(a, b):
    return a == b or a == "Never" or b == "Never"
```

## The walk

The checker has one method per kind of node, each returning the node's type:

```python
def expr(self, e):
    Num        -> "Int"
    BoolLit    -> "Bool"
    Var        -> look the name up in the scopes
    Binary     -> check operands, return Int for + - * / %, Bool for comparisons
    Call       -> look up the signature, check argument count and types, return its result type
    If         -> condition is Bool, both branches have compatible types, result is that type
    Block      -> the type of its tail, or Unit, or Never if a statement diverges
```

Statements check what they must: a `let` with an annotation must match its initialiser, an assignment needs a
`mut` variable of the same type, `return e` must match the function's declared result type, `while` needs a
`Bool` condition.

Two details that look small and are not:

- **Signatures first.** `check_program` collects every function's signature before checking any body, so
  `fn f() -> Int { g() }` may call a `g` defined later.
- **Operand rules.** `+` needs `Int` on both sides. `==` accepts `Int == Int` and `Bool == Bool` but not
  `Unit == Unit`: the evaluator can only compare numbers, and a checker that allows what the evaluator cannot run
  has a hole.

## Errors know what they were looking for

```
fn f(n: Int) -> Bool { n + 1 }
    offset 25: function `f` should return `Bool` but its body has type `Int`
```

`TypeError_` carries a message, the position, and `candidates`: for "cannot find `totl`" it lists every name in
scope. The checker does not suggest anything itself. It just keeps the evidence so module 08 can say
"did you mean `total`?".

## Run it

```
python 04-types/main.py        # good program's signatures, then six rejected programs
python 04-types/verify.py      # chapter 4 ok
```

## The real thing

Vex's checker ([`src/vex/checker.py`](https://github.com/0xmortuex/vex-lang/blob/main/src/vex/checker.py)) has the same structure:
one `infer_*` method per node kind, signatures collected first, `Never` for diverging code, and per-error positions.
The type rules are written down in [docs/types.md](https://github.com/0xmortuex/vex-lang/blob/main/docs/types.md).

Next: [05 Inference](../05-inference/)
