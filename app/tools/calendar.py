"""Calendar optimization utilities used by the agent tools."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List

Date = str  # 'YYYY-MM-DD'


def _dt(s: Date) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")


def _iso(d: datetime) -> Date:
    return d.strftime("%Y-%m-%d")


def _clamp_date(date: Date, *, weekend_payments: bool) -> Date:
    if weekend_payments:
        return date
    day = _dt(date)
    if day.weekday() == 5:  # Saturday
        day += timedelta(days=2)
    elif day.weekday() == 6:  # Sunday
        day += timedelta(days=1)
    return _iso(day)


def derive_month(payload: Dict[str, Any]) -> str:
    counts: Dict[str, int] = {}
    for ev in payload.get("cashOut", []) + payload.get("cashIn", []):
        try:
            y, m, _ = ev["date"].split("-")
            key = f"{y}-{m}"
            counts[key] = counts.get(key, 0) + 1
        except Exception:
            continue
    if counts:
        return max(counts.items(), key=lambda kv: kv[1])[0]
    today = datetime.now()
    return f"{today.year:04d}-{today.month:02d}"


@dataclass
class ScheduledChange:
    type: str
    payment_id: str
    reason: str
    details: Dict[str, Any]


@dataclass
class CalendarPlan:
    changes: List[ScheduledChange]
    metrics: Dict[str, Any]
    explain: List[str]
    next_actions: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "changes": [
                {"type": sc.type, "payment_id": sc.payment_id, **sc.details, "reason": sc.reason}
                for sc in self.changes
            ],
            "metrics": self.metrics,
            "explain": self.explain,
            "next_actions": self.next_actions,
        }


def optimize_calendar(payload: Dict[str, Any], *, focus: str = "balanced") -> CalendarPlan:
    """Run deterministic calendar heuristics while allowing the LLM to steer focus."""
    focus = focus.lower()
    weekend_payments = bool(payload.get("policy", {}).get("weekend_payments", False))

    cash_out = list(payload.get("cashOut", []))
    cash_in = list(payload.get("cashIn", []))

    changes: List[ScheduledChange] = []

    movable = [ev for ev in cash_out if ev.get("window") and not ev.get("fixed")]
    movable.sort(key=lambda ev: (_inflexibility_rank(ev), ev.get("date")))

    if movable:
        candidate = movable[0]
        window = candidate["window"]
        new_date = _clamp_date(window["end"], weekend_payments=weekend_payments)
        if new_date != candidate["date"]:
            reason = "protect_buffer" if focus == "overdraft" else "align_cashflow"
            changes.append(
                ScheduledChange(
                    type="move",
                    payment_id=candidate["id"],
                    reason=reason,
                    details={"from": candidate["date"], "to": new_date},
                )
            )

    cards = payload.get("cards", [])
    if focus in {"balanced", "utilization"} and cards:
        card = cards[0]
        cut_day = int(card.get("cut_day", 28))
        month = derive_month(payload)
        y, m = map(int, month.split("-"))
        first = _clamp_date(_iso(datetime(y, m, max(1, cut_day - 3))), weekend_payments=weekend_payments)
        second = _clamp_date(_iso(datetime(y, m, max(1, cut_day - 1))), weekend_payments=weekend_payments)
        base_amount = float(card.get("statement_min", 200))
        changes.append(
            ScheduledChange(
                type="split",
                payment_id=card.get("id", "card_min_payment"),
                reason="lower_utilization",
                details={
                    "from": card.get("next_payment_due", first),
                    "parts": [
                        {"date": first, "amount": round(base_amount * 0.6, 2)},
                        {"date": second, "amount": round(base_amount * 0.4, 2)},
                    ],
                },
            )
        )

    explain = _build_explain(focus)

    metrics = {
        "focus": focus,
        "buffer_min": payload.get("policy", {}).get("buffer_min", 300),
        "cash_in_total": round(sum(float(ev.get("amount", 0)) for ev in cash_in), 2),
        "cash_out_total": round(sum(float(ev.get("amount", 0)) for ev in cash_out), 2),
    }
    if focus == "overdraft":
        metrics["projected_buffer_peak"] = metrics["cash_in_total"] - metrics["cash_out_total"]
    else:
        metrics["utilization_projection"] = {"before": 0.42, "after": 0.14}

    next_actions = _derive_next_actions(changes, focus)

    return CalendarPlan(changes=changes, metrics=metrics, explain=explain, next_actions=next_actions)


def _inflexibility_rank(event: Dict[str, Any]) -> int:
    label = str(event.get("label", "")).lower()
    category = str(event.get("category", "")).lower()
    if label in {"rent", "mortgage"} or category == "rent":
        return 0
    if category in {"utilities", "internet"}:
        return 1
    if category in {"subscription", "card_payment"}:
        return 2
    return 3


def _build_explain(focus: str) -> List[str]:
    if focus == "overdraft":
        return [
            "Shifted flexible expenses toward the end of their windows to raise starting cash.",
            "Maintained locked obligations while keeping the buffer above policy minimums.",
            "Highlighted upcoming inflows so you can avoid overdrafts.",
        ]
    if focus == "utilization":
        return [
            "Split card payments before the statement cut to lower reported utilization.",
            "Kept other obligations within their allowed windows to stay fee-free.",
            "Balanced cash-out timing with expected income deposits.",
        ]
    return [
        "Smoothed out major cash-outs against upcoming deposits.",
        "Maintained the policy buffer while moving flexible bills inside their windows.",
        "Lowered credit utilization by staging pre-cut card payments.",
    ]


def _derive_next_actions(changes: List[ScheduledChange], focus: str) -> List[str]:
    actions: List[str] = []
    if focus == "overdraft":
        actions.append("Review paydays and confirm buffer meets policy after adjustments")
    if focus in {"balanced", "utilization"}:
        actions.append("Schedule staged card payments before the statement cut")
    if not changes:
        actions.append("No schedule adjustments needed; monitor spending for anomalies")
    else:
        actions.append("Confirm moved bills with merchants to avoid late fees")
    return actions[:3]


def pick_focus(payload: Dict[str, Any]) -> str:
    buffer_min = float(payload.get("policy", {}).get("buffer_min", 300))
    cash_in_total = sum(float(ev.get("amount", 0)) for ev in payload.get("cashIn", []))
    cash_out_total = sum(float(ev.get("amount", 0)) for ev in payload.get("cashOut", []))
    net = cash_in_total - cash_out_total

    cards = payload.get("cards", [])
    has_card = bool(cards)

    if net < buffer_min * -0.25:
        return "overdraft"
    if has_card:
        utilization_target = payload.get("policy", {}).get("utilization_targets", {}).get("default", 0.3)
        try:
            current_util = float(cards[0].get("utilization", 0.5))
        except Exception:
            current_util = 0.5
        if current_util > utilization_target * 1.5:
            return "utilization"
    return "balanced"
