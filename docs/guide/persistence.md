# Persistence & Sessions

Swarm Kit doesn't include a database. You provide two functions and it calls them at the
right moments. This is the *bring-your-own-database* approach.

```python
def load_handler(session_id: str) -> tuple[list, dict]:
    """Return (history, state) for a session, or ([], {}) if it's new."""

def save_handler(session_id: str, history: list, state: dict) -> None:
    """Persist the session after a run."""

swarm = Swarm(agents=[...], load_handler=load_handler, save_handler=save_handler)
await swarm.execute_async("Support", "Hi", session_id="user_42")
```

When a run is given a `session_id`:

1. `load_handler(session_id)` is called **before** the run. The returned history is used for
   this run only, and the returned state is merged into the `state` argument.
2. `save_handler(session_id, history, state)` is called **after** the run.

Both handlers can be regular functions or `async def`. Concurrent sessions on the same
`Swarm` instance don't share history.

The history is a list of OpenAI-style message dicts (`user`, `assistant` with `tool_calls`,
and `tool`), so it serializes directly to JSON.

## Redis

```python
import json
import redis.asyncio as redis

r = redis.from_url("redis://localhost:6379")

async def load(session_id):
    raw = await r.get(f"swarm:{session_id}")
    if not raw:
        return [], {}
    data = json.loads(raw)
    return data["history"], data["state"]

async def save(session_id, history, state):
    await r.set(f"swarm:{session_id}", json.dumps({"history": history, "state": state}), ex=86400)

swarm = Swarm(agents=[...], load_handler=load, save_handler=save)
```

## SQLite

```python
import json, sqlite3

db = sqlite3.connect("sessions.db")
db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, data TEXT)")

def load(session_id):
    row = db.execute("SELECT data FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        return [], {}
    data = json.loads(row[0])
    return data["history"], data["state"]

def save(session_id, history, state):
    db.execute("INSERT OR REPLACE INTO sessions VALUES (?, ?)",
               (session_id, json.dumps({"history": history, "state": state})))
    db.commit()
```

## PostgreSQL

Store the same JSON in a `jsonb` column, using `asyncpg` or SQLAlchemy in `async` handlers.

## Managing history yourself

To skip the hooks, pass and receive history directly:

```python
result = await swarm.execute_async("Support", "Hi", history=previous_history)
store(result.history, result.state)
```

!!! tip "Long conversations"
    Histories grow with every turn. Trim or summarize old messages in your `load_handler`
    before returning them to keep token costs down.
