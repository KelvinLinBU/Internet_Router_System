#!/usr/bin/env bash
set -euo pipefail

SEC="http://localhost:8002"

echo "== 01) Block 'tiktok.com' =="

add_domain_json() {
  local d="$1"
  curl -sS -X POST "$SEC/v1/blocklist/add" \
    -H 'Content-Type: application/json' \
    -d "{\"domains\":[\"$d\"]}" >/dev/null
}

add_domain_query() {
  local d="$1"
  curl -sS -X POST "$SEC/v1/blocklist/add?domain=$d" >/dev/null
}

add_domain() {
  local d="$1"
  # Try JSON body first; if it 4xx's, fall back to query param
  if ! add_domain_json "$d" 2>/dev/null; then
    add_domain_query "$d"
  fi
}

echo "--> Add to blocklist"
for dom in "tiktok.com" "bad.example"; do
  if add_domain "$dom"; then
    echo "   + blocked: $dom"
  else
    echo "   ! failed to block: $dom"
  fi
done

echo "--> Show blocklist"
curl -s "$SEC/v1/blocklist" | jq .
