# Vex — The Hard Way

Build a small statically typed language from nothing: lexer, parser, interpreter, type checker,
type inference, bytecode compiler, virtual machine, good error messages, enums with exhaustive
`match`, and a test strategy that finds real bugs. About 2,300 lines of plain Python (comments included), no
dependencies, every chapter runnable and self-checking.

At the end you will have built a miniature of [Vex](https://github.com/0xmortuex/vex-lang), and you
will understand the parts of a compiler that most tutorials skip: **what the type checker does when
it is wrong, how errors keep the user sane, and how to know your two implementations agree.**

## Why this exists

Most "make a language" tutorials stop at a calculator or a tree-walking interpreter with no types.
The interesting problems come after that:

- a type checker must report the *first useful* error and keep going, not explode
- inference is just unification, and it is smaller than you think
- a bytecode VM is only worth having if you can prove it behaves like the reference interpreter
- "integer overflow is undefined" is a decision you have to make on purpose

## Who this is for

Developers who can read Python and have used a typed language. No compiler theory needed; every term
is explained where it first appears. You need Python 3.10 or newer. There is nothing to install.

## The language you will build

```
enum Shape { Circle(Int), Rect(Int, Int), Dot }

fn area(s: Shape) -> Int {
    match s {
        Circle(r) => 3 * r * r,
        Rect(w, h) => w * h,
        Dot => 0,
    }
}

fn gcd(a: Int, b: Int) -> Int {            // return types can be inferred; generics are `fn id[T](x: T) -> T`
    if b == 0 { a } else { gcd(b, a % b) }
}

fn main() {
    let mut i = 0;
    while i < 3 { print(area(Rect(i, 4)) + gcd(12, 18)); i = i + 1; }
}
```

`Int` (checked 64-bit), `Bool`, `Unit`, functions, `let` / `let mut`, `if` / `while`, enums, `match`.
It is deliberately the *core* of Vex: no strings, lists or closures, so each idea fits on a page.

## Modules

| # | Module | What you build |
|---|--------|----------------|
| 01 | [Lexer](01-lexer/) | Turn source text into tokens with positions |
| 02 | [Parser](02-parser/) | Recursive descent plus a Pratt loop for operators; the syntax tree |
| 03 | [Evaluator](03-evaluator/) | A tree-walking interpreter, and Vex's integer semantics |
| 04 | [Types](04-types/) | A checker where every type is written down |
| 05 | [Inference](05-inference/) | Unification, inferred return types, generic functions |
| 06 | [Bytecode](06-bytecode/) | Compile the tree to a stack machine's instructions |
| 07 | [The VM](07-vm/) | Execute them; stack traces; prove it matches the evaluator |
| 08 | [Errors](08-errors/) | Line:column, carets, "did you mean", several errors per run |
| 09 | [Enums and match](09-enums-and-match/) | Data-carrying enums, patterns, exhaustiveness checking |
| 10 | [Testing](10-testing/) | Differential testing, program generators, fuzzing, golden files |

## How the chapters fit together

Each chapter folder contains only the **new** files for that chapter. Later chapters reuse the earlier
files unchanged, and extend them through small hooks (`parse_item`, `parse_primary_extra`, `eval_extra`,
`expr_extra`) instead of copying them. `_paths.py` puts chapters 1..N on the import path, newest first,
so `import parser` finds chapter 2's parser and chapter 9's `parser_enums` builds on it.

Every folder has:

- `README.md`: the concept and the code, explained
- `main.py`: a demo that prints something worth looking at
- `verify.py`: assertions that the chapter's code does what the chapter says (this is the "test")
- `break-it.md`: experiments that change the code on purpose to see what fails and why

```text
python verify.py          # run every chapter's verify.py and main.py
python verify.py 05 07    # just these
python 07-vm/main.py      # one demo
```

## The real thing

[vex-lang](https://github.com/0xmortuex/vex-lang) is the full language this tutorial shrinks: strings and
interpolation, lists, maps, tuples, structs, generic enums, closures, `Option` / `Result` with `?`, modules,
a REPL, a type-error corpus with exact positions and a fuzz suite. Each chapter ends with a pointer to the
file in vex-lang where the same idea lives at full size.

## License

MIT. See [LICENSE](LICENSE).
