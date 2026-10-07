"""Unsupervised mode: a triage agent routes the user to specialists.

Run with:  python examples/customer_support.py
"""

from swarm_kit import Agent, Swarm


def process_refund(order_number: str) -> str:
    """Process a refund for a customer. Call this ONLY after you have their order number."""
    # In a real app you would call your payment provider (e.g. Stripe) here.
    return f"Success! A refund has been issued to the original payment method for order {order_number}."


triage_agent = Agent(
    name="Triage",
    description="Front desk. Routes users to the right specialist.",
    instructions=(
        "You are the front desk. Ask the user what they need. "
        "If it is a refund, transfer to 'Billing'. If it is a bug, transfer to 'Tech'."
    ),
)

billing_agent = Agent(
    name="Billing",
    description="Handles refunds and payments.",
    instructions=(
        "You handle refunds. Ask for their order number if they didn't provide it. "
        "Once you have it, use the `process_refund` tool and tell the user the result. Do not transfer."
    ),
    tools=[process_refund],  # schema is generated from the type hints + docstring
)

tech_agent = Agent(
    name="Tech",
    description="Fixes bugs and technical problems.",
    instructions="You fix bugs. Ask them to describe the error code, then offer a solution. Do not transfer.",
)

swarm = Swarm(agents=[triage_agent, billing_agent, tech_agent])

if __name__ == "__main__":
    print("🚀 Running Unsupervised Swarm (Dynamic Chat)\n")
    result = swarm.execute(
        start_agent_name="Triage",
        user_input="I am very angry. I want a refund for my subscription. My order number is INV-992.",
    )
    print(f"\nFinished with {result.last_agent} after {result.turns} turns.")
