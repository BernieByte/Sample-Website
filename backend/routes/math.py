import ast
import re
from fractions import Fraction

from flask import Blueprint, jsonify, request, session


math_bp = Blueprint("math", __name__, url_prefix="/api")


class InvalidMathInput(ValueError):
    pass


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidMathInput("Use numbers and arithmetic operators in the expression.")
    result = Fraction(str(value))
    if result.denominator.bit_length() > 256 or result.numerator.bit_length() > 256:
        raise InvalidMathInput("That expression is too large to solve safely.")
    return result


def _combine(left, right, operation):
    a, avar = left
    b, bvar = right
    if isinstance(operation, ast.Add):
        return a + b, avar + bvar
    if isinstance(operation, ast.Sub):
        return a - b, avar - bvar
    if isinstance(operation, ast.Mult):
        if avar and bvar:
            raise InvalidMathInput("Only linear equations are supported; this equation has multiplied variables.")
        return a * b, avar * b + bvar * a
    if isinstance(operation, ast.Div):
        if bvar:
            raise InvalidMathInput("A variable cannot be used as a denominator in this solver.")
        if b == 0:
            raise InvalidMathInput("Division by zero is undefined.")
        return a / b, avar / b
    if isinstance(operation, ast.Pow):
        if bvar or b.denominator != 1 or abs(b) > 100:
            raise InvalidMathInput("Use a whole-number exponent from -100 to 100.")
        exponent = int(b)
        if avar and exponent not in {0, 1}:
            raise InvalidMathInput("Only linear equations are supported; variable powers above 1 are nonlinear.")
        if a == 0 and exponent < 0:
            raise InvalidMathInput("Zero cannot be raised to a negative power.")
        return a ** exponent, avar if exponent == 1 else Fraction(0)
    raise InvalidMathInput("That operator is not supported. Try +, -, *, /, ^, and parentheses.")


def _parse(node):
    if isinstance(node, ast.Expression):
        return _parse(node.body)
    if isinstance(node, ast.Constant):
        return _number(node.value), Fraction(0)
    if isinstance(node, ast.Name):
        if node.id.lower() == "pi":
            raise InvalidMathInput("Pi is not supported in exact arithmetic yet. Use a decimal approximation.")
        return Fraction(0), Fraction(1)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value, coefficient = _parse(node.operand)
        return (value, coefficient) if isinstance(node.op, ast.UAdd) else (-value, -coefficient)
    if isinstance(node, ast.BinOp):
        return _combine(_parse(node.left), _parse(node.right), node.op)
    raise InvalidMathInput("Use a number expression or a linear equation such as 2x + 3 = 7.")


def _format_fraction(value):
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def solve_math_input(raw):
    if not isinstance(raw, str) or not raw.strip():
        raise InvalidMathInput("Enter or select a math expression first.")
    if len(raw) > 300:
        raise InvalidMathInput("Please keep the expression under 300 characters.")
    expression = raw.strip().replace("×", "*").replace("÷", "/").replace("−", "-").replace("^", "**")
    # Accept familiar forms such as 2x and 2(x + 1) by inserting explicit multiplication.
    expression = re.sub(r"(?<=[0-9)])\s*(?=[A-Za-z(])", "*", expression)
    expression = re.sub(r"(?<=[A-Za-z])\s*(?=[0-9(])", "*", expression)
    if any(character.isalpha() for character in expression):
        if not re.fullmatch(r"[A-Za-z0-9_+\-*/().=\s*]+", expression):
            raise InvalidMathInput("That text contains unsupported symbols or words.")
        if any(len(name) > 1 and name.lower() != "pi" for name in re.findall(r"[A-Za-z_]+", expression)):
            raise InvalidMathInput("That looks like text rather than a math expression. Use a one-letter variable such as x.")
    else:
        if not re.fullmatch(r"[0-9+\-*/().=\s*]+", expression):
            raise InvalidMathInput("That text is not a supported math expression.")

    if expression.count("=") > 1:
        raise InvalidMathInput("Enter one equation with a single equals sign.")
    try:
        if "=" not in expression:
            tree = ast.parse(expression, mode="eval")
            value, coefficient = _parse(tree)
            if coefficient:
                raise InvalidMathInput("Use an equals sign to solve for a variable, for example x + 2 = 5.")
            return {"kind": "calculation", "answer": _format_fraction(value)}

        left_text, right_text = expression.split("=", 1)
        left = _parse(ast.parse(left_text, mode="eval"))
        right = _parse(ast.parse(right_text, mode="eval"))
    except (SyntaxError, ZeroDivisionError, OverflowError):
        raise InvalidMathInput("I couldn't read that as a valid math expression. Check the operators and parentheses.")

    # A single variable symbol is supported for linear equations.
    names = {
        node.id
        for tree in (ast.parse(left_text, mode="eval"), ast.parse(right_text, mode="eval"))
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }
    if not names:
        left_value, left_coefficient = left
        right_value, right_coefficient = right
        if left_coefficient or right_coefficient:
            raise InvalidMathInput("Use one variable (such as x) in a linear equation.")
        if left_value == right_value:
            return {"kind": "equation", "answer": f"Both sides equal {_format_fraction(left_value)}."}
        return {"kind": "equation", "answer": f"The equation is false: {_format_fraction(left_value)} ≠ {_format_fraction(right_value)}."}
    if len(names) != 1:
        raise InvalidMathInput("Use one variable (such as x) in a linear equation.")
    coefficient = left[1] - right[1]
    constant = right[0] - left[0]
    variable = next(iter(names))
    if coefficient == 0:
        if constant == 0:
            return {"kind": "equation", "answer": "Every value satisfies this equation."}
        return {"kind": "equation", "answer": "No solution."}
    return {"kind": "equation", "answer": f"{variable} = {_format_fraction(constant / coefficient)}"}


@math_bp.route("/math/solve", methods=["POST"])
def solve():
    if "user_id" not in session:
        return jsonify({"error": "Authentication required."}), 401
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Send a math expression to solve."}), 400
    try:
        return jsonify(solve_math_input(data.get("expression")))
    except InvalidMathInput as error:
        return jsonify({"error": str(error)}), 400
