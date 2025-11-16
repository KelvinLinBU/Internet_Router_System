#!/usr/bin/env bash
set -euo pipefail

# ---------- Config (override via env if needed) ----------
ORCH_URL="${ORCH_URL:-http://localhost:8000}"
DS_URL="${DS_URL:-http://localhost:8001}"
SEC_URL="${SEC_URL:-http://localhost:8002}"
CONN_URL="${CONN_URL:-http://localhost:8003}"
UPDATE_URL="${UPDATE_URL:-http://localhost:8004}"
ENERGY_URL="${ENERGY_URL:-http://localhost:8005}"
UI_URL="${UI_URL:-http://localhost:3000}"

JQ_BIN="${JQ:-jq}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="$ROOT_DIR/scripts"

# ---------- Helpers ----------
pretty() {
  if command -v "$JQ_BIN" >/dev/null 2>&1; then
    "$JQ_BIN" .
  else
    cat
  fi
}

wait_on() {
  local url="$1"
  local path="${2:-/v1/health}"
  local name="${3:-$url}"
  local tries=30
  echo "   waiting for $name ($url$path) ..."
  for i in $(seq 1 "$tries"); do
    if curl -sfS "$url$path" >/dev/null 2>&1; then
      echo "   $name is up."
      return 0
    fi
    sleep 1
  done
  echo "!! timeout waiting for $name ($url$path)" >&2
  return 1
}

kpi_snapshots() {
  echo "--> Orchestration KPI:"
  curl -sfS "$ORCH_URL/v1/kpi" | pretty || true
  echo "--> Connectivity KPI:"
  curl -sfS "$CONN_URL/v1/kpi" | pretty || true
  echo "--> Energy power:"
  curl -sfS "$ENERGY_URL/v1/power" | pretty || true
}

# ---------- Start ----------
echo "== DEMO: start =="

echo "0) Health checks:"
wait_on "$ORCH_URL" "/v1/health" "orchestration"
wait_on "$DS_URL" "/v1/health" "datastore"
wait_on "$SEC_URL" "/v1/health" "security"
wait_on "$CONN_URL" "/v1/health" "connectivity"
wait_on "$UPDATE_URL" "/v1/health" "update"
wait_on "$ENERGY_URL" "/v1/health" "energy"


echo
echo "KPI snapshot before actions:"
kpi_snapshots

echo
echo "1) Blocklist demo (block tiktok.com)"
bash "$SCRIPTS_DIR/01_block_tiktok.sh" || {
  echo "   01_block_tiktok.sh returned non-zero; continuing to next step."
}

echo
echo "KPI snapshot after blocklist:"
kpi_snapshots

echo
echo "2) Load 10 clients"
bash "$SCRIPTS_DIR/02_load_10_clients.sh" || {
  echo "   02_load_10_clients.sh returned non-zero; continuing to next step."
}

echo
echo "KPI snapshot after clients:"
kpi_snapshots

echo
echo "3) Energy toggle (active -> standby -> active)"
bash "$SCRIPTS_DIR/03_energy_toggle.sh" || {
  echo "   03_energy_toggle.sh returned non-zero; continuing to next step."
}

echo
echo "KPI snapshot after energy toggle:"
kpi_snapshots

echo
echo "4) Update success then rollback"
bash "$SCRIPTS_DIR/04_update_success_then_rollback.sh" || {
  echo "   04_update_success_then_rollback.sh returned non-zero; continuing."
}

echo
echo "Final KPI snapshot:"
kpi_snapshots

echo
echo "== DEMO: complete =="
echo "Tip: run 'bash scripts/99_cleanup.sh' to reset the environment."
