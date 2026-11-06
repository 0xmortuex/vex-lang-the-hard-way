"""Chapter 8: turn errors (a message and an offset) into helpful output.

Three upgrades over the earlier chapters:
  1. positions: offset -> line:column, and a source snippet with a caret under the problem
  2. suggestions: "did you mean `total`?" using edit distance
  3. several errors per run: the parser resynchronises after a mistake, and each function is
     type-checked independently
"""

from __future__ import annotations

import difflib

from lexer import CompileError, LexError, lex
from ops import RunError


class Source:
    def __init__(self, path: str, text: str) -> None:
        self.path = path
        self.text = text
        self.line_starts = [0] + [i + 1 for i, ch in enumerate(text) if ch == "\n"]

    def line_col(self, pos: int) -> tuple[int, int]:
        line = 0
        for i, start in enumerate(self.line_starts):
            if start <= pos:
                line = i
        return line + 1, pos - self.line_starts[line] + 1

    def line_text(self, line: int) -> str:
        start = self.line_starts[line - 1]
        end = self.text.find("\n", start)
        return self.text[start : end if end >= 0 else len(self.text)]


def suggest(name: str, candidates: list[str]) -> str | None:
    pool = sorted({c for c in candidates if c != name})
    close = difflib.get_close_matches(name, pool, n=1, cutoff=0.6)
    return close[0] if close else None


def render(src: Source, kind: str, message: str, pos: int, help: str | None = None) -> str:
    line, col = src.line_col(pos)
    text = src.line_text(line)
    gutter = " " * len(str(line))
    out = [
        f"{kind}: {message}",
        f"{gutter}--> {src.path}:{line}:{col}",
        f"{gutter} |",
        f"{line} | {text}",
        f"{gutter} | {' ' * (col - 1)}^",
    ]
    if help:
        out.append(f"{gutter} = help: {help}")
    return "\n".join(out)


def render_error(src: Source, err: CompileError) -> str:
    help = err.help
    candidates = getattr(err, "candidates", [])
    if help is None and candidates:
        # The name is in the message between backticks: "cannot find `totl` in this scope".
        parts = err.message.split("`")
        if len(parts) >= 3:
            s = suggest(parts[1], candidates)
            if s:
                help = f"did you mean `{s}`?"
    return render(src, "error", err.message, err.pos, help)


def render_runtime_error(src: Source, err: RunError) -> str:
    out = [render(src, "runtime error", err.message, err.pos)] if err.pos >= 0 else [f"runtime error: {err.message}"]
    if err.trace:
        out.append("stack trace (most recent call first):")
        for name, pos in err.trace:
            line, col = src.line_col(pos)
            out.append(f"  in {name} at {src.path}:{line}:{col}")
    return "\n".join(out)


def diagnose(text: str, path: str = "<input>") -> list[str]:
    """Run the whole front end and return every problem found, rendered. An empty list means OK."""
    import infer
    from parser import Parser
    from recovery import RecoveringParser

    src = Source(path, text)
    try:
        tokens = lex(text)
    except LexError as e:
        return [render_error(src, e)]
    parser: Parser = RecoveringParser(tokens)
    prog = parser.parse_program()
    errors: list[CompileError] = list(getattr(parser, "errors", []))
    if errors:
        return [render_error(src, e) for e in errors]  # do not type-check a program we could not parse
    errors = infer_all(infer, prog)
    return [render_error(src, e) for e in errors]


def infer_all(infer_module, prog) -> list[CompileError]:  # type: ignore[no-untyped-def]
    """Type-check every function even if an earlier one failed."""
    checker = infer_module.Inferencer(prog)
    errors: list[CompileError] = []
    # Declare the signatures first (a bad signature is an error of its own).
    for fn in prog.fns:
        try:
            tps = {n: infer_module.TParam(n) for n in fn.tparams}
            params = [checker.convert(p.ty, tps) for p in fn.params]
            ret = checker.convert(fn.ret, tps) if fn.ret else infer_module.TVar()
            checker.sigs[fn.name] = infer_module.Sig(fn, list(tps.values()), params, ret, fn.ret is not None)
        except CompileError as e:
            errors.append(e)
    for sig in list(checker.sigs.values()):
        try:
            checker.ensure(sig)
        except CompileError as e:
            errors.append(e)
            sig.state = 2  # do not check it again
            if isinstance(infer_module.prune(sig.ret), infer_module.TVar):
                sig.ret = infer_module.NEVER  # poison: callers will not report follow-up errors
    errors.sort(key=lambda e: e.pos)
    return errors
