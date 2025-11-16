#!/usr/bin/env bash
# scripts/03_energy_toggle.sh
set -euo pipefail

: "${ENERGY_URL:=}"                     # optional override, e.g. http://localhost:8005
: "${ORCH_URL:=http://localhost:8000}"  # orchestration (for KPI snapshot, optional)

have_jq() { command -v jq >/dev/null 2>&1; }
pretty() { if have_jq; then jq .; else cat; fi }

discover_energy () {
  # Respect provided ENERGY_URL if it looks like energy
  if [ -n "${ENERGY_URL}" ]; then
    if curl -fsS "${ENERGY_URL}/openapi.json" >/dev/null 2>&1 || curl -fsS "${ENERGY_URL}/v1/health" >/dev/null 2>&1; then
      echo "${ENERGY_URL}"
      return 0
    fi
  fi
  # Otherwise scan common localhost ports
  for p in $(seq 8000 8010); do
    url="http://localhost:${p}"
    if curl -fsS "${url}/openapi.json" | jq -e '.paths | has("/v1/power")' >/dev/null 2>&1; then
      echo "${url}"
      return 0
    fi
    # fallback: see if /v1/health says energy
    if curl -fsS "${url}/v1/health" | grep -qi '"energy"' >/dev/null 2>&1; then
      echo "${url}"
      return 0
    fi
  done
  return 1
}

# POST helper that tries a few candidate endpoints & payload shapes
post_mode () {
  base="$1"; desired="$2"  # desired is "low" or "active"
  body_file="$(mktemp)"; code_file="$(mktemp)"
  trap 'rm -f "$body_file" "$code_file"' RETURN

  # Try a few likely endpoints and payloads
  endpoints="/v1/energy/mode /v1/mode /energy/mode /v1/power/mode"
  payloads=(
    "{\"mode\":\"$desired\"}"
    "{\"state\":\"$desired\"}"
  )
  for ep in $endpoints; do
    for json in "${payloads[@]}"; do
      curl -sS -o "$body_file" -w '%{http_code}' -X POST \
        -H 'Content-Type: application/json' \
        "${base}${ep}" -d "$json" > "$code_file" || true
      code="$(cat "$code_file")"
      if [ "$code" = "200" ] || [ "$code" = "204" ]; then
        cat "$body_file" | pretty
        return 0
      fi
    done
  done
  echo "ERROR: failed to set energy mode='${desired}' on ${base}" >&2
  echo "Last response (HTTP ${code}):" >&2
  cat "$body_file" | pretty >&2
  return 1
}

ENERGY="$(discover_energy || true)"
if [ -z "${ENERGY}" ]; then
  echo "ERROR: Could not find Energy service. Set ENERGY_URL or start the stack." >&2
  exit 1
fi

echo "== 03) Energy toggle demo =="
echo "--> Energy at: ${ENERGY}"
echo "--> Orchestration at: ${ORCH_URL}"

echo "--> Current power reading:"
curl -sS "${ENERGY}/v1/power" | pretty

echo "--> Set mode: low-power"
post_mode "${ENERGY}" "low"

echo "--> Verify lower power reading:"
curl -sS "${ENERGY}/v1/power" | pretty

# Optional: orchestration KPI snapshot after low-power
if curl -fsS "${ORCH_URL}/v1/kpi" >/dev/null 2>&1; then
  echo "--> Orchestration KPI snapshot (after low-power):"
  curl -sS "${ORCH_URL}/v1/kpi" | pretty
fi

echo "--> Set mode: active"
post_mode "${ENERGY}" "active"

echo "--> Verify active power reading:"
curl -sS "${ENERGY}/v1/power" | pretty

# Optional: orchestration KPI snapshot after return to active
if curl -fsS "${ORCH_URL}/v1/kpi" >/dev/null 2>&1; then
  echo "--> Orchestration KPI snapshot (after active):"
  curl -sS "${ORCH_URL}/v1/kpi" | pretty
fi

echo "== Energy toggle complete =="
