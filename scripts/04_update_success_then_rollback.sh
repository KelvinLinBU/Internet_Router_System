#!/usr/bin/env bash
set -euo pipefail

UPDATE_URL="${UPDATE_URL:-http://localhost:8004}"
JQ_BIN="${JQ:-jq}"

echo "== 04) Update to a new version, then simulate a failure and rollback =="

echo "--> Check for updates"
curl -sfS -X POST "$UPDATE_URL/v1/check" | ${JQ_BIN} -r '.available_version as $v | "available_version=\($v)"'

# Apply a new version (service mocks the download/apply)
NEWV="${1:-demo-2}"
echo "--> Apply version: $NEWV"
curl -sfS -X POST "$UPDATE_URL/v1/apply" \
  -H 'Content-Type: application/json' \
  -d "{\"version\":\"$NEWV\"}" | ${JQ_BIN} -r '.applied_version as $v | "applied_version=\($v)"'

echo "--> Current update status:"
curl -sfS "$UPDATE_URL/v1/status" | ${JQ_BIN} .

# Simulate a bad health check and leave current applied as-is (apply with simulate_fail)
BADV="${2:-demo-bad}"
echo "--> Simulate failed apply for version: $BADV"
curl -sfS -X POST "$UPDATE_URL/v1/apply" \
  -H 'Content-Type: application/json' \
  -d "{\"version\":\"$BADV\",\"simulate_fail\":true}" | ${JQ_BIN} -r '.last_result'

# Now roll back to previous (should swap applied <-> previous)
echo "--> Roll back to previous"
curl -sfS -X POST "$UPDATE_URL/v1/rollback" | ${JQ_BIN} -r '.last_result'

echo "--> Status after rollback:"
curl -sfS "$UPDATE_URL/v1/status" | ${JQ_BIN} .
