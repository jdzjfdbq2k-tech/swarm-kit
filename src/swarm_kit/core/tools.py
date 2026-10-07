"""Helpers for turning plain Python functions into LLM tool schemas."""

import inspect
import types
import typing
from typing import Any, Callable, Dict, Tuple, Union

_PRIMITIVES = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    tuple: "array",
    dict: "object",
}


def _json_type(annotation: Any) -> Dict[str, Any]:
    """Best-effort mapping of a Python type annotation to a JSON schema fragment."""
    if annotation is inspect.Parameter.empty or annotation is Any:
        return {"type": "string"}

    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    # Optional[X] / X | None -> X
    if origin is Union or (hasattr(types, "UnionType") and origin is types.UnionType):
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _json_type(non_none[0])
        return {"type": "string"}

    if origin is typing.Literal:
        return {"type": _PRIMITIVES.get(type(args[0]), "string"), "enum": list(args)}

    if origin in (list, tuple, set):
        schema: Dict[str, Any] = {"type": "array"}
        if args and args[0] is not Ellipsis:
            schema["items"] = _json_type(args[0])
        return schema

    if origin is dict:
        return {"type": "object"}

    return {"type": _PRIMITIVES.get(annotation, "string")}


def function_to_schema(func: Callable[..., Any]) -> Dict[str, Any]:
    """Build an OpenAI-style function tool schema from a Python function.

    The function's docstring becomes the description, and its type hints
    become the parameter types. Parameters without defaults are required.

    Example:
        >>> def get_weather(city: str, unit: str = "celsius") -> str:
        ...     '''Get the current weather for a city.'''
        >>> function_to_schema(get_weather)["function"]["name"]
        'get_weather'
    """
    signature = inspect.signature(func)
    try:
        hints = typing.get_type_hints(func)
    except Exception:
        hints = {}

    properties: Dict[str, Any] = {}
    required = []
    for name, param in signature.parameters.items():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        properties[name] = _json_type(hints.get(name, param.annotation))
        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": inspect.getdoc(func) or "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def normalize_tool(tool: Union[Callable[..., Any], Tuple[Dict[str, Any], Callable[..., Any]]]):
    """Accept either a bare callable or a ``(schema, callable)`` tuple."""
    if callable(tool) and not isinstance(tool, tuple):
        return function_to_schema(tool), tool
    if isinstance(tool, tuple) and len(tool) == 2 and callable(tool[1]):
        return tool[0], tool[1]
    raise TypeError(
        "Each tool must be a function or a (schema, function) tuple, got " f"{type(tool).__name__}."
    )
