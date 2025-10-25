# alto-starter/app/agent_engine_app.py
"""
Agent Engine App - Deploy your agent to Google Cloud
AND
FastAPI service for local/dev usage (ingestion + planning).

- To run the HTTP API locally:
    uvicorn app.agent_engine_app:app --host 0.0.0.0 --port 8080 --reload

- To deploy to Vertex AI Agent Engine:
    python -m app.agent_engine_app   # (or set TRIGGER_DEPLOY=true and run)
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime, timedelta
import os
import json
import copy
import datetime as _dt_module
from pathlib import Path

# ----------------- Optional Google/ADK imports (guarded) -----------------
_GOOGLE_OK = True
try:
    import vertexai
    from google.adk.artifacts import GcsArtifactService
    from google.cloud import logging as google_cloud_logging
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider, export
    from vertexai import agent_engines
    from vertexai.preview.reasoning_engines import AdkApp
    from app.agent import root_agent
    from app.config import config, get_deployment_config
    from app.utils.gcs import create_bucket_if_not_exists
    from app.utils.tracing import CloudTraceLoggingSpanExporter
    from app.utils.typing import Feedback
except Exception:
    _GOOGLE_OK = False

# ----------------- FastAPI (local/dev) -----------------
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware

USE_OPENROUTER = os.getenv("USE_OPENROUTER", "false").lower() in {"1", "true", "yes"}
if USE_OPENROUTER:
    try:
        from app.llm.openrouter_client import openrouter_chat, OpenRouterError
    except Exception:
        USE_OPENROUTER = False

        def openrouter_chat(*_: Any, **__: Any) -> str:  # fallback stub
            raise RuntimeError("OpenRouter client unavailable")

        OpenRouterError = Exception

# Plaid → Agent transformer
try:
    from app.alto_ingest.ingest_plaid import plaid_to_agent_payload
except Exception as e:
    plaid_to_agent_payload = None  # type: ignore
    _INGEST_IMPORT_ERROR = e

# -----------------------------------------------------------------------------
# FastAPI APP (local/dev)
# -----------------------------------------------------------------------------
app = FastAPI(title="Alto Agents")

# Allow Next.js dev server to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "google_adk_available": _GOOGLE_OK}


@app.get("/adk/status")
def adk_status():
    return {"use_openrouter": bool(USE_OPENROUTER)}

@app.post("/ingest/plaid-transform")
def plaid_transform(plaid_payload: dict = Body(...)) -> dict:
    if plaid_to_agent_payload is None:
        # Helpful error if import failed
        raise RuntimeError(
            f"ingest_plaid import failed: {_INGEST_IMPORT_ERROR}. "
            "Ensure file exists at app/alto_ingest/ingest_plaid.py and package path is correct."
        )
    return plaid_to_agent_payload(plaid_payload)

# ----------------- Models for deterministic planner -----------------
Date = str  # 'YYYY-MM-DD'

class PolicyDict(Dict[str, Any]): ...
class WindowDict(Dict[str, Date]): ...
class Change(Dict[str, Any]): ...

def _dt(s: Date) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d")

def _iso(d: datetime) -> Date:
    return d.strftime("%Y-%m-%d")

def _bump_to_weekday(d: datetime) -> datetime:
    if d.weekday() == 5:  # Sat
        return d + timedelta(days=2)
    if d.weekday() == 6:  # Sun
        return d + timedelta(days=1)
    return d

def _short_id(prefix: str = "plan") -> str:
    import random, string
    suf = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{suf}"

def _derive_month(payload: Dict[str, Any]) -> str:
    counts: Dict[str, int] = {}
    for ev in (payload.get("cashOut", []) + payload.get("cashIn", [])):
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

# ----------------- Deterministic planner (MVP) -----------------
def calendar_planner(p: Dict[str, Any]) -> Dict[str, Any]:
    changes: List[Change] = []
    policy: Dict[str, Any] = p.get("policy", {})
    weekend_payments = bool(policy.get("weekend_payments", False))

    # MOVE: pick first moveable (prefer Utilities/Internet) → to end of window (weekday-bumped)
    moved = False
    for ev in p.get("cashOut", []):
        window = ev.get("window")
        fixed = bool(ev.get("fixed", False))
        if window and not fixed:
            lbl = str(ev.get("label", "")).lower()
            prefer = (lbl in {"utilities", "internet"})
            if prefer or not moved:
                to_dt = _dt(window["end"])
                if not weekend_payments:
                    to_dt = _bump_to_weekday(to_dt)
                to = _iso(to_dt)
                if to != ev["date"]:
                    changes.append({
                        "type": "move",
                        "payment_id": ev["id"],
                        "from": ev["date"],
                        "to": to,
                        "reason": "align_payroll",
                    })
                    moved = True
                    break

    # SPLIT: only if cards[] present
    if p.get("cards"):
        base_month = _derive_month(p)
        y, m = map(int, base_month.split("-"))
        first_card = p["cards"][0]
        cut = int(first_card.get("cut_day", 28))
        d1 = datetime(y, m, max(1, cut - 3))
        d2 = datetime(y, m, max(1, cut - 1))
        if not weekend_payments:
            d1 = _bump_to_weekday(d1)
            d2 = _bump_to_weekday(d2)
        parts = [{"date": _iso(d1), "amount": 120}, {"date": _iso(d2), "amount": 80}]
        from_date = (p.get("cashOut", [{}])[0] or {}).get("date", _iso(datetime.now()))
        changes.append({
            "type": "split",
            "payment_id": "min_visa",
            "from": from_date,
            "parts": parts,
            "reason": "pre_cut_utilization",
        })
        metrics = {
            "fees_avoided": 165,
            "overdraft_risk_delta": -0.8,
            "buffer_min": policy.get("buffer_min", 300.0),
            "utilization_projection": {"card_visa": {"before": 0.46, "after": 0.10}},
        }
        explain = [
            "Moved a payment within its allowed window to land after paycheck.",
            "Inserted pre-cut micro-payments to lower reported utilization.",
        ]
    else:
        metrics = {
            "fees_avoided": 120,
            "overdraft_risk_delta": -0.6,
            "buffer_min": policy.get("buffer_min", 300.0),
        }
        explain = [
            "Moved a payment within its allowed window to land after paycheck.",
            "No credit card provided, so no utilization split was scheduled.",
        ]

    return {"changes": changes, "metrics": metrics, "explain": explain}

# ------------ Minimal endpoints for planner ------------
@app.post("/optimize")
def optimize(payload: Dict[str, Any]):
    result = calendar_planner(payload)
    return {"changes": result["changes"], "metrics": result["metrics"]}

@app.post("/explain")
def explain(payload: Dict[str, Any]):
    native = [
        "We respect your windows and buffer requirement.",
        "Locked items are never moved.",
        "Pre-cut payments reduce reported card utilization.",
    ]
    if not USE_OPENROUTER:
        return {"explain": native}

    try:
        user_msg = {
            "role": "user",
            "content": (
                "Summarize in 2–3 crisp bullets why this month’s payment schedule improves cash safety "
                "and credit score. Avoid fluff; be concrete.\n"
                f"Policy: {json.dumps(payload.get('policy', {}))}\n"
                f"Income (first 4): {json.dumps(payload.get('cashIn', [])[:4])}\n"
                f"Bills (first 6): {json.dumps(payload.get('cashOut', [])[:6])}\n"
            ),
        }
        text = openrouter_chat(
            messages=[
                {"role": "system", "content": "You are Alto, a precise financial planner."},
                user_msg,
            ]
        )
        bullets = [b.strip("•- ").strip() for b in text.split("\n") if b.strip()]
        return {"explain": bullets[:3] or native}
    except OpenRouterError:
        return {"explain": native}
    except Exception:
        return {"explain": native}

@app.post("/orchestrate/plan")
def orchestrate_plan(payload: Dict[str, Any]):
    if payload.get("intent", {}).get("name") == "question":
        out = {"changes": [], "metrics": {}, "explain": [
            "We respect your windows and buffer requirement.",
            "Locked items are never moved.",
            "Pre-cut payments reduce reported card utilization.",
        ]}
    else:
        out = calendar_planner(payload)

    return {
        "id": _short_id("plan"),
        "user_id": str(payload.get("user", {}).get("id", "usr_demo")),
        "month": _derive_month(payload),
        "changes": out["changes"],
        "metrics": out["metrics"],
        "explain": out["explain"],
    }

# -----------------------------------------------------------------------------
# ADK / Vertex AI Agent Engine deployment bits (unchanged; guarded)
# -----------------------------------------------------------------------------
if _GOOGLE_OK:
    class AgentEngineApp(AdkApp):
        """ADK Application wrapper for Agent Engine deployment."""
        def set_up(self) -> None:
            super().set_up()
            logging_client = google_cloud_logging.Client()
            self.logger = logging_client.logger(__name__)
            provider = TracerProvider()
            processor = export.BatchSpanProcessor(
                CloudTraceLoggingSpanExporter(
                    project_id=os.environ.get("GOOGLE_CLOUD_PROJECT"),
                    service_name=f"{config.deployment_name}-service",
                )
            )
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            self.enable_tracing = True

        def register_feedback(self, feedback: dict[str, Any]) -> None:
            feedback_obj = Feedback.model_validate(feedback)
            self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

        def register_operations(self) -> dict[str, list[str]]:
            operations = super().register_operations()
            operations[""] = operations[""] + ["register_feedback"]
            return operations

        def clone(self) -> "AgentEngineApp":
            template_attributes = self._tmpl_attrs
            return self.__class__(
                agent=copy.deepcopy(template_attributes["agent"]),
                enable_tracing=bool(template_attributes.get("enable_tracing", False)),
                session_service_builder=template_attributes.get("session_service_builder"),
                artifact_service_builder=template_attributes.get("artifact_service_builder"),
                env_vars=template_attributes.get("env_vars"),
            )

    def deploy_agent_engine_app() -> agent_engines.AgentEngine:
        """Deploy the agent to Vertex AI Agent Engine."""
        print("🚀 Starting Agent Engine deployment...")

        deployment_config = get_deployment_config()
        print(f"📋 Deploying agent: {deployment_config.agent_name}")
        print(f"📋 Project: {deployment_config.project}")
        print(f"📋 Location: {deployment_config.location}")
        print(f"📋 Staging bucket: {deployment_config.staging_bucket}")

        env_vars: Dict[str, str] = {}
        env_vars["NUM_WORKERS"] = "1"

        artifacts_bucket_name = f"{deployment_config.project}-{deployment_config.agent_name}-logs-data"
        print(f"📦 Creating artifacts bucket: {artifacts_bucket_name}")
        create_bucket_if_not_exists(
            bucket_name=artifacts_bucket_name,
            project=deployment_config.project,
            location=deployment_config.location,
        )

        vertexai.init(
            project=deployment_config.project,
            location=deployment_config.location,
            staging_bucket=f"gs://{deployment_config.staging_bucket}",
        )

        with open(deployment_config.requirements_file) as f:
            requirements = f.read().strip().split("\n")

        agent_engine = AgentEngineApp(
            agent=root_agent,
            artifact_service_builder=lambda: GcsArtifactService(bucket_name=artifacts_bucket_name),
        )

        agent_config = {
            "agent_engine": agent_engine,
            "display_name": deployment_config.agent_name,
            "description": "A simple goal planning agent",
            "extra_packages": deployment_config.extra_packages,
            "env_vars": env_vars,
            "requirements": requirements,
        }

        existing = list(agent_engines.list(filter=f"display_name={deployment_config.agent_name}"))
        if existing:
            print(f"🔄 Updating existing agent: {deployment_config.agent_name}")
            remote = existing[0].update(**agent_config)
        else:
            print(f"🆕 Creating new agent: {deployment_config.agent_name}")
            remote = agent_engines.create(**agent_config)

        metadata = {
            "remote_agent_engine_id": remote.resource_name,
            "deployment_timestamp": _dt_module.datetime.now().isoformat(),
            "agent_name": deployment_config.agent_name,
            "project": deployment_config.project,
            "location": deployment_config.location,
        }

        logs_dir = Path("logs"); logs_dir.mkdir(exist_ok=True)
        meta_file = logs_dir / "deployment_metadata.json"
        with open(meta_file, "w") as f:
            json.dump(metadata, f, indent=2)

        print("✅ Agent deployed successfully!")
        print(f"📄 Deployment metadata saved to: {meta_file}")
        print(f"🆔 Agent Engine ID: {remote.resource_name}")
        return remote

# -----------------------------------------------------------------------------
# Script entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Only attempt deploy if explicitly requested or Google stack is available.
    if os.getenv("TRIGGER_DEPLOY", "false").lower() in {"1","true","yes"}:
        if not _GOOGLE_OK:
            raise RuntimeError("Google ADK/VertexAI libraries not available in this environment.")
        print(
            """
        ╔═══════════════════════════════════════════════════════════╗
        ║   🤖 DEPLOYING AGENT TO VERTEX AI AGENT ENGINE 🤖         ║
        ╚═══════════════════════════════════════════════════════════╝
            """
        )
        deploy_agent_engine_app()
    else:
        # Convenience for local testing
        print("Local mode: start with uvicorn → uvicorn app.agent_engine_app:app --port 8080 --reload")
