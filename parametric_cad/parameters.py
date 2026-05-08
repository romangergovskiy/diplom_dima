"""Граф параметров и пересчёт в топологическом порядке."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Dict, Iterator, Optional, Set

import networkx as nx

from parametric_cad.expressions import eval_expression


def _referenced_names(expr: str) -> Set[str]:
    tree = ast.parse(expr.strip(), mode="eval")
    out: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            out.add(node.id)
    return out


@dataclass
class ParameterDef:
    name: str
    default: float
    expression: Optional[str] = None


@dataclass
class ParameterStore:
    """Хранилище параметров с зависимостями по выражениям."""

    _defs: Dict[str, ParameterDef] = field(default_factory=dict)
    _values: Dict[str, float] = field(default_factory=dict)

    def add(
        self,
        name: str,
        value: float,
        expression: Optional[str] = None,
    ) -> None:
        name = name.strip()
        self._defs[name] = ParameterDef(name, float(value), expression)
        self._values[name] = float(value)
        self.rebuild()

    def set_value(self, name: str, value: float) -> None:
        if name not in self._defs:
            raise KeyError(name)
        d = self._defs[name]
        self._defs[name] = ParameterDef(d.name, float(value), d.expression)
        self._values[name] = float(value)
        self.rebuild()

    def set_expression(self, name: str, expression: str) -> None:
        if name not in self._defs:
            raise KeyError(name)
        d = self._defs[name]
        self._defs[name] = ParameterDef(d.name, d.default, expression.strip())
        self.rebuild()

    def get(self, name: str) -> float:
        return float(self._values[name])

    def names(self) -> Iterator[str]:
        return iter(self._defs.keys())

    def _dependency_graph(self) -> nx.DiGraph:
        g = nx.DiGraph()
        for name in self._defs:
            g.add_node(name)
        for name, d in self._defs.items():
            if not d.expression:
                continue
            for ref in _referenced_names(d.expression):
                if ref in self._defs and ref != name:
                    g.add_edge(ref, name)
        return g

    def rebuild(self) -> None:
        """Пересчитывает значения параметров с выражениями (топологическая сортировка)."""
        for name, d in self._defs.items():
            if d.expression is None:
                self._values[name] = d.default

        g = self._dependency_graph()
        if not nx.is_directed_acyclic_graph(g):
            raise ValueError("циклические зависимости между параметрами")

        for name in nx.topological_sort(g):
            d = self._defs[name]
            if d.expression:
                ctx = {n: self._values[n] for n in self._defs}
                self._values[name] = eval_expression(d.expression, ctx)
