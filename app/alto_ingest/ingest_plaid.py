# alto-starter/app/alto_ingest/ingest_plaid.py
from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
import calendar, re

Date = str  # 'YYYY-MM-DD'

# ---------- date helpers ----------
def _dt(s: Date) -> datetime: return datetime.strptime(s, "%Y-%m-%d")
def _iso(d: datetime) -> Date: return d.strftime("%Y-%m-%d")
def _month_bounds(d: datetime) -> Tuple[datetime, datetime]:
    start = d.replace(day=1)
    end = d.replace(day=calendar.monthrange(d.year, d.month)[1])
    return start, end
def _clamp_to_month(anchor: Date, start: datetime, end: datetime) -> Tuple[Date, Date]:
    a = _dt(anchor); m0, m1 = _month_bounds(a)
    s = max(start, m0); e = min(end, m1)
    if e < s: s = e = a
    return _iso(s), _iso(e)
def _plus_days(d: Date, n: int) -> Date: return _iso(_dt(d) + timedelta(days=n))
def _minus_days(d: Date, n: int) -> Date: return _iso(_dt(d) - timedelta(days=n))


def _detect_frequency(dates: List[Date]) -> str:
    unique = sorted({_dt(d) for d in dates})
    if len(unique) < 2:
        return "one-time"
    spans = [(unique[i] - unique[i - 1]).days for i in range(1, len(unique))]
    avg = sum(spans) / len(spans)
    if 26 <= avg <= 32:
        return "monthly"
    if 12 <= avg <= 18:
        return "biweekly"
    if 6 <= avg <= 8:
        return "weekly"
    if 32 < avg <= 62:
        return "bimonthly"
    return "irregular"


