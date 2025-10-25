"""Tool utilities for the Alto agent."""

from typing import Any, Dict

from google.adk.tools import FunctionTool

from .calendar import optimize_calendar, derive_month, pick_focus
from .explain import explain_plan


def _calendar_optimize_tool_fn(
    payload: Dict[str, Any],
    focus: str = "balanced",
) -> Dict[str, Any]:
    """Return the optimized calendar plan as a serializable dict."""
    plan = optimize_calendar(payload, focus=focus)
    return plan.as_dict()


def _explain_plan_tool_fn(
    payload: Dict[str, Any],
    plan: Dict[str, Any],
    focus: str = "balanced",
) -> Dict[str, Any]:
    """Generate narrative bullets for the provided plan."""
    bullets = explain_plan(payload, plan, focus=focus)
    return {"explain": bullets}


calendar_optimize_tool = FunctionTool.from_function(
    _calendar_optimize_tool_fn,
    name="calendar_optimize",
    description=(
        "Optimizes the user's cashflow calendar. Provide the normalized payload and an optional focus "
        "('overdraft', 'utilization', or 'balanced'). Returns changes, metrics, next_actions, and explain hints."
    ),
)

explain_plan_tool = FunctionTool.from_function(
    _explain_plan_tool_fn,
    name="explain_plan",
    description=(
        "Summarizes why the optimized calendar helps the user. Requires the original payload, the plan (as dict), and focus."
    ),
)


__all__ = [
    "optimize_calendar",
    "derive_month",
    "pick_focus",
    "explain_plan",
    "calendar_optimize_tool",
    "explain_plan_tool",
]
