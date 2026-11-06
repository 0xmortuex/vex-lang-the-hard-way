# Break It: The Bytecode Compiler

## Challenge 1: Forget the POP

In `stmt`, delete `self.emit(Op.POP)` after an expression statement. Run `python 06-bytecode/verify.py`, then
`python 07-vm/verify.py`. How does the damage show up, and where?

**Hint:** The shape test for `fn f() { 1; 2 }` fails immediately. Without it, the stack grows by one on every
expression statement; inside a loop that is a memory leak, and the final `RET` returns whatever is on top, which is
sometimes still right. The "every expression leaves one value" rule exists so this class of bug has one place to live.

## Challenge 2: Declare before compiling the initialiser

In `stmt`, swap the two lines for `Let` so the variable is declared first and `self.expr(st.init)` is compiled
after. What does `fn f(x: Int) -> Int { let x = x + 1; x }` return when `f(1)` runs on the VM?

**Hint:** The initialiser's `x` now resolves to the new, uninitialised slot, so you get `None + 1`, i.e. a Python
error instead of `2`. Scoping order matters: the new binding is not visible in its own initialiser.

## Challenge 3: Patch the wrong place

In `patch`, set the target to `len(self.chunk.code) - 1` instead of `len(self.chunk.code)`. Run `07-vm/verify.py`.
What breaks first?

**Hint:** Every jump lands one instruction early, executing the last instruction of the branch it should have
skipped. Off-by-one errors in jump targets are why `verify.py` checks exact instruction sequences for `if` and
`while`, and why disassemblers exist: printing `-> 0004` next to a jump makes the mistake visible.
