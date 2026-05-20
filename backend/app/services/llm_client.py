from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_PROVIDER


def heuristic_brief(events: list[dict[str, Any]]) -> dict[str, Any]:
    high_count = sum(1 for event in events if event["severity"] == "high")
    medium_count = sum(1 for event in events if event["severity"] == "medium")
    event_types = sorted({event["type"] for event in events})

    if high_count:
        verdict = "Elevated risk"
        confidence = 0.78
        action = "Review the high-severity moments before sharing the clip or coaching the driver."
    elif medium_count:
        verdict = "Moderate risk"
        confidence = 0.68
        action = "Check the timeline for context and confirm whether traffic controls were obeyed."
    else:
        verdict = "Low observed risk"
        confidence = 0.58
        action = "No urgent action from automated signals; keep the report for audit history."

    evidence = [
        f"{high_count} high-severity and {medium_count} medium-severity event(s) found.",
        f"Detected event types: {', '.join(event_types) if event_types else 'none'}.",
    ]

    return {
        "verdict": verdict,
        "confidence": confidence,
        "evidence": evidence,
        "recommended_action": action,
        "key_questions": [
            "Was the vehicle slowing or braking during the flagged moment?",
            "Was there enough following distance for road and weather conditions?",
            "Should any event be dismissed because it came from a false positive detection?",
        ],
        "source": "local-heuristic",
    }


async def create_driving_risk_brief(events: list[dict[str, Any]]) -> dict[str, Any]:
    if LLM_PROVIDER != "openai_compatible" or not LLM_API_KEY:
        return heuristic_brief(events)

    prompt = {
        "role": "user",
        "content": (
            "You are a driving safety reviewer. Return only JSON with keys: "
            "verdict, confidence, evidence, recommended_action, key_questions. "
            "Use the provided event JSON as evidence.\n\n"
            f"Events:\n{json.dumps(events, indent=2)}"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{LLM_BASE_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}"},
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "Return concise, valid JSON only."},
                        prompt,
                    ],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        brief = json.loads(content)
        brief["source"] = "llm"
        return brief
    except Exception as exc:
        fallback = heuristic_brief(events)
        fallback["source"] = "local-heuristic-after-llm-error"
        fallback["llm_error"] = str(exc)
        return fallback
