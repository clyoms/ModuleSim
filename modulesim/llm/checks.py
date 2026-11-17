"""Two small safety checks applied to every AI call.

shape_problems: checks an AI answer has the fields and types the schema asks
for. It covers the subset of JSON Schema the prompts use (object, array,
string, integer, number, boolean, required, enum). It is not a full
validator, and it does not need to be.

redact: removes email addresses and student numbers from anything sent to an
outside provider (Part 1, Risk 3).
"""

import re

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
}


def shape_problems(value, schema: dict, path: str = "answer") -> list[str]:
    problems: list[str] = []
    expected = schema.get("type")
    if expected:
        py_type = _TYPES[expected]
        # In Python, True counts as an int. Reject it for numbers.
        if isinstance(value, bool) and expected in ("integer", "number"):
            return [f"{path} should be {expected}, got boolean"]
        if not isinstance(value, py_type):
            return [f"{path} should be {expected}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        problems.append(f"{path} must be one of {schema['enum']}, got {value!r}")
    if expected == "object":
        for key in schema.get("required", []):
            if key not in value:
                problems.append(f"{path}.{key} is missing")
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                problems += shape_problems(value[key], sub, f"{path}.{key}")
    if expected == "array" and "items" in schema:
        for i, item in enumerate(value):
            problems += shape_problems(item, schema["items"], f"{path}[{i}]")
    return problems


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# UCC student numbers are nine digits. Any run of 8 to 10 digits is removed.
_STUDENT_NUMBER = re.compile(r"(?<!\d)\d{8,10}(?!\d)")


def redact(text: str) -> str:
    text = _EMAIL.sub("[email removed]", text)
    return _STUDENT_NUMBER.sub("[number removed]", text)


def redact_data(value):
    """Apply redact to every string inside a dict or list."""
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {k: redact_data(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_data(v) for v in value]
    return value
