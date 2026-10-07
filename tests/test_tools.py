from typing import List, Literal, Optional

from swarm_kit import function_to_schema


def test_function_to_schema_maps_types_and_required_params():
    def search(query: str, limit: int = 5, tags: Optional[List[str]] = None,
               mode: Literal["fast", "deep"] = "fast", score: float = 0.5, exact: bool = False):
        """Search the knowledge base."""

    schema = function_to_schema(search)
    fn = schema["function"]
    props = fn["parameters"]["properties"]
    assert fn["name"] == "search"
    assert fn["description"] == "Search the knowledge base."
    assert fn["parameters"]["required"] == ["query"]
    assert props["query"] == {"type": "string"}
    assert props["limit"] == {"type": "integer"}
    assert props["tags"] == {"type": "array", "items": {"type": "string"}}
    assert props["mode"] == {"type": "string", "enum": ["fast", "deep"]}
    assert props["score"] == {"type": "number"}
    assert props["exact"] == {"type": "boolean"}


def test_untyped_parameters_default_to_string_and_varargs_are_skipped():
    def f(a, *args, **kwargs):
        pass

    schema = function_to_schema(f)
    assert schema["function"]["parameters"]["properties"] == {"a": {"type": "string"}}
