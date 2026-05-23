from flask import Flask, render_template, request
import math
import ast
import operator
from dataclasses import dataclass

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

# -------------------------
# YOUR ORIGINAL LOGIC HERE
# -------------------------

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
    def __init__(self, expression: str):
        normalized = expression.replace("^", "**")
        self.tree = ast.parse(normalized, mode="eval")
        self._validate(self.tree)

    def _validate(self, node):
        if isinstance(node, ast.Expression):
            self._validate(node.body)
        elif isinstance(node, ast.Constant):
            return
        elif isinstance(node, ast.Name) and node.id in ALLOWED_NAMES:
            return
        elif isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            self._validate(node.left)
            self._validate(node.right)
        elif isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            self._validate(node.operand)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id not in ALLOWED_FUNCTIONS:
                raise ValueError("Function not allowed")
            for a in node.args:
                self._validate(a)
        else:
            raise ValueError("Invalid expression")

    def evaluate(self, x_value, y_value):
        return float(self._eval(self.tree.body, {"x": x_value, "y": y_value}))

    def _eval(self, node, values):
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            return values.get(node.id, ALLOWED_NAMES[node.id])
        if isinstance(node, ast.BinOp):
            return OPERATORS[type(node.op)](
                self._eval(node.left, values),
                self._eval(node.right, values)
            )
        if isinstance(node, ast.UnaryOp):
            return OPERATORS[type(node.op)](
                self._eval(node.operand, values)
            )
        if isinstance(node, ast.Call):
            func = ALLOWED_FUNCTIONS[node.func.id]
            return func(*[self._eval(a, values) for a in node.args])

        raise ValueError("Invalid node")


def solve_euler(expr, x0, y0, h, target_x):
    evaluator = FormulaEvaluator(expr)

    steps = int(round((target_x - x0) / h))

    rows = []
    x, y = x0, y0

    for n in range(abs(steps)):
        slope = evaluator.evaluate(x, y)
        next_x = x + h
        next_y = y + h * slope

        rows.append(EulerRow(n, x, y, slope, next_x, next_y))

        x, y = next_x, next_y

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
        form.update(request.form)

        try:
            rows = solve_euler(
                form["expression"],
                float(form["x0"]),
                float(form["y0"]),
                float(form["h"]),
                float(form["target_x"])
            )

            result = {
                "rows": rows,
                "final_y": rows[-1].next_y if rows else float(form["y0"])
            }

        except Exception as e:
            error = str(e)

    return render_template("index.html", form=form, result=result, error=error)


# 🔥 REQUIRED FOR VERCEL
application = app
