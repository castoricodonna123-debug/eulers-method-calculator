from __future__ import annotations

import ast
import math
import operator
from dataclasses import dataclass

from flask import Flask, render_template, request


app = Flask(__name__)


ALLOWED_NAMES = {
    "x": 0.0,
    "y": 0.0,
    "pi": math.pi,
    "e": math.e,
}

ALLOWED_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "ln": math.log,
    "exp": math.exp,
    "abs": abs,
}

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
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
    """Small safe evaluator for classroom formulas such as x + y or sin(x) - y."""

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
                raise ValueError(f"Function '{node.func.id}' is not allowed.")
            for arg in node.args:
                self._validate(arg)
            return

        raise ValueError("Use only numbers, x, y, +, -, *, /, ^, and common functions.")

    def evaluate(self, x_value: float, y_value: float) -> float:
        return float(self._eval(self.tree.body, {"x": x_value, "y": y_value}))

    def _eval(self, node: ast.AST, values: dict[str, float]) -> float:
        if isinstance(node, ast.Constant):
            return float(node.value)

        if isinstance(node, ast.Name):
            if node.id in values:
                return values[node.id]
            return float(ALLOWED_NAMES[node.id])

        if isinstance(node, ast.BinOp):
            operation = OPERATORS[type(node.op)]
            return operation(self._eval(node.left, values), self._eval(node.right, values))

        if isinstance(node, ast.UnaryOp):
            operation = OPERATORS[type(node.op)]
            return operation(self._eval(node.operand, values))

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            function = ALLOWED_FUNCTIONS[node.func.id]
            arguments = [self._eval(arg, values) for arg in node.args]
            return float(function(*arguments))

        raise ValueError("Invalid expression.")


def solve_euler(expression: str, x0: float, y0: float, h: float, target_x: float) -> list[EulerRow]:
    if h == 0:
        raise ValueError("Step size h cannot be zero.")

    distance = target_x - x0
    if distance == 0:
        return []

    if distance * h < 0:
        raise ValueError("The step size h must move from x0 toward the target x.")

    raw_steps = distance / h
    steps = round(raw_steps)
    if not math.isclose(raw_steps, steps, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError("Target x must be reached exactly by the chosen step size.")

    if abs(steps) > 200:
        raise ValueError("Please use 200 steps or fewer.")

    evaluator = FormulaEvaluator(expression)
    rows: list[EulerRow] = []
    x_current = x0
    y_current = y0

    for n in range(abs(steps)):
        slope = evaluator.evaluate(x_current, y_current)
        next_y = y_current + h * slope
        next_x = x_current + h
        rows.append(
            EulerRow(
                n=n,
                x=x_current,
                y=y_current,
                slope=slope,
                next_x=next_x,
                next_y=next_y,
            )
        )
        x_current = next_x
        y_current = next_y

    return rows


@app.route("/", methods=["GET", "POST"])
def index():
    defaults = {
        "expression": "x + y",
        "x0": "0",
        "y0": "1",
        "h": "0.1",
        "target_x": "0.3",
    }
    result = None
    error = None
    form = defaults.copy()

    if request.method == "POST":
        form.update({key: request.form.get(key, "").strip() for key in defaults})
        try:
            rows = solve_euler(
                form["expression"],
                float(form["x0"]),
                float(form["y0"]),
                float(form["h"]),
                float(form["target_x"]),
            )
            result = {
                "rows": rows,
                "final_x": rows[-1].next_x if rows else float(form["x0"]),
                "final_y": rows[-1].next_y if rows else float(form["y0"]),
            }
        except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as exc:
            error = str(exc)

    return render_template("index.html", form=form, result=result, error=error)


if __name__ == "__main__":
    app.run(debug=False)