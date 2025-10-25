"""Ingestion utilities for local JSON fixtures and future Plaid integration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from app.alto_ingest.ingest_plaid import plaid_to_agent_payload


def load_cashflow_from_file(path: str | Path) -> Dict[str, Any]:
    """Load a Plaid-style JSON fixture and transform it into the agent payload."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Cashflow fixture not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return plaid_to_agent_payload(data)
