# Module 07: The VM

## The Concept

The virtual machine is a loop: fetch the next instruction, do what it says, repeat. Because Vex's
instructions are simple and every function is a flat list, the VM is about 100 lines.

## Frames

Each call gets a **frame**: the function's code, a program counter, its local slots and its own operand stack.

```python
class Frame:
    chunk, pc, locals, stack
    locals = args + [None] * (nlocals - len(args))        # parameters are the first slots
```

Calls push a new frame; `RET` pops one and puts the result on the caller's stack. Vex recursion therefore
uses a Python *list*, not the Python call stack, so `s(5000)` (a recursion 5000 deep) works here although the
tree walker had to stop at 500 calls. The VM limits depth itself (`MAX_DEPTH`) and reports `stack overflow` as a
Vex error rather than letting Python run out of memory.

## The loop

```python
while True:
    op, arg = frame.chunk.code[frame.pc]
    frame.pc += 1
    if op == Op.CONST:   stack.append(arg)
    elif op in ARITH:    b = stack.pop(); a = stack.pop(); stack.append(arith(ARITH[op], a, b))
    elif op == Op.JMP_IF_FALSE:  if not stack.pop(): frame.pc = arg
    elif op == Op.CALL:  ... push a Frame
    elif op == Op.RET:   ... pop a Frame
```

Arithmetic calls the same `ops.arith` as the evaluator, so the integer rules (checked 64-bit, truncating division) are
written once. Reuse like that is why the two implementations can be expected to agree.

## Proving it agrees

`verify.py` runs 17 programs on **both** the tree walker and the VM and asserts identical output, then runs
seven failing programs on both and asserts they fail with the same message. This is *differential testing*:
two independent implementations of one specification check each other. Module 10 does the same with random
programs.

## Stack traces

When a `RunError` escapes the loop, `VM.run` walks the frame stack:

```python
err.trace = [(f.chunk.name, f.chunk.pos[f.pc - 1]) for f in reversed(frames)]
```

`pc - 1` is the instruction that was executing (the program counter has already moved past it). For callers it is the
`CALL` that is still waiting for its result, so the trace reads innermost first:

```
runtime error: division by zero
  in inner at offset 29        <- the `/`
  in middle at offset 62       <- the call `inner(n)`
  in main at offset 95         <- the call `middle(0)`
```

This is the payoff of `Chunk.pos` from module 06: it is one line of code here, and impossible to retrofit cleanly.

## Is it faster?

`python 07-vm/main.py` runs `fib(22)` on both:

```
tree walker  fib(22) = 17711   0.26s
bytecode VM  fib(22) = 17711   0.23s
```

Roughly equal, and that is the honest result: both are interpreters written in Python, and Python's own
dispatch dominates. The VM's advantages here are depth, traces, a place to optimise (real Vex fuses `i + 1` into one
instruction and specialises integer ops), and being the foundation for the next steps. In a language like C a bytecode
VM beats a tree walker by a large factor; do not assume the same holds in Python.

## Run it

```
python 07-vm/main.py        # timing comparison and a stack trace
python 07-vm/verify.py      # chapter 7 ok
```

## The real thing

[`src/vex/vm.py`](https://github.com/0xmortuex/vex-lang/blob/main/src/vex/vm.py) has the same loop with the hot instructions first,
frames kept as tuples on one list, closures and cells, and builtins that call back into the loop. See
[docs/vm.md](https://github.com/0xmortuex/vex-lang/blob/main/docs/vm.md) for the instruction table and `benchmarks/run.py` for honest numbers.

Next: [08 Errors](../08-errors/)
