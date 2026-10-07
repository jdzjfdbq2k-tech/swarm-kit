import json

import pytest
from conftest import make_response, tool_call

from swarm_kit import Agent, Swarm, SwarmResult


def make_swarm(**kwargs):
    triage = Agent(name="Triage", instructions="Route the user.", description="Front desk")
    billing = Agent(name="Billing", instructions="Handle refunds.", tools=[refund])
    return Swarm(agents=[triage, billing], verbose=False, **kwargs)


def refund(order_number: str) -> str:
    """Process a refund."""
    return f"Refunded {order_number}"


def test_rejects_duplicate_agents_and_unknown_start_agent(llm):
    a = Agent(name="A", instructions="x")
    with pytest.raises(ValueError, match="Duplicate"):
        Swarm(agents=[a, a])
    with pytest.raises(ValueError, match="not found"):
        Swarm(agents=[a], verbose=False).execute("Nope", "hi")


def test_simple_reply_returns_result(llm):
    llm.queue(make_response("Hello!"))
    result = make_swarm().execute("Triage", "hi")
    assert isinstance(result, SwarmResult)
    assert result.final_output == "Hello!"
    assert result.last_agent == "Triage"
    assert result.history[-1] == {"role": "assistant", "content": "Hello!"}


def test_transfer_and_tool_execution_use_proper_tool_messages(llm):
    llm.queue(
        make_response(None, [tool_call("transfer", {"next_agent": "Billing"}, "t1")]),
        make_response(None, [tool_call("refund", {"order_number": "INV-9"}, "r1")]),
        make_response("Your refund is done."),
    )
    result = make_swarm().execute("Triage", "refund INV-9")

    assert result.last_agent == "Billing"
    assert result.final_output == "Your refund is done."
    tool_msgs = [m for m in result.history if m["role"] == "tool"]
    assert tool_msgs == [
        {"role": "tool", "tool_call_id": "t1", "name": "transfer", "content": "Transferred to Billing."},
        {"role": "tool", "tool_call_id": "r1", "name": "refund", "content": "Refunded INV-9"},
    ]
    # The second LLM call must be made with the Billing agent's prompt.
    assert llm.calls[1]["messages"][0]["content"].startswith("Handle refunds.")


def test_every_parallel_tool_call_gets_a_response(llm):
    llm.queue(
        make_response(None, [
            tool_call("update_state", {"key": "a", "value": "1"}, "s1"),
            tool_call("update_state", {"key": "b", "value": "2"}, "s2"),
        ]),
        make_response("done"),
    )
    result = make_swarm().execute("Triage", "go")
    assert result.state == {"a": "1", "b": "2"}
    assert [m["tool_call_id"] for m in result.history if m["role"] == "tool"] == ["s1", "s2"]


def test_invalid_transfer_is_reported_back_instead_of_ending_the_run(llm):
    llm.queue(
        make_response(None, [tool_call("transfer", {"next_agent": "Ghost"})]),
        make_response("Sorry, let me help directly."),
    )
    result = make_swarm().execute("Triage", "hi")
    tool_msg = next(m for m in result.history if m["role"] == "tool")
    assert "unknown agent 'Ghost'" in tool_msg["content"]
    assert result.final_output == "Sorry, let me help directly."


def test_tool_exceptions_and_unknown_tools_are_fed_back(llm):
    def boom() -> str:
        """Explodes."""
        raise RuntimeError("kaput")

    agent = Agent(name="A", instructions="x", tools=[boom])
    llm.queue(
        make_response(None, [tool_call("boom", {}, "b1"), tool_call("missing", {}, "m1")]),
        make_response("ok"),
    )
    result = Swarm(agents=[agent], verbose=False).execute("A", "go")
    contents = [m["content"] for m in result.history if m["role"] == "tool"]
    assert "RuntimeError: kaput" in contents[0]
    assert "not available" in contents[1]


def test_max_turns_is_respected(llm):
    llm.queue(*[make_response(None, [tool_call("update_state", {"key": "k", "value": "v"}, f"c{i}")]) for i in range(3)])
    result = make_swarm().execute("Triage", "loop", max_turns=3)
    assert result.turns == 3
    assert len(llm.calls) == 3


def test_in_memory_history_persists_between_sync_calls(llm):
    swarm = make_swarm()
    llm.queue(make_response("first"), make_response("second"))
    swarm.execute("Triage", "one")
    swarm.execute("Triage", "two")
    assert [m["content"] for m in swarm.history if m["role"] == "user"] == ["one", "two"]
    swarm.reset()
    assert swarm.history == []


