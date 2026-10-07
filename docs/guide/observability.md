# Observability & Agent Studio

Swarm Kit reports what happens during a run in three ways.

## 1. Terminal transcript

With `verbose=True` (the default), each response, transfer, tool call and state update is
printed to the terminal with [Rich](https://github.com/Textualize/rich). Use `verbose=False`
in servers.

## 2. Events

Every step produces an **event** dict:

```python
{"agent": "Billing", "action": "Tool", "content": "process_refund({'order_number': 'INV-9'})",
 "timestamp": 1760000000.0, "tool": "process_refund"}
```

| `action` | Emitted when | Extra keys |
| --- | --- | --- |
| `Start` | A run begins | |
| `Plan` | The planner returned a plan (supervised mode) | `plan` |
| `Response` | An agent replied with text | |
| `Tool` | A user tool is about to run | `tool` |
| `ToolResult` | A user tool returned | `tool` |
| `StateUpdate` | `update_state` was called | `key`, `value` |
| `Transfer` | Control moved to another agent | `to` |
| `Error` | A tool failed, a bad transfer, an invalid plan step, or `max_turns` was reached | sometimes `tool` |
| `Complete` | The run finished | |

Pass `event_handler` to send events to your own logging, metrics or tracing:

```python
import logging
log = logging.getLogger("swarm")

swarm = Swarm(agents=[...], event_handler=lambda e: log.info("%s %s", e["agent"], e["action"], extra=e))
```

## 3. JSONL log and Agent Studio

Events are also appended to `log_file` (default `.swarm_runs.jsonl` in the working directory).
The file is cleared when each run starts. Use `log_file=None` to turn it off, which you
should do in production.

The **Agent Studio** is a local dashboard that shows this file live:

```bash
swarm-kit studio                       # http://127.0.0.1:8000
swarm-kit studio --port 9000 --log-file path/to/run.jsonl
```

Run your swarm in another terminal and the dashboard updates every second, with badges for
each action type.

!!! warning
    The Studio has no authentication and shows full prompts and tool output. Keep it bound
    to `127.0.0.1`.
