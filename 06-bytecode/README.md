# Module 06: Bytecode

## The Concept

The tree walker re-examines the tree every time it runs a node. A **bytecode compiler** does that work once:
it flattens each function into a list of tiny instructions for an imaginary stack machine, and a loop (module 07)
executes them. The flat form is faster to run, easy to inspect, has no recursion in the host language, and gives
you a place to attach per-instruction source positions.

## A stack machine in one picture

`1 + 2 * 3` becomes

```
CONST 1     stack: 1
CONST 2     stack: 1 2
CONST 3     stack: 1 2 3
MUL         stack: 1 6          pops two, pushes the product
ADD         stack: 7
```

Operands are found on the stack, not named. That makes the compiler almost mechanical: compile the left side,
compile the right side, emit the operator.

## The one rule

> **Every expression leaves exactly one value on the stack.** (Unit is `None`.)

Statements that do not want the value follow the expression with `POP`. `print(x)` leaves `Unit` (a `CONST None`
after the `PRINT`). A `while` loop is a statement, so it leaves nothing, but its body is a block, which is an
expression, so each iteration ends in `POP`. With this rule you never have to track stack depth.

## The instruction set (`bytecode.py`)

| Group | Instructions |
|-------|--------------|
| values | `CONST v`, `LOAD slot`, `STORE slot`, `POP` |
| arithmetic | `ADD SUB MUL DIV MOD NEG` |
| logic | `NOT`, `EQ NE LT LE GT GE` |
| jumps | `JMP`, `JMP_IF_FALSE`, `JMP_IF_FALSE_KEEP`, `JMP_IF_TRUE_KEEP` |
| calls | `CALL (name, argc)`, `RET`, `PRINT` |

Local variables live in numbered **slots** of the function's frame. The compiler maps names to slots at compile
time, so the VM never looks up a string. Every `let` gets a fresh slot, even when it shadows another, which
is what makes `let x = x + 1` work: compile the initialiser first (it sees the old `x`), then declare the new one.

## Control flow is jumps

`if c { a } else { b }` has no machinery of its own:

```
    <c>
    JMP_IF_FALSE  else        pops the condition
    <a>
    JMP           end
else:
    <b>
end:
```

The compiler emits the jump with a placeholder target and **patches** it once it knows where the label is:

```python
else_jump = self.emit(Op.JMP_IF_FALSE)       # target unknown yet
...
self.patch(else_jump)                          # target := the next instruction to be emitted
```

`while` jumps back to the top. `a && b` is `<a> JMP_IF_FALSE_KEEP end <b> end:` where the `_KEEP` variants leave
the tested value on the stack when they jump (it becomes the result) and pop it when they fall through. That is
all short-circuiting is.

## Source positions

`Chunk.pos[i]` is the source offset of instruction `i`. It costs one list and buys real stack traces in
module 07. Skipping it "to keep the compiler simple" is something you cannot add cheaply later.

## Run it

```
python 06-bytecode/main.py        # disassembly of fib and a loop
python 06-bytecode/verify.py      # chapter 6 ok
```

## The real thing

[`src/vex/compiler.py`](https://github.com/0xmortuex/vex-lang/blob/main/src/vex/compiler.py) is this compiler plus closures
(captured variables), patterns (`match` compiles to tag tests and jumps), `for` loops over an iterator, and
fused instructions like `ADDK_L` for `i + 1`. The instruction table is in [docs/vm.md](https://github.com/0xmortuex/vex-lang/blob/main/docs/vm.md).

Next: [07 The VM](../07-vm/)
