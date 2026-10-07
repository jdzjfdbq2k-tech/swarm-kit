"""Shared fixtures: a scripted fake LLM so tests never hit the network."""

import json
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest


def tool_call(name: str, arguments: Any, call_id: Optional[str] = None) -> Dict[str, Any]:
    args = arguments if isinstance(arguments, str) else json.dumps(arguments)
    return {"id": call_id or f"call_{name}", "name": name, "arguments": args}


def make_response(content: Optional[str] = None, tool_calls: Optional[List[Dict[str, Any]]] = None):
    calls = None
    if tool_calls:
        calls = [
            SimpleNamespace(id=c["id"], function=SimpleNamespace(name=c["name"], arguments=c["arguments"]))
            for c in tool_calls
        ]
    message = SimpleNamespace(content=content, tool_calls=calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeLLM:
    """Returns pre-scripted responses in order and records every request."""

    def __init__(self):
        self.responses: List[Any] = []
        self.calls: List[Dict[str, Any]] = []

    def queue(self, *responses):
        self.responses.extend(responses)

    def _next(self, kwargs):
        # Snapshot messages: the swarm keeps appending to the same list.
        self.calls.append({**kwargs, "messages": [dict(m) for m in kwargs.get("messages", [])]})
        if not self.responses:
            raise AssertionError("FakeLLM ran out of scripted responses")
        return self.responses.pop(0)

    def completion(self, **kwargs):
        return self._next(kwargs)

    async def acompletion(self, **kwargs):
        return self._next(kwargs)


@pytest.fixture
def llm(monkeypatch):
    fake = FakeLLM()
    import swarm_kit.core.agent as agent_mod
    import swarm_kit.core.swarm as swarm_mod

    monkeypatch.setattr(agent_mod, "completion", fake.completion)
    monkeypatch.setattr(agent_mod, "acompletion", fake.acompletion)
    monkeypatch.setattr(swarm_mod, "completion", fake.completion)
    monkeypatch.setattr(swarm_mod, "acompletion", fake.acompletion)
    return fake


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Keep .swarm_runs.jsonl and generated files out of the repo."""
    monkeypatch.chdir(tmp_path)