def test_log_file_and_event_handler(llm, tmp_path):
    events = []
    llm.queue(make_response("hi"))
    log = tmp_path / "run.jsonl"
    make_swarm(log_file=str(log), event_handler=events.append).execute("Triage", "hello")
    lines = [json.loads(line) for line in log.read_text().splitlines()]
    assert [e["action"] for e in lines] == ["Start", "Response", "Complete"]
    assert [e["action"] for e in events] == ["Start", "Response", "Complete"]


def test_rich_markup_in_model_output_does_not_crash(llm):
    swarm = make_swarm()
    swarm.verbose = True
    llm.queue(make_response("weird [/bold] text [red]"))
    assert swarm.execute("Triage", "hi").final_output == "weird [/bold] text [red]"


async def test_async_sessions_are_isolated_and_persisted(llm):
    db = {}

    async def save(session_id, history, state):
        db[session_id] = (list(history), dict(state))

    def load(session_id):
        return db.get(session_id, ([], {}))

    swarm = make_swarm(save_handler=save, load_handler=load)
    llm.queue(make_response("for alice"), make_response("for bob"), make_response("alice again"))

    await swarm.execute_async("Triage", "I am Alice", session_id="alice")
    await swarm.execute_async("Triage", "I am Bob", session_id="bob")
    # Bob must never see Alice's history.
    assert all("Alice" not in str(m.get("content")) for m in llm.calls[1]["messages"])

    result = await swarm.execute_async("Triage", "Me again", session_id="alice")
    assert [m["content"] for m in result.history if m["role"] == "user"] == ["I am Alice", "Me again"]
    assert len(db["alice"][0]) == 4


async def test_async_tools_are_awaited(llm):
    async def fetch(url: str) -> dict:
        """Fetch a URL."""
        return {"status": 200, "url": url}

    agent = Agent(name="A", instructions="x", tools=[fetch])
    llm.queue(make_response(None, [tool_call("fetch", {"url": "x"}, "f1")]), make_response("ok"))
    result = await Swarm(agents=[agent], verbose=False).execute_async("A", "go")
    tool_msg = next(m for m in result.history if m["role"] == "tool")
    assert json.loads(tool_msg["content"]) == {"status": 200, "url": "x"}


def test_async_tool_works_from_sync_execute(llm):
    async def ping() -> str:
        """Ping."""
        return "pong"

    agent = Agent(name="A", instructions="x", tools=[ping])
    llm.queue(make_response(None, [tool_call("ping", {}, "p1")]), make_response("ok"))
    result = Swarm(agents=[agent], verbose=False).execute("A", "go")
    assert any(m.get("content") == "pong" for m in result.history)


# ------------------------------------------------------------------
# Supervised mode
# ------------------------------------------------------------------
def plan_response(steps):
    return make_response(json.dumps({"plan": steps}))


def test_execute_plan_runs_steps_in_order_without_transfer_tool(llm):
    llm.queue(
        plan_response([
            {"agent_name": "Triage", "task": "classify"},
            {"agent_name": "Ghost", "task": "ignored"},
            {"agent_name": "Billing", "task": "refund"},
        ]),
        make_response(None, [tool_call("update_state", {"key": "category", "value": "refund"}, "s1")]),
        make_response("classified"),
        make_response("refunded"),
    )
    result = make_swarm().execute_plan("I need a refund", state={"user": "u1"})

    assert [s["agent_name"] for s in result.plan] == ["Triage", "Billing"]
    assert result.state == {"user": "u1", "category": "refund"}
    assert result.final_output == "refunded"
    for call in llm.calls[1:]:
        assert "transfer" not in [t["function"]["name"] for t in call["tools"]]


def test_plan_parsing_tolerates_code_fences(llm):
    llm.queue(make_response('Sure!\n```json\n{"plan": [{"agent_name": "Triage", "task": "t"}]}\n```'), make_response("ok"))
    result = make_swarm().execute_plan("x")
    assert result.plan == [{"agent_name": "Triage", "task": "t"}]


def test_invalid_plan_raises(llm):
    llm.queue(make_response("no json here"))
    with pytest.raises(ValueError, match="valid JSON"):
        make_swarm().execute_plan("x")


async def test_execute_plan_async_uses_async_planner_and_saves(llm):
    saved = {}
    swarm = make_swarm(save_handler=lambda sid, h, s: saved.update({sid: s}))
    llm.queue(plan_response([{"agent_name": "Billing", "task": "refund"}]), make_response("done"))
    result = await swarm.execute_plan_async("refund", session_id="job1")
    assert result.final_output == "done"
    assert "job1" in saved
