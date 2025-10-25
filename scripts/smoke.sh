#!/usr/bin/env bash
set -euo pipefail

AGENT_URL=${AGENT_URL:-http://localhost:8080}
SAMPLE=${SAMPLE:-app/examples/plaid_sample.json}

workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

payload="$workdir/agent_payload.json"
with_card="$workdir/with_card.json"

echo "== health =="
curl -s "$AGENT_URL/health" | jq .

echo "== ingest =="
curl -s -X POST "$AGENT_URL/ingest/plaid-transform" \
  -H 'Content-Type: application/json' \
  --data-binary @"$SAMPLE" \
  | tee "$payload" >/dev/null

jq '.cards=[{"id":"card_visa","limit":5000,"balance":860,"cut_day":28,"due_day":21}]' \
  "$payload" >"$with_card"

echo "== optimize (auto focus) =="
curl -s -X POST "$AGENT_URL/optimize" \
  -H 'Content-Type: application/json' \
  --data-binary @"$payload" | jq .

echo "== plan (with card) =="
curl -s -X POST "$AGENT_URL/orchestrate/plan" \
  -H 'Content-Type: application/json' \
  --data-binary @"$with_card" | jq .

echo "== explain =="
curl -s -X POST "$AGENT_URL/explain" \
  -H 'Content-Type: application/json' \
  --data-binary @"$payload" | jq .

echo "== agent session =="
curl -s -X POST "$AGENT_URL/agent/session" \
  -H 'Content-Type: application/json' \
  --data-binary @"$with_card" | jq .
