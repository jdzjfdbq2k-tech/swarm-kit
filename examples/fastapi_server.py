"""Serve a swarm behind a FastAPI endpoint, one session per user.

Run with:  uvicorn examples.fastapi_server:app --reload
Then:      curl -X POST localhost:8000/chat -H 'content-type: application/json' \
               -d '{"session_id": "u1", "message": "Hi!"}'
"""

from fastapi import FastAPI
from pydantic import BaseModel

from swarm_kit import Agent, Swarm

# Replace with Redis/Postgres in production. Each session's history is isolated.
SESSIONS = {}

swarm = Swarm(
    agents=[Agent(name="Assistant", instructions="You are a concise, friendly assistant.")],
    save_handler=lambda sid, history, state: SESSIONS.__setitem__(sid, (history, state)),
    load_handler=lambda sid: SESSIONS.get(sid, ([], {})),
    log_file=None,  # don't write the Studio log file from a server
    verbose=False,
)

app = FastAPI()


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.post("/chat")
async def chat(req: ChatRequest):
    result = await swarm.execute_async("Assistant", req.message, session_id=req.session_id)
    return {"reply": result.final_output, "agent": result.last_agent, "state": result.state}
