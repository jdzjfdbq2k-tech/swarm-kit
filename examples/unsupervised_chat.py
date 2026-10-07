"""Async unsupervised chat with Bring-Your-Own-Database session persistence.

Run with:  python examples/unsupervised_chat.py
"""

import asyncio

from swarm_kit import Agent, Swarm

# ==========================================
# 1. MOCK DATABASE (swap for Redis/Postgres/...)
# ==========================================
db = {}


async def save_session(session_id, history, state):
    print(f"[DB] Saving session {session_id}...")
    db[session_id] = {"history": history, "state": state}


async def load_session(session_id):
    data = db.get(session_id)
    if data:
        print(f"[DB] Resuming session {session_id}...")
        return data["history"], data["state"]
    return [], {}


# ==========================================
# 2. CUSTOM TOOLS (sync or async)
# ==========================================
async def lookup_order(order_id: str) -> str:
    """Look up the status of a customer's order."""
    orders = {"ORD-123": "Shipped", "ORD-456": "Processing"}
    return orders.get(order_id, "Order not found.")


# ==========================================
# 3. AGENTS & SWARM
# ==========================================
support = Agent(
    name="Support",
    instructions="You are a support agent. If a user asks about an order, use the lookup tool. Keep responses short.",
    tools=[lookup_order],
)

swarm = Swarm(agents=[support], save_handler=save_session, load_handler=load_session)


async def main():
    print("--- User opens chat ---")
    await swarm.execute_async(start_agent_name="Support", user_input="Can you check on ORD-123?", session_id="user_session_99")

    print("\n--- User replies 10 minutes later ---")
    # The history is loaded automatically through the load handler.
    await swarm.execute_async(
        start_agent_name="Support", user_input="Great, thanks! What about ORD-456?", session_id="user_session_99"
    )


if __name__ == "__main__":
    asyncio.run(main())
