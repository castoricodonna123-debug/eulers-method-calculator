from __future__ import annotations

import ast
import math
import operator
from dataclasses import dataclass

from flask import Flask, render_template, request

app = Flask(__name__)

ALLOWED_NAMES = {"x": 0.0, "y": 0.0, "pi": math.pi, "e": math.e}
ALLOWED_FUNCTIONS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "sqrt": math.sqrt, "log": math.log, "ln": math.log,
    "exp": math.exp, "abs": abs,
}
OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

@dataclass
class EulerRow:
    n: int
    x: float
    y: float
    slope: float
    next_x: float
    next_y: float


class FormulaEvaluator:
    def __init__(self, expression: str):
        normalized = expression.replace("^", "**")
        self.tree = ast.parse(normalized, mode="eval")
        self._validate(self.tree)

    def _validate(self, node: ast.AST) -> None:
        if isinstance(node, ast.Expression):
            self._validate(node.body)
            return
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return
        if isinstance(node, ast.Name) and node.id in ALLOWED_NAMES:
            return
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            self._validate(node.left)
            self._validate(node.right)
            return
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            self._validate(node.operand)
            return
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id not in ALLOWED_FUNCTIONS:
                raise ValueError("Function not allowed.")
            return
        raise ValueError("Invalid expression.")

    def evaluate(self, x_value: float, y_value: float) -> float:
        return float(self._eval(self.tree.body, {"x": x_value, "y": y_value}))

    def _eval(self, node, values):
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            return values[node.id]
        if isinstance(node, ast.BinOp):
            return OPERATORS[type(node.op)](
                self._eval(node.left, values),
                self._eval(node.right, values)
            )
        if isinstance(node, ast.Call):
            func = ALLOWED_FUNCTIONS[node.func.id]
            args = [self._eval(a, values) for a in node.args]
            return func(*args)


def solve_euler(expression, x0, y0, h, target_x):
    evaluator = FormulaEvaluator(expression)

    steps = int(round((target_x - x0) / h))

    rows = []
    x, y = x0, y0

    for i in range(steps):
        slope = evaluator.evaluate(x, y)
        new_y = y + h * slope
        new_x = x + h

        rows.append(EulerRow(i, x, y, slope, new_x, new_y))

        x, y = new_x, new_y

    return rows


@app.route("/", methods=["GET", "POST"])
def index():
    form = {
        "expression": "x + y",
        "x0": "0",
        "y0": "1",
        "h": "0.1",
        "target_x": "0.3",
    }

    result = None
    error = None

    if request.method == "POST":
        try:
            rows = solve_euler(
                request.form["expression"],
                float(request.form["x0"]),
                float(request.form["y0"]),
                float(request.form["h"]),
                float(request.form["target_x"]),
            )

            result = {
                "rows": rows,
                "final_y": rows[-1].next_y if rows else float(request.form["y0"])
            }

        except Exception as e:
            error = str(e)

    return render_template("index.html", form=form, result=result, error=error)


if __name__ == "__main__":
    app.run(debug=True)
