"""
======================================================================
 Multi-Turn Context Retention Evaluation

======================================================================
"""

import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_ext.models.ollama import OllamaChatCompletionClient


def make_client():
    return OllamaChatCompletionClient(
        model="llama3.2",
        base_url="http://localhost:11434"
    )


# ── Phase 1: Run the research conversation ────────────────────────────────────
async def run_research_conversation() -> list[dict]:
    """
    Manually drives a 4-turn Q&A so we can inject each question
    and capture the growing history — exactly how context retention works.
    """
    client = make_client()

    researcher = AssistantAgent(
        name="researcher",
        model_client=client,
        system_message=(
            "You are an AI history expert. "
            "Always reference what was discussed earlier in the conversation "
            "when answering follow-up questions. Build on prior answers."
        )
    )

    questions = [
        "When was the transformer architecture first introduced?",
        "Who were the main authors of that paper?",
        "How did it improve on earlier NLP approaches like LSTMs?",
        "Given everything we just discussed, summarise the key innovation in one sentence.",
    ]

    history = []
    print("\n" + "=" * 55)
    print("RESEARCH CONVERSATION")
    print("=" * 55)

    for q in questions:
        history.append({"role": "user", "content": q})
        response = await researcher.run(task=q)
        answer = response.messages[-1].content
        history.append({"role": "assistant", "content": answer})
        print(f"\nQ: {q}")
        print(f"A: {answer[:300]}...")

    return history


# ── Phase 2: Evaluate with a judge agent ──────────────────────────────────────
async def evaluate_with_agent(history: list[dict]) -> None:
    client = make_client()

    # Format conversation for the evaluator
    conv_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in history
    )

    evaluator = AssistantAgent(
        name="evaluator",
        model_client=client,
        system_message=(
            "You are an expert conversation evaluator. "
            "Score the ASSISTANT's responses on these criteria (0-5 each):\n"
            "  1. Context Retention — does each answer reference earlier turns?\n"
            "  2. Factual Accuracy — are the historical facts correct?\n"
            "  3. Answer Completeness — does each answer fully address the question?\n"
            "  4. Coherent Progression — do answers build on each other logically?\n\n"
            "Format your output as:\n"
            "  Context Retention: X/5 — reason\n"
            "  Factual Accuracy: X/5 — reason\n"
            "  Answer Completeness: X/5 — reason\n"
            "  Coherent Progression: X/5 — reason\n"
            "  OVERALL: X/20\n"
            "Then say EVALUATION_COMPLETE."
        )
    )

    prompt = (
        "Please evaluate the following multi-turn conversation:\n\n"
        f"{conv_text}\n\n"
        "Apply the rubric from your instructions."
    )

    termination = (
        MaxMessageTermination(max_messages=4) |
        TextMentionTermination("EVALUATION_COMPLETE")
    )

    # Single-agent team for the evaluator
    team = RoundRobinGroupChat(
        participants=[evaluator],
        termination_condition=termination
    )

    result = await team.run(task=prompt)

    print("\n\n" + "=" * 55)
    print("AGENTEVAL — EVALUATOR AGENT SCORES")
    print("=" * 55)
    for msg in result.messages:
        if msg.source == "evaluator":
            print(f"\n{msg.content}")


# ── Phase 3: Rubric-based keyword scoring ─────────────────────────────────────
def rubric_score(history: list[dict]) -> None:
    answers = [m["content"] for m in history if m["role"] == "assistant"]
    full = " ".join(answers).lower()

    rubric = {
        "Mentions 2017 (transformer year)":   "2017" in full,
        "Names Vaswani or Attention is All":   any(w in full for w in ["vaswani", "attention is all"]),
        "Contrasts with LSTM/RNN":             any(w in full for w in ["lstm", "rnn", "recurrent"]),
        "Final answer references prior turns": any(
            w in answers[-1].lower() for w in
            ["as discussed", "as mentioned", "we covered", "earlier", "above", "transformer"]
        ),
    }

    print("\n" + "=" * 55)
    print("RUBRIC KEYWORD SCORES")
    print("=" * 55)
    total = 0
    for criterion, passed in rubric.items():
        mark = "" if passed else ""
        print(f"  {mark}  {criterion}")
        total += int(passed)
    print(f"\n  Total: {total}/{len(rubric)}")


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    history = await run_research_conversation()
    rubric_score(history)
    await evaluate_with_agent(history)
    print("\nDone.\n")


if __name__ == "__main__":
    asyncio.run(main())
