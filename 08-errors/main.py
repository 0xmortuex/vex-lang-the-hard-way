"""Chapter 8 demo: what good error messages look like."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(8)

import vm  # noqa: E402
from diagnostics import Source, diagnose, render_runtime_error  # noqa: E402
from ops import RunError  # noqa: E402

BAD_SYNTAX = """\
fn main() {
    let a = ;
    let b = 2;
    let c = 3 +;
}
"""

BAD_TYPES = """\
fn total(items: Int) -> Int {
    items + itmes
}

fn label(n: Int) -> Bool {
    n + 1
}

fn main() {
    let x: Bool = total(3);
}
"""

BOOM = """\
fn inner(n: Int) -> Int { 10 / n }
fn main() {
    print(inner(0));
}
"""

if __name__ == "__main__":
    for title, text in [("syntax errors", BAD_SYNTAX), ("type errors", BAD_TYPES)]:
        print(f"--- {title}")
        for d in diagnose(text, "demo.vx"):
            print(d)
            print()
    print("--- runtime error")
    try:
        vm.run(BOOM)
    except RunError as e:
        print(render_runtime_error(Source("demo.vx", BOOM), e))
