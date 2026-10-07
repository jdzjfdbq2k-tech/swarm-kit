# Execution Modes

Swarm Kit supports two ways of coordinating agents. Both have a sync and an async version,
and both return a [`SwarmResult`](../api.md#swarmresult).

| | Unsupervised | Supervised |
| --- | --- | --- |
| Sync | `swarm.execute(start_agent_name, user_input)` | `swarm.execute_plan(user_input)` |
| Async | `await swarm.execute_async(...)` | `await swarm.execute_plan_async(...)` |
| Who decides the flow | The agents, by calling `transfer` | A planner LLM, before any agent runs |
| Good for | Chat, support, open-ended tasks | Pipelines, reports, ETL-style jobs |

## Unsupervised mode

You choose the first agent. Each turn:

1. the current agent is called with the history and the state;
2. if it replies with **no tool calls**, the run is complete;
3. otherwise each tool call runs and its result is added to the history. A `transfer`
   switches the current agent, and the loop continues.

```python
result = swarm.execute(
    start_agent_name="Triage",
    user_input="My invoice is wrong",
    state={"plan": "pro"},   # optional initial state
    max_turns=15,            # safety limit on LLM calls
)
```

A transfer to an unknown agent, or to the current agent, returns an error to the model. It
does not end the run. If `max_turns` is reached, an `Error` event is logged and the result
so far is returned.

!!! tip
    Give every agent a short `description`. Agents see a roster of their peers' names and
    descriptions, which helps them transfer to the right one.

## Supervised mode

No start agent is needed. A **planner** (`planner_model`, `gpt-4o` by default) receives the
request and the agents' descriptions, then returns a JSON plan:

```json
{"plan": [
  {"agent_name": "Researcher", "task": "Collect facts about Apollo 11"},
  {"agent_name": "Copywriter", "task": "Write a 2-sentence tweet"},
  {"agent_name": "Editor", "task": "Add 3 hashtags"}
]}
```

The steps then run in order. Each agent may make up to `max_steps_per_task` LLM calls
(default `3`) to use tools before the next step starts. Agents cannot transfer in this mode.

```python
swarm = Swarm(agents=[researcher, copywriter, editor], planner_model="gpt-4o-mini")
result = swarm.execute_plan("Tweet about the Apollo 11 landing")
print(result.plan)          # the validated plan
print(result.final_output)  # the last agent's reply
```

Plan steps that name an unknown agent are skipped and logged. If the planner returns
something that can't be parsed as JSON, a `ValueError` is raised.

Use `planner_kwargs` to pass extra LiteLLM parameters to the planner, such as an `api_key`,
or `response_format=None` for models that don't support JSON mode.

## Conversation history

Each run needs a history. It comes from the first of these that applies:

1. the `history=` argument, which is copied before use;
2. the `load_handler`, when a `session_id` is given (see [Persistence](persistence.md));
3. otherwise `swarm.history`, an **in-memory** history that carries over between calls on the
   same `Swarm`. This is convenient for scripts and REPL chats. Call `swarm.reset()` to clear it.

!!! warning "Servers"
    In a web server, always pass a `session_id` with a `load_handler`, or pass `history=`
    yourself. Otherwise all users share `swarm.history`.
