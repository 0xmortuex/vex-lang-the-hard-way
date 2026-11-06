# Break It: Enums and match

## Challenge 1: Trust the arms

In `EnumInferencer.match`, delete the exhaustiveness check (the `w = missing(...)` block). Run
`python 09-enums-and-match/verify.py`, then run a `match` that leaves out a variant and call the function with
that variant. What does the evaluator do, and who is blamed?

**Hint:** The type checker accepts the program; at run time the evaluator reaches the end of the arms and raises
`no match arm matched`. A runtime error in code the compiler "approved" is exactly what exhaustiveness checking exists
to prevent. The evaluator's fallback is a safety net, not a design.

## Challenge 2: Make Int literals exhaustive

In `family_of`, return `[(0, 0), (1, 0)]` for `Int` literals as though `0` and `1` were the only integers. Then check
`match n { 0 => 1, 1 => 2 }`. Why is this wrong, and which of `verify.py`'s lines catches it?

**Hint:** The family is infinite (`2`, `-7`, ...), so literals can never cover the type by themselves. The assertion
`missing([PLit(1), PLit(2)], {}) == "_"` fails. Exhaustiveness is only sound if each constructor family is described
exactly.

## Challenge 3: Compile a match (the exercise)

Add `se.Match` support to the bytecode compiler by extending `FnCompiler.expr_extra` in a new file, and teach the VM an
`IS_TAG` instruction. A sketch:

```
    <scrutinee>        STORE tmp
arm1:
    LOAD tmp; IS_TAG "Circle"; JMP_IF_FALSE arm2
    LOAD tmp; GET_FIELD 0; STORE r         # bind the payload to a slot
    <body>; JMP end
arm2: ...
end:
```

Enum values need a runtime representation (a Python object with a name and a field list works). Check yourself with
chapter 10's differential testing: your VM must agree with `EnumEvaluator` on every program.

**Hint:** Real Vex (`src/vex/compiler.py`, `cmatch`) does the same, and puts a `PANIC` after the last arm as the
unreachable fall-through.
