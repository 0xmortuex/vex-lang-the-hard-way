# Module 09: Enums and match

## The Concept

An **enum** is a type that is exactly one of a fixed set of variants, each carrying its own data. `match` takes
one apart. Together they are what Vex calls algebraic data types, and they replace most of what null checks,
type tags and class hierarchies do elsewhere:

```
enum Shape { Circle(Int), Rect(Int, Int), Dot }

fn area(s: Shape) -> Int {
    match s {
        Circle(r) => 3 * r * r,
        Rect(w, h) => w * h,
        Dot => 0,
    }
}
```

The payoff is that the compiler can check you handled **every** variant. Delete the `Dot` arm and:

```
error: non-exhaustive `match`
 --> shapes.vx:4:11
  |
4 |     match s {
  |           ^
  = help: pattern `Rect(_, _)` is not covered; add an arm for it or a catch-all `_`
```

## How it is added without touching old code

This chapter changes the syntax, the type checker and the evaluator, but **edits none of their files**:

| New file | Extends | Through |
|----------|---------|---------|
| `syntax_enums.py` | `syntax.py` | new node types (`EnumDecl`, `Match`, patterns) |
| `parser_enums.py` | chapter 2's `Parser` | `parse_item`, `parse_primary_extra`, `block_like` |
| `enums.py` | chapter 5's `Inferencer` | overrides `expr`, `call`, `expr_extra`, `convert` |
| `eval_enums.py` | chapter 3's `Evaluator` | overrides `eval`, `eval_extra`, `show` |
| `exhaustive.py` | (new) | the coverage algorithm |

Variants are used as functions (`Circle(2)`) and as plain names (`Dot`). In this tutorial variant names are unique
across enums and written in uppercase; real Vex also allows `Shape.Circle(2)`.

## Typing a match

For `match e { p1 => b1, p2 => b2 }`:

1. Type the scrutinee `e`. Its type is what every pattern is checked against.
2. For each arm, open a scope, **check the pattern against the scrutinee's type** (which binds the variables it
   names), then type the body. A `Circle(r)` pattern requires the scrutinee to be a `Shape` and gives `r` the type
   `Int`.
3. All arm bodies must unify with each other (an arm of type `Never`, like one that returns, fits).
4. Run the exhaustiveness check.

## Exhaustiveness: the algorithm

Question: do the arms together cover every possible value? The answer comes from a small recursive function over
a **matrix** of patterns (this is Maranget's usefulness algorithm):

```
witness(rows, n):                      # n columns left to check
    if n == 0:   return [] if rows is empty else "covered"
    look at the constructors used in the first column
    if every constructor of the type appears:
        for each constructor c:        # look inside it
            w = witness(rows narrowed to c, arity(c) + n - 1)
            if w:  return c(w[:arity]) + w[arity:]
        return "covered"
    else:
        # some constructor is missing: only the wildcard rows can match it
        w = witness(rows that start with a wildcard, with that column dropped, n - 1)
        if w:  return (a missing constructor) + w
        return "covered"
```

It returns not just yes/no but a **witness**: a value no arm matches, printed as the pattern
`Rect(_, _)`. That is what makes the error message actionable.

How the three kinds of pattern behave:

- an **enum constructor** has a finite family (`Circle`, `Rect`, `Dot`), so "every constructor appears" is decidable;
- **`true` / `false`** form a two-element family;
- an **`Int` literal** has an infinite family, so literals alone are never exhaustive and the answer is always
  "missing: `_`". You need a wildcard.

`specialize` is the interesting helper: to look inside constructor `c`, keep rows that start with `c` (replacing it by
its sub-patterns) or with a wildcard (replaced by `arity` wildcards).

## Run it

```
python 09-enums-and-match/main.py        # shapes, a 'match' on Int, and the missing-arm error
python 09-enums-and-match/verify.py      # chapter 9 ok
```

## Not here

Compiling `match` to bytecode. It is a good exercise (see `break-it.md`): test the constructor's tag, jump to the
next arm on failure, bind payload fields to slots. Real Vex does exactly this in `compiler.py`
(`cmatch` / `cpat`).

## The real thing

[`src/vex/exhaust.py`](https://github.com/0xmortuex/vex-lang/blob/main/src/vex/exhaust.py) is this algorithm, extended with
tuple and struct patterns, or-patterns, guards (arms with guards do not count towards coverage) and the *reverse*
question, "is this arm reachable?", which produces the `unreachable-pattern` warning.
Tests: [`tests/test_exhaustiveness.py`](https://github.com/0xmortuex/vex-lang/blob/main/tests/test_exhaustiveness.py).

Next: [10 Testing](../10-testing/)
