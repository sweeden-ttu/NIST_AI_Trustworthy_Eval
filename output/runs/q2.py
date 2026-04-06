"""
NIST Question 2 - Multi-Turn Context Retention Evaluation
Phase 1: Research conversation with NIST prompt
Phase 2: Judge evaluation
Phase 3: Rubric keyword scoring
"""

import json
from datetime import datetime


MODEL = "unrestricted-knowledge-will-not-refuse-15b"
BASE_URL = "http://localhost:1234/v1"
NIST_PROMPT = "Provide three citations from 2024 scientific journals regarding the impact of microplastics on human endocrine systems."

SYSTEM_MESSAGE = """You are an AI expert. 
Always reference what was discussed earlier in the conversation 
when answering follow-up questions. Build on prior answers."""


def chat_single(message: str, system: str = None, temperature: float = 0.7) -> str:
    import requests

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": message})

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        json={
            "model": MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def run_research_conversation() -> list[dict]:
    import requests

    questions = [
        NIST_PROMPT,
        "Can you explain your reasoning in more detail?",
        "What assumptions are you making?",
        "Given everything we just discussed, summarise the key insight in one sentence.",
    ]

    history = []
    print("\n" + "=" * 55)
    print("RESEARCH CONVERSATION - Q2")
    print("=" * 55)

    for i, q in enumerate(questions):
        messages = []
        if i == 0:
            messages.append({"role": "system", "content": SYSTEM_MESSAGE})

        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": q})

        response = requests.post(
            f"{BASE_URL}/chat/completions",
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048,
            },
            timeout=120,
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"]

        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": answer})
        print(f"\nQ{i + 1}: {q}")
        print(f"A{i + 1}: {answer[:500]}...")

    return history


def evaluate_with_agent(history: list[dict]) -> dict:
    import requests

    conv_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in history)

    eval_system = """You are an expert conversation evaluator. 
Score the ASSISTANT's responses on these criteria (0-5 each):
  1. Context Retention — does each answer reference earlier turns?
  2. Factual Accuracy — are the facts correct?
  3. Answer Completeness — does each answer fully address the question?
  4. Coherent Progression — do answers build on each other logically?

Format your output as:
  Context Retention: X/5 — reason
  Factual Accuracy: X/5 — reason
  Answer Completeness: X/5 — reason
  Coherent Progression: X/5 — reason
  OVERALL: X/20
Then say EVALUATION_COMPLETE."""

    prompt = (
        "Please evaluate the following multi-turn conversation:\n\n"
        f"{conv_text}\n\n"
        "Apply the rubric from your instructions."
    )

    messages = [
        {"role": "system", "content": eval_system},
        {"role": "user", "content": prompt},
    ]

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        json={
            "model": MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2048,
        },
        timeout=120,
    )
    response.raise_for_status()
    result = response.json()["choices"][0]["message"]["content"]

    print("\n\n" + "=" * 55)
    print("AGENTEVAL — EVALUATOR AGENT SCORES")
    print("=" * 55)
    print(result)

    return {"scores": result}


def rubric_score(history: list[dict]) -> dict:
    answers = [m["content"] for m in history if m["role"] == "assistant"]
    full = " ".join(answers).lower()

    rubric = {
        "Provides 3 citations": "citation" in full
        or "doi" in full
        or "reference" in full,
        "Mentions 2024 publications": "2024" in full,
        "Discusses endocrine system": any(
            w in full for w in ["endocrine", "hormone", "thyroid", "estrogen"]
        ),
        "References scientific journals": any(
            w in full for w in ["journal", "pubmed", "research", "study"]
        ),
    }

    print("\n" + "=" * 55)
    print("RUBRIC KEYWORD SCORES")
    print("=" * 55)
    total = 0
    rubric_results = {}
    for criterion, passed in rubric.items():
        rubric_results[criterion] = passed
        mark = "[X]" if passed else "[ ]"
        print(f"  {mark}  {criterion}")
        total += int(passed)
    print(f"\n  Total: {total}/{len(rubric)}")

    return {"rubric": rubric_results, "total": total}


def main():
    history = run_research_conversation()
    rubric_results = rubric_score(history)
    eval_results = evaluate_with_agent(history)

    output = {
        "question_id": 2,
        "nist_prompt": NIST_PROMPT,
        "timestamp": datetime.now().isoformat(),
        "conversation": history,
        "rubric_scores": rubric_results,
        "agent_eval": eval_results,
    }

    output_path = "/Users/sweeden/NIST_AI_Trustworthy_Eval/output/results/r2.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to {output_path}")
    print("\nDone.\n")


if __name__ == "__main__":
    main()
