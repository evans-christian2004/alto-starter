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

    def _valid_amount(t: Dict[str, Any]) -> bool:
        try: return float(t.get("amount")) > 0
        except: return False

    for t in txns:
        tid = t.get("transaction_id"); 
        if not tid or tid in seen: continue
        if not _valid_amount(t): continue
        seen.add(tid)

        amount = float(t["amount"]); date = t.get("date")
        if not date: continue

        label, cat = _label_from_plaid(t)

        if cat == "income":
            cash_in.append({"id": tid, "label": label, "date": date, "amount": amount, "fixed": True})
            continue

        if cat in {"rent","utilities","internet","subscription","card_payment"}:
            win = _window_for(cat, date)
            fixed = (cat == "rent")
            cash_out.append({
                "id": tid, "label": label, "date": date, "amount": amount, "fixed": fixed, "window": win
            })

    cash_in.sort(key=lambda e: e["date"])
    cash_out.sort(key=lambda e: e["date"])

    policy = {
        "buffer_min": 300,
        "never_move": ["Rent"],
        "weekend_payments": False,
        "bnpl_guard_days": 7,
        "utilization_targets": {"default": 0.10},
    }

    return {
        "user": {"id": "usr_demo", "tz": "America/Los_Angeles", "currency": currency},
        "policy": policy,
        "cashIn": cash_in,
        "cashOut": cash_out,
        "cards": [],
        "bnplPlans": [],
        "intent": {"name": "fee_proof", "params": {}},
    }
