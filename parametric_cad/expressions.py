"""Безопасное вычисление арифметических выражений с именами параметров."""

from __future__ import annotations

import ast
import operator
from typing import Mapping

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def eval_expression(expr: str, variables: Mapping[str, float]) -> float:
    """Вычисляет выражение; разрешены +, -, *, /, **, скобки и имена из variables."""
    expr = expr.strip()
    if not expr:
        raise ValueError("пустое выражение")
    tree = ast.parse(expr, mode="eval")

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise KeyError(f"неизвестный параметр: {node.id}")
            return float(variables[node.id])
        raise TypeError(f"недопустимый элемент выражения: {ast.dump(node)}")

    return float(_eval(tree))
