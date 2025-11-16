import httpx, time, json, os

BASES = {
  "ds":"http://localhost:8000",
  "orch":"http://localhost:8003",
  "sec":"http://localhost:8001",
  "con":"http://localhost:8002",
  "upd":"http://localhost:8004",
  "eng":"http://localhost:8005",
}

def get(url):  return httpx.get(url, timeout=5.0)
def post(url, **kw): return httpx.post(url, timeout=10.0, **kw)

def bump_rule(enable=True):
    cfg = get(f"{BASES['ds']}/v1/config/current").json()
    cfg["version"] += 1
    # ensure rule r1 exists
    rule = next((r for r in cfg["rules"] if r["id"]=="r1"), None)
    if rule: rule["enabled"] = enable
    else:
        cfg["rules"].append({"id":"r1","type":"url_block","value":"tiktok.com","enabled":enable})
    r = post(f"{BASES['orch']}/v1/config", json=cfg)
    assert r.status_code < 300

def test_block_rule():
    bump_rule(True)
    r = post(f"{BASES['sec']}/v1/eval", params={"client_id":"u1","url":"https://tiktok.com"})
    assert r.json()["allow"] is False

def test_10_client_load_and_metrics():
    # open 8 wifi + 2 lan
    for i in range(1,9):
        post(f"{BASES['con']}/v1/flows/open", json={"client_id":f"w{i}","link":"wifi","kbps":10000})
    for i in [1,2]:
        post(f"{BASES['con']}/v1/flows/open", json={"client_id":f"e{i}","link":"lan","kbps":940000})
    m = get(f"{BASES['con']}/v1/flows/metrics").json()
    assert m["aggregate_mbps"] > 100
    assert m["p95_latency_ms"] > 0
    # clean up
    for id_ in [f"w{i}" for i in range(1,9)] + ["e1","e2"]:
        post(f"{BASES['con']}/v1/flows/close", params={"client_id": id_})

def test_energy_night_mode_effect():
    post(f"{BASES['con']}/v1/flows/open",
         json={"client_id":"w1","link":"wifi","kbps":10000})
    m1 = get(f"{BASES['con']}/v1/flows/metrics").json()
    post(f"{BASES['eng']}/v1/policy/set", params={"mode":"night"})
    m2 = get(f"{BASES['con']}/v1/flows/metrics").json()
    post(f"{BASES['eng']}/v1/policy/set", params={"mode":"active"})
    post(f"{BASES['con']}/v1/flows/close", params={"client_id":"w1"})
    assert m2["p95_latency_ms"] >= m1["p95_latency_ms"]

def test_update_ok_and_rollback():
    # OK path
    post(f"{BASES['upd']}/v1/apply", params={"version":"2.0.0"})
    r = post(f"{BASES['upd']}/v1/health-report", params={"ok": True})
    assert r.json().get("activated") is True
    # Fail path → rollback
    post(f"{BASES['upd']}/v1/apply", params={"version":"2.0.0"})
    r = post(f"{BASES['upd']}/v1/health-report", params={"ok": False})
    assert r.json().get("activated") is False
