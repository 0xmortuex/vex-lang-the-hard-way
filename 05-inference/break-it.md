# Break It: Inference

## Challenge 1: Treat type parameters as flexible

In `unify`, add a case that lets a `TParam` unify with `Int` (in both argument orders, for example `if (isinstance(a, TParam) and b is INT) or (isinstance(b, TParam) and a is INT): return`). Run
`python 05-inference/verify.py`. Which assertion fails, and what function does the checker now wrongly accept?

**Hint:** `fn add_one[T](x: T) -> T { x + 1 }`. If `T` can be solved to `Int`, the body type-checks, but the
function claims to work for *every* `T`, so `add_one(true)` would be accepted and crash at run time. Rigid type
parameters are what make a generic function's body checkable once for all callers.

## Challenge 2: Share one variable between calls

In `Inferencer.call`, build `mapping` once per function (for example cache it on the `Sig`) instead of creating
fresh variables per call. What breaks in `id(1)` followed by `id(true)`?

**Hint:** The first call solves the shared variable to `Int`; the second then tries to unify `Int` with `Bool` and
reports an error in a perfectly good program. Instantiation is what makes generics reusable.

## Challenge 3: Drop the in-progress check

Remove the `elif not sig.declared and sig.state == 1 and sig.tparams` branch in `call`, then check
`fn f[T](x: T) { f(x) }`. What happens, and why is "unconstrained variable" a worse failure than an error message?

**Hint:** The recursive call just returns the function's own, still unknown, result variable, nothing ever
constrains it, and the checker falls back to `Unit` without telling anyone: it accepted the program by making an
answer up. Inference needs a rule for cycles: Vex says "write the return type" and reports it at the call.
