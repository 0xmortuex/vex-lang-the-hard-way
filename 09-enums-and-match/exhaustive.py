"""Chapter 9: is every possible value matched by some arm? (Maranget's algorithm, small version.)

A pattern is turned into one of:
    WILD                      matches anything
    ("ctor", name, [args])    a variant, with sub-patterns
    ("lit", value)            an Int or Bool literal
`families` maps a constructor name to the list of all sibling constructors (name, arity); Bool
literals form the family {true, false}; Int literals have no finite family.
"""

from __future__ import annotations

import syntax_enums as se

WILD = ("wild",)
Pat = tuple  # type: ignore[type-arg]

BOOL_FAMILY = [(True, 0), (False, 0)]


def to_pat(p: object) -> Pat:
    if isinstance(p, se.PCtor):
        return ("ctor", p.name, [to_pat(a) for a in p.args])
    if isinstance(p, se.PLit):
        return ("lit", p.value)
    return WILD  # PWild and PVar


def key(p: Pat) -> object:
    return p[1]


def family_of(p: Pat, families: dict[str, list[tuple[str, int]]]) -> list[tuple[object, int]] | None:
    if p[0] == "ctor":
        return list(families[p[1]])
    if p[0] == "lit" and isinstance(p[1], bool):
        return list(BOOL_FAMILY)
    return None  # Int literals: infinitely many values


def specialize(rows: list[list[Pat]], name: object, arity: int) -> list[list[Pat]]:
    """Keep the rows that can match constructor `name`, replacing it with its sub-patterns."""
    out = []
    for row in rows:
        head, rest = row[0], row[1:]
        if head == WILD:
            out.append([WILD] * arity + rest)
        elif key(head) == name:
            out.append((head[2] if head[0] == "ctor" else []) + rest)
    return out


def witness(rows: list[list[Pat]], n: int, families: dict[str, list[tuple[str, int]]]) -> list[Pat] | None:
    """A list of n patterns that no row matches, or None if the rows cover everything."""
    if n == 0:
        return [] if not rows else None
    heads = [r[0] for r in rows if r[0] != WILD]
    if heads:
        family = family_of(heads[0], families)
        present = {key(h) for h in heads}
        if family is not None and all(name in present for name, _ in family):
            for name, arity in family:  # every constructor appears: look inside each one
                w = witness(specialize(rows, name, arity), arity + n - 1, families)
                if w is not None:
                    shown: Pat = ("ctor", name, w[:arity]) if heads[0][0] == "ctor" else ("lit", name)
                    return [shown, *w[arity:]]
            return None
    # Some constructor is missing from the first column: only the wildcard rows can match it.
    w = witness([r[1:] for r in rows if r[0] == WILD], n - 1, families)
    if w is None:
        return None
    if heads:
        family = family_of(heads[0], families)
        if family is not None:
            present = {key(h) for h in heads}
            name, arity = next((nm, ar) for nm, ar in family if nm not in present)
            shown = ("ctor", name, [WILD] * arity) if heads[0][0] == "ctor" else ("lit", name)
            return [shown, *w]
    return [WILD, *w]


def show(p: Pat) -> str:
    if p == WILD:
        return "_"
    if p[0] == "lit":
        return "true" if p[1] is True else "false" if p[1] is False else str(p[1])
    args = f"({', '.join(show(a) for a in p[2])})" if p[2] else ""
    return f"{p[1]}{args}"


def missing(patterns: list[object], families: dict[str, list[tuple[str, int]]]) -> str | None:
    """Describe a value the patterns fail to match, or None if they are exhaustive."""
    w = witness([[to_pat(p)] for p in patterns], 1, families)
    return None if w is None else show(w[0])
