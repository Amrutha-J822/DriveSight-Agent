"""Rule-based coaching brief generator.

When a reviewer finalizes a case, we look at which events were approved or
escalated and emit a single coaching recommendation per case. The rules are
deliberately simple — a Phase 3 follow-up can pass these inputs to an LLM for
a more polished narrative.
"""

from __future__ import annotations

from typing import Any

EVENT_COACHING: dict[str, str] = {
    "close_following": "Maintain a 3-second following distance and scan further ahead in moderate traffic.",
    "close_following_approximation": "Maintain a 3-second following distance and scan further ahead in moderate traffic.",
    "lane_drift": "Review lane discipline; check for fatigue and reduce in-cab distractions.",
    "lane_drift_placeholder": "Review lane discipline; check for fatigue and reduce in-cab distractions.",
    "pedestrian_near_road": "Slow down near pedestrian-heavy areas and double-check crosswalks.",
    "pedestrian_detected": "Slow down near pedestrian-heavy areas and double-check crosswalks.",
    "stop_sign_detected": "Come to a complete stop at every stop sign and pause for 2 seconds before proceeding.",
    "harsh_braking": "Anticipate slowdowns earlier and apply brakes progressively.",
    "vehicle_detected": "Stay aware of surrounding traffic density and adjust speed accordingly.",
}

DEFAULT_RECOMMENDATION = "Schedule a general defensive driving refresher review."


def build_coaching(case: dict[str, Any]) -> dict[str, str] | None:
    """Return ``{recommendation_text, reason}`` or ``None`` if no coaching needed."""
    events = case.get("events") or []
    serious = [e for e in events if e.get("status") in {"approved", "escalated"}]
    if not serious:
        return None

    # Pick the most common serious event type to anchor the recommendation.
    counts: dict[str, int] = {}
    severities: dict[str, list[str]] = {}
    for event in serious:
        event_type = event.get("event_type") or "general"
        counts[event_type] = counts.get(event_type, 0) + 1
        severities.setdefault(event_type, []).append(event.get("severity", "medium"))

    primary_type = max(counts, key=counts.get)
    occurrences = counts[primary_type]

    recommendation = EVENT_COACHING.get(primary_type, DEFAULT_RECOMMENDATION)

    escalated_total = sum(1 for e in serious if e.get("status") == "escalated")
    intensifier = ""
    if escalated_total:
        intensifier = (
            f" {escalated_total} event(s) on this clip were escalated — recommend a 1:1 coaching session "
            "this week and re-review after the next 5 trips."
        )

    driver_name = (case.get("driver") or {}).get("name") or "the driver"
    text = (
        f"Recommendation for {driver_name}: {recommendation}"
        f" This clip contained {occurrences} confirmed {primary_type.replace('_', ' ')} event(s)."
        f"{intensifier}"
    )

    reason = (
        f"primary_event={primary_type}; occurrences={occurrences}; "
        f"escalated={escalated_total}; severities={','.join(sorted(set(sum(severities.values(), []))))}"
    )

    return {"recommendation_text": text, "reason": reason}
