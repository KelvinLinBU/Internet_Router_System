# Simple Home Router — Systems Engineering Demo 

This repo is a **systems engineering demonstration** for a budget home router.  
We model the router as **six cooperating components** (each its own containerized “system”) that **interact via HTTP APIs**:

- **UI** — end-user setup and status
- **Orchestration** — command & control
- **Data Store** — single source of truth for config, logs, and metadata
- **Connectivity** — WAN↔LAN traffic, DHCP/NAT, Wi-Fi presence 
- **Security** — SPI firewall, parental/guest policies
- **Energy** — power modes, watts
- **Update** — firmware check/apply/rollback

> Goal: show a **functional architecture** with clear **traceability** to requirements, a **repeatable test harness**, and **observable behavior** via simple APIs.  

---

## Why this approach (Systems Engineering context)

- **Functional decomposition**: We separate what the router **does** into independent functions (UI, Connectivity, Security, Update, Energy, Data Store, Orchestration).  
- **Clear interfaces**: Components communicate over **explicit REST endpoints**. That makes contracts testable and integration predictable.  
- **Traceability**: Each function exists because of a **requirement** (e.g., Update → auto updates; Security → rules & parental controls; Energy → power caps).  
- **MBSE-lite**: The running system + endpoints + demo scripts are a **living model** of behaviors and interfaces. The scripts simulate scenarios you’ll verify later as integration tests.

---

## Architecture at a Glance

```
[ UI ]  ──(API)──>  [ Orchestration ] ──writes/reads──> [ Data Store ]
                     │       │   │   \
                     │       │   │    \──notify/collect KPIs──> [ Update ]
                     │       │   └─────notify/collect KPIs──> [ Energy ]
                     │       └─────────notify/collect KPIs──> [ Security ]
                     └─────────────────notify/collect KPIs──> [ Connectivity ]

Traffic path (simulated): Clients → Connectivity → (Security policy decision) → WAN/LAN
```

- **Only Orchestration writes** to the **Data Store**; other functions **read on notify**.  
- **KPIs** (throughput/latency, rules active, power, clients) are pulled by Orchestration for status.

---

## What each service does

- **UI**  
  Minimal FastAPI app for “user-facing” endpoints; in this demo it’s a placeholder to show the pattern (runs on `:3000`).

- **Orchestration**  
  Central controller. Applies configuration versions to the Data Store, **notifies** functions to reload, and aggregates KPIs. Endpoints:
  - `GET /v1/health`
  - `GET /v1/status` — current config version and KPI snapshot
  - `GET /v1/kpi` — merged KPIs
  - `POST /v1/config/apply` — `{version, payload}` → writes Data Store, notifies functions

- **Data Store**  
  In-memory store for **config**, **blocklist**, and light **logs/metadata**. Endpoints:
  - `GET /v1/health`
  - `GET /v1/config` / `POST /v1/config`
  - `GET /v1/blocklist` / `POST /v1/blocklist` (domain entries)

- **Connectivity** *(simulated)*  
  Pretends to manage DHCP/NAT/Wi-Fi and track **active clients** + **throughput/latency**. Endpoints:
  - `GET /v1/health`
  - `POST /v1/notify/config`
  - `GET /v1/kpi` — `{throughput_mbps, p95_latency_ms, active_clients}`
  - `POST /v1/clients/simulate` — `{count}` to load up “clients”
  - `GET /v1/clients` — current simulated clients

- **Security** *(simulated)*  
  SPI firewall + parental controls. Can accept a **blocklist** from Data Store and expose **rules count**. Endpoints:
  - `GET /v1/health`
  - `POST /v1/notify/config`
  - `GET /v1/kpi` (optional light metrics)
  - `GET /v1/rules/count` — how many rules are active
  - `GET /v1/blocklist` / `POST /v1/blocklist/add` (some demos post to Data Store instead; both patterns are supported for convenience)
  - `POST /v1/policy/block` — alternative way to add deny rules

- **Energy** *(simulated)*  
  Exposes a **mode** and **current watts**; used to demonstrate power caps/idle transitions. Endpoints:
  - `GET /v1/health`
  - `POST /v1/notify/config`
  - `POST /v1/mode` — `"active"` or `"standby"`
  - `GET /v1/power` — `{mode, power_watts}`

- **Update** *(simulated)*  
  Implements **check**, **apply**, and **rollback**, and records **last result**. Endpoints:
  - `GET /v1/health`
  - `POST /v1/notify/config`
  - `POST /v1/check`
  - `POST /v1/apply` — `{version}`
  - `POST /v1/rollback`
  - `GET /v1/status` — current `{available_version, applied_version, last_result, last_check}`

---

## Project Layout

