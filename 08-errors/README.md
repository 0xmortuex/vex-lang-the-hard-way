# Module 08: Errors

## The Concept

A compiler's most-read output is its error messages. Everything so far reports `offset 42: expected ...`,
which is correct and useless. This module upgrades three things:

1. **Where**: offset to `line:column`, the source line, and a caret under the problem.
2. **What to do**: "did you mean `total`?".
3. **How many**: report several independent problems in one run, not just the first.

```
error: cannot find `itmes` in this scope
 --> demo.vx:2:13
  |
2 |     items + itmes
  |             ^
  = help: did you mean `items`?
```

Nothing in modules 1 to 7 needed to change for the first two: they were designed to carry the information (a
`pos` on every node and token, `candidates` on name errors).

## Offsets to line and column

```python
class Source:
    line_starts = [0] + [i + 1 for i, ch in enumerate(text) if ch == "\n"]
    def line_col(self, pos): ...       # the last line start <= pos
```

`render` prints the line number, the line, and `" " * (col - 1) + "^"`. The gutter width is derived from the line
number so that line 10 and line 9 align. Compilers that print a caret with a tab in the line must copy the tab
into the padding (real Vex does); this tutorial's lexer treats tabs as ordinary whitespace and keeps the example
simple.

## "Did you mean"

```python
def suggest(name, candidates):
    return difflib.get_close_matches(name, sorted(set(candidates) - {name}), n=1, cutoff=0.6)
```

Edit-distance matching from the standard library, over the names that were *in scope* at the error (collected by
the checker in `candidates`). A wrong suggestion is worse than none, so the cutoff is conservative.

## Several errors at once

A parser that raises on the first problem hides everything after it. **Panic-mode recovery**: when a statement
fails to parse, record the error, skip tokens until a likely restart point, and carry on.

```python
try:
    node = self.parse_stmt()
except ParseError as e:
    self.errors.append(e)
    self.sync_stmt()           # skip to just after the next `;`, or stop at `}` / `fn`
    continue
```

Two rules keep this honest:

- **Always make progress.** If syncing did not consume anything, advance one token, or a bad token loops forever.
  (Vex's fuzz tests found exactly this bug in its own parser.)
- **Brace depth counts.** Skipping to the next `;` must not stop inside a nested `{ ... }`, or the recovery
  desynchronises and produces a storm of follow-up errors.

The type checker recovers differently, because it cannot "skip tokens": each **function** is checked
independently (`infer_all`). When one fails, its return type is replaced by `Never`, which unifies with
everything, so its callers do not report follow-up errors about a function that already has one. This is the
*poison type* trick; real Vex uses a dedicated error type.

A program that failed to parse is not type-checked at all: types on a half-parsed tree are guesses, and every
guess is a potential bogus message.

## Runtime errors, too

`render_runtime_error` prints the failing source line with a caret, then the stack trace from module 07 as
`in fn at file:line:col`. The same `Source` and the same `render` serve both kinds.

## Run it

```
python 08-errors/main.py        # syntax errors, type errors, a runtime error
python 08-errors/verify.py      # chapter 8 ok
```

## The real thing

[`src/vex/diagnostics.py`](https://github.com/0xmortuex/vex-lang/blob/main/src/vex/diagnostics.py) renders spans with a width
(`^^^^`), secondary spans ("declared here"), notes and help, sorts and de-duplicates diagnostics, and caps the count.
The corpus in [`tests/errors/`](https://github.com/0xmortuex/vex-lang/tree/main/tests/errors) pins down the code and exact
`line:col` of 146 different mistakes.

Next: [09 Enums and match](../09-enums-and-match/)
