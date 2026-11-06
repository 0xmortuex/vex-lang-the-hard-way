"""Chapter 10: golden-file tests. Each `x.vx` has an `x.out` with the exact expected output.

A run that ends in a runtime error contributes a final line `error: <message>`.
Programs without enums run on both the tree walker and the VM, and both must match the file.
"""

from __future__ import annotations

import pathlib

import evaluator
import vm
from ops import RunError

GOLDEN = pathlib.Path(__file__).resolve().parent / "golden"


def run_with_runner(runner, text: str) -> str:  # type: ignore[no-untyped-def]
    lines: list[str] = []
    try:
        # `runner` returns the printed lines but we want partial output on errors too, so collect ourselves.
        runner(text, lines.append)
    except RunError as e:
        lines.append(f"error: {e.message}")
    return "".join(line + "\n" for line in lines)


def eval_runner(text: str, out):  # type: ignore[no-untyped-def]
    from parser import parse

    evaluator.Evaluator(parse(text), out).run_main()


def vm_runner(text: str, out):  # type: ignore[no-untyped-def]
    from compiler import compile_program
    from parser import parse

    vm.VM(compile_program(parse(text)), out).run_main()


def enum_runner(text: str, out):  # type: ignore[no-untyped-def]
    from enums import check
    from eval_enums import EnumEvaluator
    from lexer import lex
    from parser_enums import EnumParser

    prog = EnumParser(lex(text)).parse_program()
    check(prog)
    EnumEvaluator(prog, out).run_main()


def check_golden(directory: pathlib.Path = GOLDEN) -> list[str]:
    """Run every golden program; return the names of the ones that passed."""
    passed = []
    for src_file in sorted(directory.glob("*.vx")):
        text = src_file.read_text(encoding="utf-8")
        expected = src_file.with_suffix(".out").read_text(encoding="utf-8")
        runners = [enum_runner] if "enum" in text else [eval_runner, vm_runner]
        for runner in runners:
            got = run_with_runner(runner, text)
            assert got == expected, f"{src_file.name} via {runner.__name__}:\n--- got\n{got}--- expected\n{expected}"
        passed.append(src_file.stem)
    return passed
