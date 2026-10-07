import pytest
from conftest import make_response, tool_call

from swarm_kit import Agent, function_to_schema


def lookup(order_id: str) -> str:
    """Look up an order."""
    return "Shipped"


def test_plain_function_tools_get_a_generated_schema():
    agent = Agent(name="A", instructions="x", tools=[lookup])
    assert agent.functions["lookup"] is lookup
    assert agent.custom_tool_schemas[0]["function"]["parameters"]["required"] == ["order_id"]


def test_tuple_tools_are_still_supported():
    schema = function_to_schema(lookup)
    agent = Agent(name="A", instructions="x", tools=[(schema, lookup)])
    assert agent.functions == {"lookup": lookup}


def test_reserved_and_duplicate_tool_names_are_rejected():
    def transfer(next_agent: str): ...

    with pytest.raises(ValueError, match="reserved"):
        Agent(name="A", instructions="x", tools=[transfer])
    with pytest.raises(ValueError, match="Duplicate"):
        Agent(name="A", instructions="x", tools=[lookup, lookup])


def test_build_kwargs_includes_state_roster_and_model_kwargs():
    agent = Agent(name="A", instructions="Be nice.", model_kwargs={"temperature": 0.1}, api_key="k")
    kwargs = agent._build_kwargs([], {"tier": "gold"}, peers={"A": "me", "B": "billing"})
    system = kwargs["messages"][0]["content"]
    assert "tier" in system and "- B: billing" in system and "- A:" not in system
    assert kwargs["temperature"] == 0.1 and kwargs["api_key"] == "k"
    names = [t["function"]["name"] for t in kwargs["tools"]]
    assert names == ["transfer", "update_state"]


def test_transfer_tool_can_be_disabled():
    agent = Agent(name="A", instructions="x")
    kwargs = agent._build_kwargs([], {}, allow_transfer=False)
    assert [t["function"]["name"] for t in kwargs["tools"]] == ["update_state"]


def test_parse_response_handles_invalid_json_arguments():
    agent = Agent(name="A", instructions="x")
    out = agent._parse_response(make_response(tool_calls=[tool_call("lookup", "{not json")]))
    assert out.tool_calls[0].arguments == {}
    assert "Invalid JSON" in out.tool_calls[0].parse_error


def test_to_message_produces_openai_tool_calls():
    agent = Agent(name="A", instructions="x")
    out = agent._parse_response(make_response("hi", [tool_call("lookup", {"order_id": "1"}, "c1")]))
    msg = out.to_message()
    assert msg["role"] == "assistant" and msg["content"] == "hi"
    assert msg["tool_calls"][0] == {
        "id": "c1",
        "type": "function",
        "function": {"name": "lookup", "arguments": '{"order_id": "1"}'},
    }
