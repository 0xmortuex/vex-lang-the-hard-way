"""Chapter 9 demo: enums with data, match, and the exhaustiveness check."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _paths import setup  # noqa: E402

setup(9)

from diagnostics import Source, render_error  # noqa: E402
from eval_enums import run  # noqa: E402
from lexer import CompileError  # noqa: E402

SHAPES = """\
enum Shape { Circle(Int), Rect(Int, Int), Dot }

fn area(s: Shape) -> Int {
    match s {
        Circle(r) => 3 * r * r,
        Rect(w, h) => w * h,
        Dot => 0,
    }
}

fn describe(n: Int) -> Int {
    match n { 0 => 100, 1 => 200, _ => 300 }
}

fn main() {
    print(area(Circle(2)));
    print(area(Rect(3, 4)));
    print(area(Dot));
    print(Rect(1, 2));
    print(describe(1) + describe(9));
}
"""

INCOMPLETE = """\
enum Shape { Circle(Int), Rect(Int, Int), Dot }

fn area(s: Shape) -> Int {
    match s {
        Circle(r) => 3 * r * r,
        Dot => 0,
    }
}
"""

if __name__ == "__main__":
    print("\n".join(run(SHAPES)))
    print()
    try:
        run(INCOMPLETE)
    except CompileError as e:
        print(render_error(Source("shapes.vx", INCOMPLETE), e))
