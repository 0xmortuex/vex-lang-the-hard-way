"""Chapter 2: the syntax tree. Every node remembers where it started (`pos`)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    pos: int


# ---- types written by the programmer
@dataclass
class TypeRef(Node):
    name: str  # "Int", "Bool", "Unit", or a type parameter such as "T"


# ---- expressions
@dataclass
class Num(Node):
    value: int


@dataclass
class BoolLit(Node):
    value: bool


@dataclass
class Var(Node):
    name: str


@dataclass
class Unary(Node):
    op: str
    operand: Node


@dataclass
class Binary(Node):
    op: str
    left: Node
    right: Node


@dataclass
class Call(Node):
    name: str
    args: list[Node]


@dataclass
class If(Node):
    cond: Node
    then: Block
    els: Node | None  # a Block or another If


@dataclass
class Block(Node):
    stmts: list[Node]
    tail: Node | None  # value of the block, or None for Unit


# ---- statements
@dataclass
class Let(Node):
    name: str
    mutable: bool
    ty: TypeRef | None
    init: Node


@dataclass
class Assign(Node):
    name: str
    value: Node


@dataclass
class While(Node):
    cond: Node
    body: Block


@dataclass
class Return(Node):
    value: Node | None


@dataclass
class ExprStmt(Node):
    expr: Node
    semi: bool = True  # False for the last expression of a block (its value)


# ---- items
@dataclass
class Param(Node):
    name: str
    ty: TypeRef


@dataclass
class Fn(Node):
    name: str
    tparams: list[str]
    params: list[Param]
    ret: TypeRef | None
    body: Block


@dataclass
class Program:
    fns: list[Fn]
    extra: list[Node] = field(default_factory=list)  # chapter 9 adds enums here
