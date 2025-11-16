#!/usr/bin/env bash
set -euo pipefail

SECURITY_URL="${SECURITY_URL:-http://localhost:8002}"
CONN_URL="${CONN_URL:-http://localhost:8003}"
ENERGY_URL="${ENERGY_URL:-http://localhost:8005}"
UPDATE_URL="${UPDATE_URL:-http://localhost:8004}"
ORCH_URL="${ORCH_URL:-http://localhost:8000}"

echo "== 99) Cleanup/reset demo state =="

echo "--> Clear security blocklist"
curl -sfS -X POST "$SECURITY_URL/v1/blocklist/set" \
  -H 'Content-Type: application/json' \
  -d '{"domains":[]}' >/dev/null || true

echo "--> Clear simulated clients"
curl -sfS -X POST "$CONN_URL/v1/simulate/clients" \
  -H 'Content-Type: application/json' \
  -d '{"count":0}' >/dev/null || true

echo "--> Ensure energy mode=active"
curl -sfS -X POST "$ENERGY_URL/v1/mode" \
  -H 'Content-Type: application/json' \
  -d '{"mode":"active"}' >/dev/null || true

echo "--> Reset updater state (if supported)"
curl -sfS -X POST "$UPDATE_URL/v1/reset" >/dev/null || true

echo "--> Final KPI snapshot:"
curl -sfS "$ORCH_URL/v1/kpi" | ${JQ:-jq} .

echo "== Cleanup complete =="
