# Tools

Tools let agents call your code: databases, HTTP APIs, payment providers and so on.

## Plain functions (recommended)

Pass a function with type hints and a docstring. Swarm Kit generates the JSON schema for you.

```python
from typing import Literal, Optional

def search_products(query: str, category: Optional[str] = None,
                    sort: Literal["price", "rating"] = "rating", limit: int = 5) -> list:
    """Search the product catalogue and return matching items."""
    ...

agent = Agent(name="Shop", instructions="...", tools=[search_products])
```

How the schema is generated:

- **Name**: the function name.
- **Description**: the docstring. The model reads it to decide when to call the tool, so be specific.
- **Parameters**: `str`, `int`, `float`, `bool`, `list[...]`, `dict`, `Optional[...]` and
  `Literal[...]` map to their JSON schema types. Unannotated parameters are treated as strings.
- **Required**: every parameter without a default value.

To inspect the result, call `function_to_schema` yourself:

```python
from swarm_kit import function_to_schema
print(function_to_schema(search_products))
```

## Explicit schemas

To control the schema fully, for example to add per-parameter descriptions, pass a
`(schema, function)` tuple:

```python
refund_schema = {
    "type": "function",
    "function": {
        "name": "process_refund",
        "description": "Process a refund. Call ONLY after you have the order number.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_number": {"type": "string", "description": "e.g. ORD-123"}
            },
            "required": ["order_number"],
        },
    },
}

billing = Agent(name="Billing", instructions="...", tools=[(refund_schema, process_refund)])
```

You can mix both styles in one `tools` list.

## Async tools

`async def` tools are awaited:

```python
async def fetch_weather(city: str) -> dict:
    """Get the current weather for a city."""
    async with httpx.AsyncClient() as client:
        return (await client.get(f"https://api.example.com/weather/{city}")).json()
```

With `execute_async()` they run on the current event loop. With the synchronous `execute()`
they run through `asyncio.run()`, which fails when an event loop is already running. In that
case, use `execute_async()`.

!!! note
    In `execute_async()`, **synchronous** tools run directly on the event loop. Avoid long
    blocking calls in them, or make them `async`.

## Return values and errors

- A `str` return value is passed to the model unchanged. Any other value is serialized as JSON.
- If a tool **raises**, the swarm catches the exception and sends `Error: <Type>: <message>`
  back to the model so it can recover or explain. The run continues.
- If the model calls a tool that doesn't exist, or sends invalid JSON arguments, it gets an
  error message back.

!!! warning "Treat arguments as untrusted input"
    The LLM chooses the arguments. Validate them inside every tool, and add a confirmation
    step before destructive actions.

## Parallel tool calls

When a model requests several tools in one response, all of them run in order. Each result
is recorded as a `tool` message linked by `tool_call_id`, which is the format OpenAI,
Anthropic and other providers expect.
