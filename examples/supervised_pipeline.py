"""Async supervised data pipeline that writes extracted entities to shared state.

Run with:  python examples/supervised_pipeline.py
"""

import asyncio

from swarm_kit import Agent, Swarm

# ==========================================
# 1. MOCK DATABASE
# ==========================================
pipeline_db = {}


def save_pipeline(session_id, history, state):
    pipeline_db[session_id] = {"state": state}


def load_pipeline(session_id):
    return [], pipeline_db.get(session_id, {}).get("state", {})


# ==========================================
# 2. AGENTS & SWARM
# ==========================================
extractor = Agent(
    name="Extractor",
    description="Extracts entities into the global state.",
    instructions="Extract the core entities from the user's prompt and save each one with the update_state tool.",
)

writer = Agent(
    name="Writer",
    description="Summarises the global state.",
    instructions="Read the global state and write a 1-sentence summary of the entities.",
)

swarm = Swarm(agents=[extractor, writer], save_handler=save_pipeline, load_handler=load_pipeline)


async def main():
    print("--- Running Supervised Data Pipeline ---")
    result = await swarm.execute_plan_async(
        user_input="Apple just released the M4 MacBook Pro in Space Black for $1999.",
        session_id="job_404",
    )

    print("\n--- Final State ---")
    print(result.state)
    print("\n--- Database Record ---")
    print(pipeline_db)


if __name__ == "__main__":
    asyncio.run(main())
