"""
======================================================================
Customer Support Bot Quality Evaluation
======================================================================
"""

import asyncio
import json
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_ext.models.ollama import OllamaChatCompletionClient


def make_client():
    return OllamaChatCompletionClient(
        model="llama3.2",
        base_url="http://localhost:11434"
    )


# ── Evaluation rubric ─────────────────────────────────────────────────────────
RUBRIC = {
    "Acknowledges the complaint": lambda t: 1 if any(
        w in t.lower() for w in ["understand", "sorry", "apologi", "concern", "charged twice"]
    ) else 0,

    "Offers concrete resolution": lambda t: 1 if any(
        w in t.lower() for w in ["refund", "credit", "investigate", "billing team", "resolve", "fix"]
    ) else 0,

    "Asks for account details": lambda t: 1 if any(
        w in t.lower() for w in ["account", "email", "order", "invoice", "subscription id"]
    ) else 0,

    "Professional tone": lambda t: 0 if any(
        w in t.lower() for w in ["not my problem", "whatever", "deal with it", "can't help"]
    ) else 1,

    "Response length adequate": lambda t: 1 if len(t.split()) > 60 else 0,
}

def score_response(text: str) -> dict:
    return {name: fn(text) for name, fn in RUBRIC.items()}

def print_scores(label: str, scores: dict):
    total = sum(scores.values())
    max_s = len(scores)
    bar = "█" * total + "░" * (max_s - total)
    print(f"\n  [{label}]  {bar}  {total}/{max_s}")
    for k, v in scores.items():
        print(f"    {'' if v else ''}  {k}")


# ── Build and run a support team ──────────────────────────────────────────────
async def run_support_team(customer_message: str, agent_quality: str = "good") -> str:
    client = make_client()

    if agent_quality == "good":
        support_msg = (
            "You are a friendly, professional customer support agent. "
            "Always acknowledge the customer's frustration first, then "
            "offer a concrete next step (refund, investigation, escalation). "
            "Ask for account details if needed. End with RESOLVED."
        )
    else:
        support_msg = (
            "You are a bored support agent. Give very short dismissive replies. "
            "Do not offer solutions. End with RESOLVED."
        )

    triage = AssistantAgent(
        name="triage",
        model_client=client,
        system_message=(
            "You are a triage agent. Classify the customer issue as: "
            "BILLING, TECHNICAL, or ACCOUNT. State the category, then pass to support."
        )
    )

    support = AssistantAgent(
        name="support",
        model_client=client,
        system_message=support_msg
    )

    qa = AssistantAgent(
        name="qa_reviewer",
        model_client=client,
        system_message=(
            "You are a QA reviewer. After support responds, rate the reply "
            "1-5 for empathy and 1-5 for resolution quality. Be brief."
        )
    )

    termination = (
        MaxMessageTermination(max_messages=8) |
        TextMentionTermination("RESOLVED")
    )

    team = RoundRobinGroupChat(
        participants=[triage, support, qa],
        termination_condition=termination
    )

    result = await team.run(task=customer_message)

    print("\n" + "=" * 55)
    print(f"CONVERSATION [{agent_quality.upper()} AGENT]:")
    print("=" * 55)
    for msg in result.messages:
        print(f"\n  [{msg.source}]: {msg.content[:350]}")

    full_text = " ".join(
        msg.content for msg in result.messages
        if msg.source in ("triage", "support", "qa_reviewer")
    )
    return full_text


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    complaint = (
        "I was charged twice for my subscription this month. "
        "I need this fixed immediately or I'm cancelling."
    )

    print("\n>>> Running GOOD support agent...")
    good_text = await run_support_team(complaint, agent_quality="good")

    print("\n>>> Running BAD support agent...")
    bad_text = await run_support_team(complaint, agent_quality="bad")

    good_scores = score_response(good_text)
    bad_scores  = score_response(bad_text)

    print("\n\n" + "=" * 55)
    print("AGENTEVAL COMPARISON")
    print("=" * 55)
    print_scores("Good Agent", good_scores)
    print_scores("Bad Agent ", bad_scores)

    # Save for use by exp2_eval_llm.py if you want LLM-based scoring too
    with open("support_good.txt", "w") as f:
        f.write(good_text)
    with open("support_bad.txt", "w") as f:
        f.write(bad_text)

    print("\nSaved: support_good.txt  support_bad.txt")
    print("Tip: Run exp2_eval_llm.py to get LLM-as-judge scoring on top.\n")


if __name__ == "__main__":
    asyncio.run(main())
