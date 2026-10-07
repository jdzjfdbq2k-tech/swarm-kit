# Getting Started

## 1. Install

```bash
pip install swarm-agent-kit
```

Swarm Kit requires Python 3.10+.

## 2. Add an API key

Swarm Kit uses [LiteLLM](https://docs.litellm.ai/docs/providers), so any supported provider
works. Put your key in a `.env` file in your project directory. It is loaded automatically
when you `import swarm_kit`.

```env
OPENAI_API_KEY="sk-..."
# ANTHROPIC_API_KEY="..."
# GEMINI_API_KEY="..."
```

!!! tip "Scaffold a project"
    `swarm-kit init my-project` creates `my-project/agents/main.py` and a `.env.example`.

## 3. Your first swarm

```python title="main.py"
from swarm_kit import Agent, Swarm


def process_refund(order_number: str) -> str:
    """Process a refund. Call this only once you have the order number."""
    return f"Refund issued for {order_number}."


triage = Agent(
    name="Triage",
    description="Front desk that routes customers.",
    instructions="Find out what the user needs. Refunds go to 'Billing'.",
)

billing = Agent(
    name="Billing",
    description="Handles refunds.",
    instructions="Issue refunds with the process_refund tool, then confirm to the user.",
    tools=[process_refund],
)

swarm = Swarm(agents=[triage, billing])

result = swarm.execute(
    start_agent_name="Triage",
    user_input="I want a refund for order INV-992.",
)

print(result.final_output)  # the last thing an agent said
print(result.last_agent)    # "Billing"
print(result.state)         # the shared state dictionary
```

Run it with `python main.py`. The terminal shows each step as it happens: the transfer from
Triage to Billing, the tool call and its result, and the final reply.

## 4. Watch it in the Studio

In a second terminal, from the same directory:

```bash
swarm-kit studio
```

Open <http://localhost:8000> and run your script again to see the run update live.

## 5. Go async

Inside FastAPI or any other `asyncio` app, use the async variants:

```python
result = await swarm.execute_async("Triage", user_input, session_id=user_id)
```

With a `session_id` and [persistence hooks](guide/persistence.md), each user keeps their own
conversation across requests.

## Where next?

- [Agents](guide/agents.md) covers models, descriptions and per-agent settings.
- [Tools](guide/tools.md) shows how to connect agents to your own code and APIs.
- [Execution Modes](guide/modes.md) explains when to use supervised and unsupervised mode.
