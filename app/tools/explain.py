"""Explanation helpers for calendar plans."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

try:
    from vertexai.preview.generative_models import GenerationConfig, GenerativeModel
    _GEMINI_READY = True
except Exception:  # pragma: no cover - graceful fallback in local/dev without Vertex
    GenerationConfig = None  # type: ignore
    GenerativeModel = None  # type: ignore
    _GEMINI_READY = False


def _format_prompt(payload: Dict[str, Any], plan: Dict[str, Any], focus: str) -> str:
    cash_in = payload.get("cashIn", [])[:5]
    cash_out = payload.get("cashOut", [])[:8]
    changes = plan.get("changes", [])
    metrics = plan.get("metrics", {})
    summary = {
        "focus": focus,
        "income": cash_in,
        "cash_out": cash_out,
        "changes": changes,
        "metrics": metrics,
    }
    return (
        "You are Alto, a money coach who explains scheduling decisions clearly.\n"
        "Summarize why the proposed calendar keeps the client safe and improves their credit.\n"
        "Output 3 short bullet points (max 18 words each).\n"
        "Stay concrete: mention paychecks, buffer protection, credit utilization, or subscription timing as relevant.\n"
        f"Context JSON: {json.dumps(summary, default=str)}"
    )


def explain_with_gemini(
    payload: Dict[str, Any],
    plan: Dict[str, Any],
    *,
    focus: str = "balanced",
    model: Optional[str] = None,
    temperature: float = 0.2,
) -> List[str]:
    """Generate explanation bullets using Gemini if available."""
    if not _GEMINI_READY:
        raise RuntimeError("Gemini generative SDK not available in this environment.")

    target_model = model or os.getenv("EXPLAIN_MODEL", "gemini-2.5-flash")
    gen_model = GenerativeModel(target_model)
    config = GenerationConfig(temperature=temperature, candidate_count=1)
    prompt = _format_prompt(payload, plan, focus)
    response = gen_model.generate_content(prompt, generation_config=config)

    text = ""
    if getattr(response, "text", None):
        text = response.text
    else:
        candidates = getattr(response, "candidates", []) or []
        if candidates:
            parts = getattr(candidates[0], "content", {}).parts  # type: ignore[attr-defined]
            text = "\n".join(getattr(part, "text", "") for part in parts if getattr(part, "text", ""))

    bullets = [line.strip("•- ").strip() for line in text.splitlines() if line.strip()]
    return bullets[:3]


def fallback_explain(plan: Dict[str, Any], *, focus: str = "balanced") -> List[str]:
    explain = plan.get("explain") or []
    if explain:
        return explain[:3]
    return [
        "Smoothed big bills against expected deposits.",
        "Kept buffer above policy minimum while honoring locked payments.",
        "Targeted card utilization improvements with staged paydowns.",
    ]


def explain_plan(
    payload: Dict[str, Any],
    plan: Dict[str, Any],
    *,
    focus: str = "balanced",
    prefer_gemini: bool = True,
) -> List[str]:
    """Primary interface used by the agent to narrate the calendar plan."""
    if prefer_gemini and _GEMINI_READY:
        try:
            bullets = explain_with_gemini(payload, plan, focus=focus)
            if bullets:
                return bullets
        except Exception:
            pass
    return fallback_explain(plan, focus=focus)
