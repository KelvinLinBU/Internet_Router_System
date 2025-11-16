#!/usr/bin/env bash
# scripts/02_load_10_clients.sh
set -euo pipefail

COUNT="${1:-10}"
: "${ORCH_URL:=http://localhost:8000}"   # orchestration (aggregated KPIs)
: "${CONN_URL:=}"                        # connectivity (auto-discover if empty)

have_jq() { command -v jq >/dev/null 2>&1; }
pretty() { if have_jq; then jq .; else cat; fi }

discover_connectivity () {
  # Respect provided CONN_URL if it has the endpoint
  if [ -n "${CONN_URL}" ]; then
    if curl -fsS "${CONN_URL}/openapi.json" | jq -e '.paths | has("/v1/clients/simulate")' >/dev/null 2>&1; then
      echo "${CONN_URL}"
      return 0
    fi
  fi
  # Otherwise scan common localhost ports
  for p in $(seq 8000 8010); do
    url="http://localhost:${p}"
    if curl -fsS "${url}/openapi.json" | jq -e '.paths | has("/v1/clients/simulate")' >/dev/null 2>&1; then
      echo "${url}"
      return 0
    fi
  done
  return 1
}

CONN="$(discover_connectivity || true)"
if [ -z "${CONN}" ]; then
  echo "ERROR: Could not find connectivity service. Set CONN_URL or start the stack." >&2
  exit 1
fi

echo "== 02) Simulate ${COUNT} clients =="
echo "--> Connectivity at: ${CONN}"
echo "--> Orchestration at: ${ORCH_URL}"

# --- POST /v1/clients/simulate with BSD-safe body/status capture ---
body_file="$(mktemp)"; code_file="$(mktemp)"
trap 'rm -f "$body_file" "$code_file"' EXIT

curl -sS -o "$body_file" -w '%{http_code}' \
  -X POST "${CONN}/v1/clients/simulate" \
  -H 'Content-Type: application/json' \
  -d "{\"count\":${COUNT}}" > "$code_file"

code="$(cat "$code_file")"
if [ "$code" != "200" ]; then
  echo "ERROR: simulate clients HTTP $code"
  cat "$body_file" | pretty
  exit 1
fi

cat "$body_file" | pretty

echo "--> Connectivity KPI (should show active_clients = ${COUNT}):"
curl -sS "${CONN}/v1/kpi" | pretty

echo "--> Orchestration KPI snapshot (aggregated):"
curl -sS "${ORCH_URL}/v1/kpi" | pretty
