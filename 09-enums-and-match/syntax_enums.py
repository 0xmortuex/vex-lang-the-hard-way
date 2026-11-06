"""Chapter 9: new syntax nodes for enums and `match`."""

from __future__ import annotations

from dataclasses import dataclass

from syntax import Node, TypeRef


@dataclass
class Variant(Node):
    name: str
    fields: list[TypeRef]


@dataclass
class EnumDecl(Node):
    name: str
    variants: list[Variant]


# ---- patterns
@dataclass
class PWild(Node):
    pass


@dataclass
class PVar(Node):
    name: str


@dataclass
class PLit(Node):
    value: int | bool


@dataclass
class PCtor(Node):
    name: str
    args: list[Node]


@dataclass
class Arm(Node):
    pat: Node
    body: Node


@dataclass
class Match(Node):
    scrut: Node
    arms: list[Arm]
