"""Chapter 10: tools for testing a language implementation.

Three techniques that find bugs unit tests do not:
  * differential testing: two independent implementations (tree walker, VM) must agree
  * generative testing: random but well-typed programs, including ones that fail at run time
  * fuzzing: mangled programs must produce diagnostics, never a Python traceback
"""

from __future__ import annotations

import random

import evaluator
import vm
from ops import RunError

INT_CONSTS = ["0", "1", "2", "3", "7", "10", "100", "1000", "4611686018427387904", "9223372036854775807"]


# ---------------------------------------------------------------- random program generator
class Gen:
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def int_expr(self, vars: list[str], fns: list[tuple[str, int]], depth: int) -> str:
        r = self.rng
        if depth <= 0 or r.random() < 0.25:
            if vars and r.random() < 0.6:
                return r.choice(vars)
            c = r.choice(INT_CONSTS)
            return c if r.random() < 0.8 else f"(-{c})"
        kind = r.random()
        if kind < 0.55:
            op = r.choice(["+", "-", "*", "/", "%"])
            return f"({self.int_expr(vars, fns, depth - 1)} {op} {self.int_expr(vars, fns, depth - 1)})"
        if kind < 0.7:
            return f"(if {self.bool_expr(vars, fns, depth - 1)} {{ {self.int_expr(vars, fns, depth - 1)} }} " \
                   f"else {{ {self.int_expr(vars, fns, depth - 1)} }})"
        if kind < 0.85 and fns:
            name, arity = r.choice(fns)
            args = ", ".join(self.int_expr(vars, fns, depth - 1) for _ in range(arity))
            return f"{name}({args})"
        return f"(-{self.int_expr(vars, fns, depth - 1)})"

    def bool_expr(self, vars: list[str], fns: list[tuple[str, int]], depth: int) -> str:
        r = self.rng
        if depth <= 0 or r.random() < 0.5:
            op = r.choice(["<", "<=", ">", ">=", "==", "!="])
            return f"({self.int_expr(vars, fns, 0)} {op} {self.int_expr(vars, fns, 0)})"
        if r.random() < 0.2:
            return f"(!{self.bool_expr(vars, fns, depth - 1)})"
        op = r.choice(["&&", "||"])
        return f"({self.bool_expr(vars, fns, depth - 1)} {op} {self.bool_expr(vars, fns, depth - 1)})"

    def body(self, params: list[str], fns: list[tuple[str, int]]) -> str:
        r = self.rng
        vars = list(params)
        out: list[str] = ["let mut x = " + self.int_expr(vars, fns, 2) + ";"]
        vars.append("x")
        for _ in range(r.randint(0, 3)):
            kind = r.random()
            if kind < 0.4:
                out.append(f"x = {self.int_expr(vars, fns, 2)};")
            elif kind < 0.7:
                out.append(f"if {self.bool_expr(vars, fns, 1)} {{ x = {self.int_expr(vars, fns, 2)}; }}")
            else:  # a bounded loop, so every generated program terminates
                bound = r.randint(0, 5)
                out.append(f"let mut i = 0; while i < {bound} {{ x = {self.int_expr(vars + ['i'], fns, 2)}; i = i + 1; }}")
            if r.random() < 0.2:
                out.append(f"print({self.int_expr(vars, fns, 1)});")
        out.append(self.int_expr(vars, fns, 2))
        return " ".join(out)

    def program(self) -> str:
        r = self.rng
        fns: list[tuple[str, int]] = []
        parts: list[str] = []
        for k in range(r.randint(1, 4)):
            arity = r.randint(0, 3)
            params = [f"p{j}" for j in range(arity)]
            sig = ", ".join(f"{p}: Int" for p in params)
            # A function may only call functions defined before it: no recursion, so no infinite loops.
            parts.append(f"fn f{k}({sig}) -> Int {{ {self.body(params, fns)} }}")
            fns.append((f"f{k}", arity))
        calls = " ".join(f"print({self.int_expr([], fns, 2)});" for _ in range(r.randint(1, 4)))
        parts.append(f"fn main() {{ {calls} }}")
        return "\n".join(parts)


# ---------------------------------------------------------------- differential testing
def run_both(src: str) -> tuple[tuple[list[str], str | None], tuple[list[str], str | None]]:
    """Run a program on the tree walker and on the VM. Each result is (output lines, error message)."""
    results = []
    for mod in (evaluator, vm):
        lines: list[str] = []
        error: str | None = None
        try:
            if mod is evaluator:
                from parser import parse

                evaluator.Evaluator(parse(src), lines.append).run_main()
            else:
                from compiler import compile_program
                from parser import parse

                vm.VM(compile_program(parse(src)), lines.append).run_main()
        except RunError as e:
            error = e.message
        results.append((lines, error))
    return results[0], results[1]


# ---------------------------------------------------------------- fuzzing
TOKENS = ["fn", "let", "mut", "if", "else", "while", "return", "true", "false", "enum", "match", "main", "x", "Int",
          "(", ")", "{", "}", "[", "]", ",", ";", ":", "->", "=>", "=", "==", "<", "+", "-", "*", "/", "&&", "!", "1",
          "99999999999999999999", "$", "é", "//", "\n"]  # fmt: skip


def mutate(rng: random.Random, text: str) -> str:
    for _ in range(rng.randint(1, 4)):
        if not text:
            break
        i = rng.randrange(len(text))
        kind = rng.randrange(4)
        if kind == 0:
            text = text[:i] + text[i + 1 :]
        elif kind == 1:
            text = text[:i] + " " + rng.choice(TOKENS) + " " + text[i:]
        elif kind == 2:
            text = text[:i]
        else:
            j = min(len(text), i + rng.randint(1, 10))
            text = text[:i] + text[j:]
    return text
