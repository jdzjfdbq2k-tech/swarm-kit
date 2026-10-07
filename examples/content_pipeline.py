"""Supervised mode: a planner LLM sequences specialised workers.

Run with:  python examples/content_pipeline.py
"""

from swarm_kit import Agent, Swarm

researcher = Agent(
    name="Researcher",
    description="Finds facts about a topic.",
    instructions="Find factual information about the user's topic. Summarize it into bullet points.",
)

copywriter = Agent(
    name="Copywriter",
    description="Writes short marketing copy.",
    instructions="Read the research in the chat history. Write a punchy, 2-sentence marketing tweet based on it.",
)

editor = Agent(
    name="Editor",
    description="Polishes copy and adds hashtags.",
    instructions="Review the tweet. Add exactly 3 relevant hashtags to the end of it.",
)

swarm = Swarm(agents=[researcher, copywriter, editor])

if __name__ == "__main__":
    print("🚀 Running Supervised Swarm (Sequential Pipeline)\n")
    # No start agent: the supervisor decides the flow.
    result = swarm.execute_plan(user_input="I want to post a tweet about the history of the Apollo 11 moon landing.")
    print("\nFinal tweet:\n", result.final_output)