def _group_summary(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        label = str(ev.get("label") or ev.get("category") or ev.get("id"))
        key = label.lower()
        grp = groups.setdefault(
            key,
            {
                "label": ev.get("label", label),
                "category": ev.get("category"),
                "merchant": ev.get("merchant"),
                "frequency": ev.get("frequency", "one-time"),
                "total_amount": 0.0,
                "count": 0,
                "last_date": ev.get("date"),
            },
        )
        amount = float(ev.get("amount", 0.0))
        grp["total_amount"] += amount
        grp["count"] += 1
        current_date = ev.get("date")
        if isinstance(current_date, str) and grp.get("last_date"):
            grp["last_date"] = max(grp["last_date"], current_date)
    summaries: List[Dict[str, Any]] = []
    for grp in groups.values():
        count = max(grp["count"], 1)
        avg = grp["total_amount"] / count
        summaries.append(
            {
                "label": grp["label"],
                "category": grp.get("category"),
                "merchant": grp.get("merchant"),
                "frequency": grp.get("frequency"),
                "average_amount": round(avg, 2),
                "count": grp["count"],
                "last_date": grp.get("last_date"),
            }
        )
    summaries.sort(key=lambda item: item["label"].lower())
    return summaries

# ---------- normalization ----------
_SUB_MERCHANTS = {
    "spotify":"Spotify","netflix":"Netflix","icloud":"iCloud","apple icloud":"iCloud",
    "apple.com/bill":"Apple Services","hulu":"Hulu","youtube":"YouTube",
    "amazon prime":"Amazon Prime","prime video":"Amazon Prime Video",
}
_UTIL_MERCHANTS = {
    "comcast":"Internet","xfinity":"Internet","at&t":"Internet","verizon fios":"Internet","spectrum":"Internet",
    "sdge":"Utilities","pg&e":"Utilities","pge":"Utilities","coned":"Utilities",
}
_RENT_PAT = re.compile(r"\brent\b|\bmortgage\b", re.I)

def _norm(s: Optional[str]) -> str: return (s or "").strip()

def _label_from_plaid(txn: Dict[str, Any]) -> tuple[str, str]:
    """
    Returns (normalized_label, category_tag)
    category_tag ∈ {'income','rent','utilities','internet','subscription','card_payment','other'}
    """
    name = _norm(txn.get("name")); merch = _norm(txn.get("merchant_name"))
    cat = txn.get("personal_finance_category") or {}
    primary = (cat.get("primary") or "").upper()
    detailed = (cat.get("detailed") or "").upper()

    if primary == "INCOME" or "INCOME" in detailed:
        return "Paycheck", "income"
    if "TRANSFER_OUT_CREDIT_CARD_PAYMENT" in detailed:
        return "Card Payment", "card_payment"
    if "TRANSFER_OUT_RENT" in detailed or _RENT_PAT.search(name) or _RENT_PAT.search(merch):
        return "Rent", "rent"

    merch_l = merch.lower(); name_l = name.lower()
    for key, lbl in _UTIL_MERCHANTS.items():
        if key in merch_l or key in name_l:
            return ("Internet" if lbl == "Internet" else "Utilities", "internet" if lbl=="Internet" else "utilities")

    if detailed.startswith("UTILITIES_"):
        return ("Internet","internet") if "INTERNET" in detailed else ("Utilities","utilities")

    if detailed.endswith("_SUBSCRIPTIONS") or "SUBSCRIPTION" in detailed:
        title = None
        for k, v in _SUB_MERCHANTS.items():
            if k in merch_l or k in name_l:
                title = v; break
        return f"Subscription: {title or 'Recurring'}", "subscription"

    for k, v in _SUB_MERCHANTS.items():
        if k in merch_l or k in name_l:
            return f"Subscription: {v}", "subscription"

    return (name or merch or "Payment"), "other"

# ---------- windows ----------
def _window_for(category: str, date: Date) -> Optional[Dict[str, Date]]:
    if category == "subscription":
        s, e = _dt(_plus_days(date, 3)), _dt(_plus_days(date, 7))
    elif category == "internet":
        s, e = _dt(_minus_days(date, 2)), _dt(_plus_days(date, 5))
    elif category == "utilities":
        s, e = _dt(_minus_days(date, 3)), _dt(_plus_days(date, 5))
    elif category == "card_payment":
        s, e = _dt(_minus_days(date, 3)), _dt(_plus_days(date, 3))
    else:
        return None
    start, end = _clamp_to_month(date, s, e)
    return {"start": start, "end": end}

# ---------- main ----------
def plaid_to_agent_payload(plaid: Dict[str, Any]) -> Dict[str, Any]:
    accounts = plaid.get("accounts") or []
    added = plaid.get("added") or []
    modified = plaid.get("modified") or []
    txns = list(added) + list(modified)

    currency = "USD"
    if accounts:
        bal = (accounts[0].get("balances") or {})
        currency = bal.get("iso_currency_code") or currency

    seen: set[str] = set()
    cash_in: List[Dict[str, Any]] = []
    cash_out: List[Dict[str, Any]] = []
    events_by_key: Dict[str, List[Dict[str, Any]]] = {}

    def _valid_amount(t: Dict[str, Any]) -> bool:
        try:
            return float(t.get("amount")) > 0
        except Exception:
            return False

    def _register(event: Dict[str, Any]) -> None:
        key = f"{str(event.get('label', '')).lower()}::{str(event.get('merchant', '')).lower()}"
        events_by_key.setdefault(key, []).append(event)

    for t in txns:
        tid = t.get("transaction_id")
        if not tid or tid in seen:
            continue
        if not _valid_amount(t):
            continue
        seen.add(tid)

        amount = float(t["amount"])
        date = t.get("date")
        if not date:
            continue

        label, cat = _label_from_plaid(t)
        raw_name = _norm(t.get("name"))
        raw_merchant = _norm(t.get("merchant_name"))
        category_info = t.get("personal_finance_category") or {}

        base_event: Dict[str, Any] = {
            "id": tid,
            "label": label,
            "date": date,
            "amount": amount,
            "category": cat,
            "merchant": raw_merchant or raw_name,
            "frequency": "one-time",
            "source": "plaid",
            "metadata": {
                "original_name": raw_name,
                "merchant_name": raw_merchant,
                "plaid_category": category_info,
            },
        }

        if cat == "income":
            base_event["fixed"] = True
            detail = (category_info.get("detailed") or "").upper()
            base_event["stream"] = "salary" if "PAYCHECK" in detail else "income"
            cash_in.append(base_event)
            _register(base_event)
            continue

        if cat in {"rent", "utilities", "internet", "subscription", "card_payment"}:
            win = _window_for(cat, date)
            base_event["fixed"] = (cat == "rent")
            if win:
                base_event["window"] = win
            if cat == "subscription":
                base_event["metadata"]["subscription_hint"] = base_event.get("merchant") or base_event["label"]
            cash_out.append(base_event)
            _register(base_event)
            continue

        # Discretionary or other categories (still useful for insights)
        base_event["fixed"] = False
        cash_out.append(base_event)
        _register(base_event)

    cash_in.sort(key=lambda e: e["date"])
    cash_out.sort(key=lambda e: e["date"])

    for events in events_by_key.values():
        dates = [ev.get("date") for ev in events if ev.get("date")]
        if not dates:
            continue
        freq = _detect_frequency(dates)
        observed = sorted({*dates})
        for ev in events:
            ev["frequency"] = freq
            meta = ev.setdefault("metadata", {})
            meta["observed_dates"] = observed

    policy = {
        "buffer_min": 300,
        "never_move": ["Rent"],
        "weekend_payments": False,
        "bnpl_guard_days": 7,
        "utilization_targets": {"default": 0.10},
    }

    salary_stream = max(
        (ev for ev in cash_in if ev.get("stream") == "salary"),
        key=lambda ev: ev.get("amount", 0.0),
        default=None,
    )
    if salary_stream:
        policy["primary_income"] = {
            "label": salary_stream["label"],
            "amount": salary_stream["amount"],
            "frequency": salary_stream.get("frequency"),
            "merchant": salary_stream.get("merchant"),
        }

    subscriptions_summary = [
        {
            "id": ev["id"],
            "label": ev["label"],
            "amount": ev["amount"],
            "merchant": ev.get("merchant"),
            "frequency": ev.get("frequency"),
            "date": ev["date"],
        }
        for ev in cash_out
        if ev.get("category") == "subscription"
    ]

    recurring_expenses = _group_summary(
        [ev for ev in cash_out if ev.get("frequency") not in {"one-time"}]
    )
    income_streams = _group_summary(cash_in)

    meta = {
        "income_streams": income_streams,
        "recurring_expenses": recurring_expenses,
        "subscriptions": subscriptions_summary,
        "salary_stream": {
            "label": salary_stream["label"],
            "amount": salary_stream["amount"],
            "frequency": salary_stream.get("frequency"),
            "merchant": salary_stream.get("merchant"),
            "date": salary_stream.get("date"),
        }
        if salary_stream
        else None,
    }

    return {
        "user": {"id": "usr_demo", "tz": "America/Los_Angeles", "currency": currency},
        "policy": policy,
        "cashIn": cash_in,
        "cashOut": cash_out,
        "cards": [],
        "bnplPlans": [],
        "intent": {"name": "fee_proof", "params": {}},
        "meta": meta,
    }