```
Internet_Router_System/
├─ compose/
│  └─ docker-compose.yml
├─ services/
│  ├─ orchestration/   (main.py, models.py, Dockerfile)
│  ├─ datastore/       (main.py, models.py, Dockerfile)
│  ├─ connectivity/    (main.py, models.py, Dockerfile)
│  ├─ security/        (main.py, models.py, Dockerfile)
│  ├─ energy/          (main.py, models.py, Dockerfile)
│  └─ update/          (main.py, models.py, Dockerfile)
├─ scripts/
│  ├─ demo_all.sh
│  ├─ 01_block_tiktok.sh
│  ├─ 02_load_10_clients.sh
│  ├─ 03_energy_toggle.sh
│  ├─ 04_update_success_then_rollback.sh
│  ├─ 99_cleanup.sh
│  └─ lib.sh
├─ requirements.txt
└─ README.md   (this file)
```

---

## Prerequisites

- **Docker** and **Docker Compose**
- **bash** (macOS/Linux; zsh is fine)  
- **jq** *(optional)* for pretty JSON output

---

## Setup & Run

From repo root:

```bash
# 1) Build + start all services
cd compose
docker compose up -d --build
cd ..

# 2) Make scripts executable
chmod +x scripts/*.sh
```

**Health checks (optional)**

```bash
curl -s http://localhost:8000/v1/health  # orchestration
curl -s http://localhost:8001/v1/health  # data store
curl -s http://localhost:8002/v1/health  # security
curl -s http://localhost:8003/v1/health  # connectivity
curl -s http://localhost:8004/v1/health  # update
curl -s http://localhost:8005/v1/health  # energy
```

---

## Quick Demo

Run **everything** in sequence:

```bash
bash scripts/demo_all.sh
```

What it does:
1. **Blocklist** demo — add `tiktok.com` and verify exposure via APIs.
2. **Load clients** — simulate 10 active clients in Connectivity.
3. **Energy toggle** — active → standby → active; observe watts.
4. **Update** — check, apply a new version, then simulate rollback.

You’ll see **KPI snapshots** (throughput, latency, power, rules, clients) after each step.

**Individual demos**

```bash
bash scripts/01_block_tiktok.sh
bash scripts/02_load_10_clients.sh
bash scripts/03_energy_toggle.sh
bash scripts/04_update_success_then_rollback.sh
```

**Cleanup**

```bash
bash scripts/99_cleanup.sh
```

---

## How this maps to requirements

- **Auto update** → `update` service (`/v1/check`, `/v1/apply`, `/v1/rollback`), invoked/observed via orchestration KPI/status.  
- **Firewall & parental controls** → `security` service (`/v1/rules/count`, policy/blocklist endpoints).  
- **Guest & general Wi-Fi** → represented by `connectivity` (client load, throughput/latency KPIs).  
- **Energy caps** → `energy` (`/v1/mode`, `/v1/power`) to demonstrate power budget behavior.  
- **Simple setup & UI** → `ui` and **orchestration** provide “single writer” pattern to the config (`/v1/config/apply`) and a status API.  
- **Traceability** → Each function contains the responsibility stated in the original functional requirements; orchestration is the single point that records **config version** and enforces an order of operations.

---

## Testing & Verification (sample)

- **Policy enforcement**: Add domains via Data Store or Security blocklist endpoint; retrieve `/v1/rules/count` and `/v1/blocklist` to confirm rules are loaded.  
- **Performance scenario**: `02_load_10_clients.sh` sets a **client load**; check `/v1/kpi` on Orchestration and Connectivity for **throughput/latency/active_clients**.  
- **Energy target**: Toggle modes and read `/v1/power`; ensure it reflects “active/standby” watts.  
- **Update safety**: Run `04_update_success_then_rollback.sh`; observe `/v1/status` transitions: `available_version`, `applied_version`, and `last_result`.  
- **End-to-end control**: Apply a config version at `/v1/config/apply` and confirm functions acknowledge via healthy KPIs and notify endpoints.

---

## Extending the demo

- **Persist Data Store** (bind a volume or add a lightweight DB).  
- **Richer KPIs** (packet counters, per-client stats).  
- **Config diff & rollback** (store multiple versions; add `/v1/config/{version}`).  
- **UI dashboard** that calls Orchestration `/v1/kpi` and each service’s health.  
- **Formal tests** (pytest) that exercise each script scenario and assert KPIs.

---

## Troubleshooting

- **“Error loading ASGI app. Could not import module …”**  
  Ensure each service’s Dockerfile runs `uvicorn services.<service>.main:app` and **PYTHONPATH** includes `/app`. The compose file already sets:
  ```
  command: uvicorn services.<name>.main:app --host 0.0.0.0 --port 8000
  environment: [ PYTHONUNBUFFERED=1, PYTHONPATH=/app ]
  ```
- **Copy step can’t find `requirements.txt`**  
  The Dockerfiles expect `requirements.txt` at repo root (copied from build context). Keep it there.  
- **Port conflicts**  
  Default host ports are 8000–8005 and 3000. Adjust `ports:` in `compose/docker-compose.yml` if needed.  
- **Service up but endpoint 404**  
  Use `curl -s http://localhost:<port>/openapi.json | jq '.paths | keys'` to see exactly which paths a service exposes.

