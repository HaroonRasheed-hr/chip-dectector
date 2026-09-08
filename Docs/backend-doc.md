# VisionPulse — Backend Documentation

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Architectural Approach](#architectural-approach)
5. [Bridge Architecture (AI Inference)](#bridge-architecture-ai-inference)
6. [Apps Layer](#apps-layer)
7. [Core Layer](#core-layer)
8. [MQTT Integration](#mqtt-integration)
9. [JSONL Persistence](#jsonl-persistence)
10. [System Monitoring](#system-monitoring)
11. [Error Node System](#error-node-system)
12. [Logging System](#logging-system)
13. [Authentication & Middleware](#authentication--middleware)
14. [API Endpoints](#api-endpoints)
15. [Database Models](#database-models)
16. [Settings & Environment](#settings--environment)
17. [Running the Backend](#running-the-backend)
18. [Testing](#testing)
19. [Engineering Standards](#engineering-standards)
20. [Future Extensions](#future-extensions)

---

## Overview

VisionPulse's backend is a **Django + Django REST Framework** service that exposes the inference and monitoring APIs consumed by the Next.js frontend. It is built to the Part A specification: GPU-accelerated inference orchestrated through a **Bridge Architecture**, with a **Mosquitto MQTT** event bus, **fault-tolerant JSONL persistence**, **psutil/pynvml telemetry**, a **General Error Node System**, and a four-file structured logger.

The backend is deliberately structured so the AI team can drop their RF-DETR / TensorRT engine into the bridge without anyone touching the views, the frontend, or the API contract.

---

## Technology Stack

| Technology | Version | Why It Was Chosen |
|---|---|---|
| **Python** | 3.12 | Type-hint maturity, dataclasses, and broad compatibility with NVIDIA tooling. |
| **Django** | 4.2 LTS | Mature ORM, admin, migrations, middleware, and AppConfig hooks. LTS = long support window. |
| **Django REST Framework** | 3.15 | Class-based views, serializers, multipart parsers — minimal boilerplate for typed JSON endpoints. |
| **SimpleJWT** | 5.3 | Stateless access tokens + rotating refresh tokens. Refresh stored in an httpOnly cookie. |
| **django-cors-headers** | 4.3 | CORS for the Next.js dev server on port 3000. |
| **django-environ** | 0.11 | Strict `.env` loading with type coercion (bool, int, float, list). |
| **paho-mqtt** | 2.1 | Reference Python MQTT client; speaks to the Mosquitto broker. Threaded loop with auto-reconnect. |
| **Mosquitto** | 2.x | Eclipse's MQTT broker — installed locally as a Windows service via `winget`. |
| **psutil** | 6.0 | CPU / memory / disk / boot-time telemetry (spec A.5). Cross-platform. |
| **nvidia-ml-py** (pynvml) | 12.560 | GPU utilization + VRAM via NVML. Gracefully degrades when no NVIDIA driver is present. |
| **Pillow** | 10.4 | Image decode + the red-defect overlay (spec B.4.1). |
| **SQLite** (dev) / **PostgreSQL** (prod) | — | SQLite for fast dev iteration; switch to Postgres by populating `DATABASE_URL` in `.env`. |

---

## Project Structure

```
backend/
├── manage.py                          # Django entrypoint (defaults to config.settings.development)
├── requirements.txt                   # Pinned dependencies
├── .env                               # Local environment (gitignored — copy from .env.example)
├── db.sqlite3                         # Dev database
│
├── config/                            # Django project package
│   ├── settings/
│   │   ├── base.py                    # Shared settings (apps, middleware, JWT, MQTT, MONITORING, LOGGING)
│   │   ├── development.py             # DEBUG=True overrides
│   │   └── production.py              # Production overrides
│   ├── urls.py                        # Root URL include (admin + /api/auth + /api/inference + /api/monitoring)
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/                              # Domain apps (each registered in INSTALLED_APPS)
│   ├── users/                         # JWT auth: register / login / refresh / me / logout
│   ├── inference/                     # Inference API + Bridge Architecture
│   │   ├── bridge/
│   │   │   ├── interfaces/ai_provider.py    # AIProvider ABC (abstraction side)
│   │   │   ├── providers/                   # Concrete engines (implementation side)
│   │   │   │   ├── future_provider.py       # StubProvider — exercises the flow without a model
│   │   │   │   ├── rf_detr_provider.py      # RF-DETR — filled in once AI team delivers .pt/.onnx
│   │   │   │   └── tensorrt_provider.py     # TRT FP16 — filled in once .trt engine lands
│   │   │   ├── services/
│   │   │   │   ├── inference_bridge.py      # The only entrypoint views may import
│   │   │   │   ├── provider_router.py       # Lazy-loading registry, picks provider by name
│   │   │   │   └── image_processor.py       # Pixel-area → mm² math (spec B.3)
│   │   │   └── dto/
│   │   │       ├── inference_request.py     # Engine-agnostic request DTO
│   │   │       └── inference_response.py    # Detection + InferenceResponse dataclasses
│   │   ├── services/
│   │   │   ├── inference_service.py         # Orchestrates: validate → bridge → DB + JSONL + MQTT
│   │   │   ├── threshold_service.py         # Confidence clamp + severity band (spec B.5.3)
│   │   │   ├── area_calculator.py           # Re-export of bridge image_processor for spec parity
│   │   │   ├── mask_generator.py            # Reusable red-overlay helper for real providers
│   │   │   ├── mqtt_service.py              # Publishes result / defect_area / alert topics
│   │   │   └── persistence_service.py       # Appends to measurements.jsonl
│   │   ├── utils/
│   │   │   ├── image_utils.py               # Reads bytes from UploadedFile without double-buffering
│   │   │   ├── validation.py                # Content-type + size guards on uploads
│   │   │   └── base64_encoder.py            # JPEG-base64 ↔ data: URL helpers
│   │   ├── models.py                        # InferenceRun (DB mirror of each inference call)
│   │   ├── serializers.py                   # InferenceRequest/Response serializers
│   │   ├── views.py                         # InferView (POST /api/inference/infer/)
│   │   ├── admin.py                         # Read-only admin listing of past runs
│   │   ├── urls.py
│   │   └── apps.py                          # AppConfig (label='inference')
│   ├── monitoring/                          # Telemetry endpoint
│   │   ├── services/                        # Per-metric collectors (legacy spec slot)
│   │   ├── views.py                         # MetricsView (GET /api/monitoring/metrics/)
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── apps.py                          # ready() starts the telemetry scheduler
│   ├── mqtt_manager/                        # MQTT lifecycle + publishers/subscribers
│   │   ├── publishers/
│   │   │   ├── status_publisher.py          # visionpulse/system/status (startup/shutdown)
│   │   │   ├── monitor_publisher.py         # Ad-hoc monitor publish (recurring loop lives in core/)
│   │   │   ├── result_publisher.py          # Alias → apps.inference.services.mqtt_service
│   │   │   └── alert_publisher.py           # ic_inspection/.../alert
│   │   ├── subscribers/
│   │   │   └── command_subscriber.py        # ic_inspection/command/{station} → start/stop/set_threshold
│   │   ├── services.py                      # start_mqtt_subsystem() / stop_mqtt_subsystem()
│   │   └── apps.py                          # ready() boots MQTT client + subscriber
│   ├── calibration/                         # Reserved — scaffold only
│   └── websocket/                           # Reserved — scaffold only (consumers/routing for later)
│
├── core/                                    # Cross-cutting infrastructure (no domain logic)
│   ├── middleware/
│   │   ├── request_logging_middleware.py    # Logs every request to runtime.log
│   │   ├── authentication_middleware.py     # Hoists access_token cookie → Authorization header
│   │   └── rate_limit_middleware.py         # Path-based limit using LocMemCache
│   ├── mqtt/
│   │   ├── mqtt_client.py                   # paho wrapper: reconnect, offline queue, command callback
│   │   ├── mqtt_connection.py               # start_mqtt() / stop_mqtt() / publish_json() facade
│   │   ├── queue_manager.py                 # Thread-safe FIFO of QueuedMessage
│   │   ├── reconnect_handler.py             # ExponentialBackoff (doubles, capped)
│   │   └── topics.py                        # Single source of truth for every spec topic
│   ├── monitoring/
│   │   ├── cpu_monitor.py
│   │   ├── memory_monitor.py
│   │   ├── disk_monitor.py
│   │   ├── gpu_monitor.py                   # pynvml — degrades cleanly without driver
│   │   ├── uptime_monitor.py
│   │   ├── telemetry.py                     # Aggregator → one snapshot dict
│   │   └── scheduler.py                     # Daemon thread; publishes every N seconds
│   ├── logging_system/
│   │   ├── logger_config.py                 # Named-logger accessors (runtime/errors/inference/warnings)
│   │   ├── runtime_logger.py
│   │   ├── error_logger.py
│   │   ├── inference_logger.py
│   │   └── warning_logger.py
│   ├── persistence/
│   │   ├── jsonl_writer.py                  # Append-only writer + ISO-8601 helper
│   │   ├── persistence_manager.py
│   │   └── measurements.jsonl               # Authoritative inference store (gitignored data)
│   └── errors/
│       ├── error_node_handler.py            # Central capture_error() — logs + MQTT publish
│       ├── backend_error_handler.py         # Per-domain thin wrappers (spec A.6.1)
│       ├── mqtt_error_handler.py
│       ├── gpu_error_handler.py
│       ├── inference_error_handler.py
│       ├── monitoring_error_handler.py
│       └── serialization_error_handler.py
│
├── logs/                                    # Output of the four-file logger
│   ├── runtime.log
│   ├── errors.log
│   ├── inference.log
│   └── warnings.log
│
├── media/                                   # Django MEDIA_ROOT (uploads)
├── static/                                  # Django STATIC_ROOT (collectstatic target)
└── tests/                                   # Reserved for cross-app integration suites
    ├── unit/
    ├── integration/
    └── performance/
```

---

## Architectural Approach

The backend is split into two top-level packages by intent:

| Package | Purpose | What lives here |
|---|---|---|
| **`apps/`** | Domain logic — anything tied to a Django app (models, URLs, views). | `users`, `inference`, `monitoring`, `mqtt_manager`, etc. Each app has its own `models.py`, `urls.py`, `apps.py`. |
| **`core/`** | Cross-cutting infrastructure — no Django app boundary, no models. | MQTT client, telemetry collectors, JSONL writer, error node system, named loggers, middleware. |

**Why two packages?** It enforces a one-way dependency: `apps/` may import from `core/`, never the reverse. That keeps infrastructure (MQTT, logging, JSONL, metrics) reusable across apps and trivially mockable in tests.

### Layered request flow (inference example)

```
HTTP POST /api/inference/infer/
  │
  ▼
DRF View                        apps/inference/views.py
  │  – parses multipart
  │  – validates with InferenceRequestSerializer
  ▼
Application Service             apps/inference/services/inference_service.py
  │  – upload validation
  │  – builds InferenceRequest DTO
  │  – calls bridge (engine-agnostic)
  │  – persists side-effects: JSONL + DB + MQTT
  ▼
Bridge Facade                   apps/inference/bridge/services/inference_bridge.py
  │  – resolves provider via router
  │  – delegates inference
  │  – runs pixel→mm² annotation
  ▼
Provider                        apps/inference/bridge/providers/*.py
  │  – the ONLY place that knows about a specific model / runtime
  ▼
Response DTO  →  Serializer  →  JSON to frontend
```

The frontend never knows which provider ran. Swapping `StubProvider` for `RfDetrProvider` later is a single `.env` line change (`INFERENCE_DEFAULT_PROVIDER=rf_detr`); no view or serializer touches a model.

### Process lifecycle hooks

Two Django `AppConfig.ready()` hooks start long-lived background subsystems:

- **`apps.mqtt_manager.apps.MqttManagerConfig.ready`** → connects to Mosquitto, subscribes to commands, publishes `system/status:startup`.
- **`apps.monitoring.apps.MonitoringConfig.ready`** → spawns the telemetry daemon thread.

Both use singleton patterns so re-imports (e.g. Django autoreload) don't spawn duplicate threads / clients.

---

## Bridge Architecture (AI Inference)

> **Spec A.4.1 — Bridge Architecture is mandatory. Direct coupling between frontend and inference engine will be rejected in code review.**

The Bridge pattern decouples an **abstraction** (the interface the API layer programs against) from one or more **implementations** (concrete inference engines). In this codebase:

| Role | Class / Module | Path |
|---|---|---|
| **Abstraction** | `AIProvider` (ABC) | `apps/inference/bridge/interfaces/ai_provider.py` |
| **Implementations** | `StubProvider`, `RfDetrProvider`, `TensorRTProvider` | `apps/inference/bridge/providers/*.py` |
| **Refined Abstraction (facade)** | `run_inference()` | `apps/inference/bridge/services/inference_bridge.py` |
| **Selector** | `ProviderRouter` | `apps/inference/bridge/services/provider_router.py` |
| **Transport DTOs** | `InferenceRequest`, `InferenceResponse`, `Detection` | `apps/inference/bridge/dto/*.py` |

```
              ┌──────────────────────────────┐
              │  apps/inference/views.py     │
              │  (and only views.py)         │
              └─────────────┬────────────────┘
                            │ calls bridge facade
                            ▼
              ┌──────────────────────────────┐
              │  inference_bridge.run_*()    │   ← refined abstraction
              └─────────────┬────────────────┘
                            │ resolves
                            ▼
              ┌──────────────────────────────┐
              │  ProviderRouter              │   ← selector
              └─────────────┬────────────────┘
                            │ returns one of:
            ┌───────────────┼────────────────┬─────────────────────┐
            ▼               ▼                ▼                     ▼
       StubProvider   RfDetrProvider   TensorRTProvider   <future engines>
       (placeholder)  (PyTorch/ONNX)   (FP16 TRT engine)
```

**Rules enforced in the codebase:**

1. Views must call `inference_bridge.run_inference()` only — never import a provider directly.
2. Providers must implement `AIProvider.{load, is_ready, infer, shutdown}` and accept/return only the DTOs in `bridge/dto/`.
3. Provider selection is data-driven: the `model` field of the request, falling back to `settings.INFERENCE['DEFAULT_PROVIDER']`. Adding a new engine = one new file + one entry in `ProviderRouter._registry`.

**Why this matters:** the AI team can deliver `rf_detr_v1.pt` / `rf_detr_v1.trt` and swap providers without rebuilding the API, the frontend, or any consumer of `measurements.jsonl`.

---

## Apps Layer

### `apps.users` — Authentication

JWT auth with **access in memory, refresh in httpOnly cookie**:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/auth/register/` | POST | Create user (email + full_name + password) |
| `/api/auth/login/` | POST | Returns access token + sets `refresh_token` cookie |
| `/api/auth/token/refresh/` | POST | Reads cookie, rotates, returns new access |
| `/api/auth/logout/` | POST | Blacklists refresh + clears cookie |
| `/api/auth/me/` | GET | Returns current user profile |

Custom user model `apps.users.models.User` uses **email as `USERNAME_FIELD`**. `AUTH_USER_MODEL = 'users.User'` is set in `base.py`.

### `apps.inference` — Inference API

The Bridge-pattern layer is described in detail above. The visible surface is:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/inference/infer/` | POST (multipart) | Upload an image → masked image + defect mm²/% |

**Request fields** (`InferenceRequestSerializer`):
- `image` (file, required)
- `model` (string, optional — provider name, e.g. `stub` / `rf_detr` / `tensorrt`)
- `confidence_threshold` (float 0–1, optional)
- `line_id`, `station_id` (strings, optional)

**Response fields** (`InferenceResponseSerializer`): `model_name`, `provider_name`, `inference_time_ms`, `confidence_threshold`, `chip_detected`, `defect_detected`, `defect_area_mm2`, `defect_percentage`, `confidence_scores[]`, `detections[]`, `output_image` (`data:image/jpeg;base64,...`).

### `apps.monitoring` — Telemetry

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/monitoring/metrics/` | GET | Live point-in-time snapshot of CPU / RAM / disk / GPU / uptime |

The same snapshot is also pushed to `visionpulse/system/monitor` every N seconds (default 5) by the scheduler in `core/monitoring/scheduler.py`.

### `apps.mqtt_manager` — MQTT lifecycle

No HTTP endpoints. Its only job is to:
1. Boot the MQTT client at process startup (`AppConfig.ready`).
2. Subscribe to `ic_inspection/command/{station_id}` and route inbound commands to handlers.
3. Publish lifecycle events to `visionpulse/system/status`.
4. Provide named "publisher" helpers (`alert_publisher`, `monitor_publisher`, …) for callers that prefer named modules over the bare `publish_json()`.

### `apps.calibration`, `apps.websocket` — Reserved

Scaffold folders for future work (camera calibration endpoints, real-time WS push of inference results). No production code yet.

---

## Core Layer

### Why a separate `core/`?

Three rules:

1. **No Django app boundary.** Anything in `core/` works in management commands, Celery workers, ad-hoc scripts, and tests without `manage.py runserver` being involved.
2. **No domain logic.** Code in `core/` doesn't know what an "ic_chip" or "defect" is. It knows about bytes, sockets, threads, and JSON.
3. **One-way imports.** `apps/` → `core/` is allowed. `core/` → `apps/` is not.

### `core/mqtt`

See the [MQTT Integration](#mqtt-integration) section.

### `core/monitoring`

See the [System Monitoring](#system-monitoring) section.

### `core/logging_system`

See the [Logging System](#logging-system) section.

### `core/persistence`

See the [JSONL Persistence](#jsonl-persistence) section.

### `core/errors`

See the [Error Node System](#error-node-system) section.

### `core/middleware`

Three custom middlewares wired in `MIDDLEWARE`:

| Middleware | Job |
|---|---|
| `RequestLoggingMiddleware` | Logs `METHOD PATH status durationMs user= ip=` to `runtime.log` for every request. |
| `JWTAuthCookieMiddleware` | If no `Authorization` header is present, lifts `access_token` cookie into `Authorization: Bearer ...`. Lets SSR and tests authenticate without manually setting headers. |
| `RateLimitMiddleware` | Path-based limiter (configured per-path in `settings.RATE_LIMIT_PATHS`). Uses Django's cache backend (`LocMemCache` in dev). |

---

## MQTT Integration

> **Spec A.4.2** — Mosquitto broker, full topic hierarchy, auto-reconnect with exponential backoff, in-flight messages queued during disconnection, connection failures logged.

### Broker

Mosquitto 2.x runs as a Windows service installed via `winget install EclipseFoundation.Mosquitto`. Defaults: `localhost:1883`, no auth. Enable in production by setting `MQTT_USERNAME` / `MQTT_PASSWORD` in `.env` and switching `mosquitto.conf` to require auth.

### Topic hierarchy

Defined once in [`core/mqtt/topics.py`](backend/core/mqtt/topics.py):

| Topic | Direction | Purpose |
|---|---|---|
| `visionpulse/inference/results` | Out | Mirror of every inference run (spec A.4.2) |
| `visionpulse/system/errors` | Out | All errors captured by the Error Node System |
| `visionpulse/system/monitor` | Out | psutil/pynvml snapshot, every N seconds |
| `visionpulse/system/status` | Out | Lifecycle events: `startup`, `shutdown`, `heartbeat` |
| `ic_inspection/{line_id}/{station_id}/result` | Out | Per-station full result (spec B.5.1) |
| `ic_inspection/{line_id}/{station_id}/defect_area` | Out | Numeric defect mm² + % |
| `ic_inspection/{line_id}/{station_id}/status` | Out | Per-station pipeline state |
| `ic_inspection/{line_id}/{station_id}/alert` | Out | Fired when severity ≠ `none` (spec B.5.3) |
| `ic_inspection/command/{station_id}` | **In** | start / stop / set_threshold commands |

### Client design — `core/mqtt/mqtt_client.py`

A single `MQTTClient` singleton wraps `paho.mqtt.Client`. Lifecycle:

```
start()  →  _connect_loop (daemon thread)
                │
                ├── try client.connect()
                │      ├── success → on_connect → drain queue
                │      └── failure → ExponentialBackoff.next_delay() → retry
                │
                └── paho client.loop_start() owns the reader thread
```

Three guarantees the spec demands, each implemented as a discrete unit:

1. **Auto-reconnect with exponential backoff** — `core/mqtt/reconnect_handler.py::ExponentialBackoff` doubles delay (min 1s, cap 60s), resets on successful connect.
2. **Offline message queue** — `core/mqtt/queue_manager.py::MessageQueue` is a thread-safe bounded FIFO (1000 messages). `publish_json` enqueues when disconnected; `on_connect` drains in order.
3. **No silent failures** — every connect/publish/subscribe exception goes through the Error Node System (`core.errors.mqtt_error_handler`), which logs to `errors.log` *and* publishes to `visionpulse/system/errors`.

### Publish API

```python
from core.mqtt.mqtt_connection import publish_json
from core.mqtt.topics import INFERENCE_RESULTS

publish_json(INFERENCE_RESULTS, {'defect_percentage': 3.52, ...})
```

Returns `True` on direct success, `False` if queued or disabled. Callers never branch on connection state — the client handles it.

### Inbound commands

`apps.mqtt_manager.subscribers.command_subscriber` subscribes to `ic_inspection/command/{station_id}` and registers a single command-router callback with the client. Recognised actions (JSON body): `start`, `stop`, `set_threshold` (with `value`).

---

## JSONL Persistence

> **Spec A.4.3** — Append-only, one JSON per line, ISO 8601 UTC timestamp, fault-tolerant.

[`core/persistence/jsonl_writer.py`](backend/core/persistence/jsonl_writer.py) provides `append_jsonl(path, payload)`:

- Wraps every write in `try/except (OSError, TypeError, ValueError)`. Failures route to `errors.log`.
- Adds `timestamp` automatically (`utc_iso_timestamp()` → `'2026-05-15T16:15:26Z'`).
- Holds a module-level `threading.Lock()` so concurrent inference requests can't interleave bytes.
- Returns a `bool` so the caller can react to failure without exceptions propagating.

The authoritative file lives at [`core/persistence/measurements.jsonl`](backend/core/persistence/measurements.jsonl). Every inference call appends one line:

```jsonl
{"timestamp":"2026-05-15T16:15:26Z","model":"stub-v0","provider":"stub","line_id":"line-1","station_id":"station-1","confidence_threshold":0.5,"inference_time_ms":1.45,"chip_detected":true,"defect_detected":true,"defect_area_mm2":7.03,"defect_percentage":3.52,"confidence_scores":[0.99,0.91]}
```

The DB `InferenceRun` row is a *mirror* for the admin UI — the JSONL file is the source of truth for downstream analytics.

---

## System Monitoring

> **Spec A.5** — psutil + pynvml, configurable interval (default 5s), publish to `visionpulse/system/monitor`, display in UI.

### Collectors — `core/monitoring/`

| Module | Source API | Returned shape |
|---|---|---|
| `cpu_monitor` | `psutil.cpu_percent`, `cpu_count` | `{percent, count_logical, count_physical}` |
| `memory_monitor` | `psutil.virtual_memory()` | `{total, used, available, percent}` |
| `disk_monitor` | `psutil.disk_partitions`, `disk_usage`, `disk_io_counters` | `{partitions: [...], io: {...}}` |
| `gpu_monitor` | `pynvml.nvmlDeviceGet{UtilizationRates, MemoryInfo}` | `{available, devices: [...]}` |
| `uptime_monitor` | `psutil.boot_time()` | `{boot_time, uptime_seconds}` |

Each collector catches `Exception`, routes to `monitoring_error_handler.report(...)`, and returns a degraded-but-shaped dict so consumers don't crash. The GPU collector additionally guards against `pynvml.nvmlInit()` failure (no driver / no GPU).

### Aggregator — `core/monitoring/telemetry.py`

```python
def collect_snapshot() -> dict:
    return {
        'timestamp': utc_iso_timestamp(),
        'cpu': cpu_monitor.collect(),
        'memory': memory_monitor.collect(),
        'disk': disk_monitor.collect(),
        'gpu': gpu_monitor.collect(),
        'uptime': uptime_monitor.collect(),
    }
```

The same dict is returned by the `/api/monitoring/metrics/` endpoint *and* used as the MQTT payload — one source of truth, two transports.

### Scheduler — `core/monitoring/scheduler.py`

A `MonitoringScheduler` singleton runs in a daemon thread (`name='monitoring-scheduler'`). Wakes every `MONITORING_INTERVAL_SECONDS` (default 5), collects a snapshot, calls `publish_json(SYSTEM_MONITOR, snapshot)`. Started by `MonitoringConfig.ready()`.

---

## Error Node System

> **Spec A.6.1** — MANDATORY: Bilal's General Error Node System integrated across all critical paths. Every error captured, reported to MQTT, and logged locally.

### Central handler

[`core/errors/error_node_handler.py::capture_error()`](backend/core/errors/error_node_handler.py) is the single chokepoint:

```python
def capture_error(domain, message, *, exc=None, context=None, severity='error') -> ErrorEvent:
    # 1. Build a typed ErrorEvent dataclass (timestamp, domain, severity, context, traceback)
    # 2. Log to errors.log (with full traceback if exc was passed)
    # 3. Publish to visionpulse/system/errors via MQTT (lazy import to avoid cycles)
```

Failures inside step 3 are themselves caught and logged — the error-reporting path can never raise back into the caller.

### Domain wrappers

One file per spec domain, all five lines long, so call sites never need to remember the domain string:

```python
# core/errors/inference_error_handler.py
from core.errors.error_node_handler import capture_error
DOMAIN = 'AI Pipeline'

def report(message, *, exc=None, context=None):
    capture_error(DOMAIN, message, exc=exc, context=context)
```

Mapping (spec A.6.1 → file):

| Spec Domain | Module |
|---|---|
| Backend | `core/errors/backend_error_handler.py` |
| AI Pipeline | `core/errors/inference_error_handler.py` |
| MQTT | `core/errors/mqtt_error_handler.py` |
| GPU Execution | `core/errors/gpu_error_handler.py` (severity = `critical`) |
| Serialization | `core/errors/serialization_error_handler.py` |
| Monitoring Services | `core/errors/monitoring_error_handler.py` |

### Where it's wired

| Source of failure | Handler |
|---|---|
| MQTT connect / publish / subscribe | `mqtt_error_handler` |
| JSONL write | `error_logger.exception` (kept local to avoid MQTT recursion) |
| psutil / pynvml exceptions | `monitoring_error_handler` |
| Provider `load()` / `infer()` failures | `inference_error_handler` |
| Inference view top-level | `backend_error_handler` |
| MQTT command payload parse | `mqtt_error_handler` (serialization-flavoured) |

---

## Logging System

> **Spec A.6.2** — four log files plus `measurements.jsonl`.

Configured in [`config/settings/base.py`](backend/config/settings/base.py) under `LOGGING`:

| Logger name | File | When to write |
|---|---|---|
| `visionpulse.runtime` | `logs/runtime.log` | Lifecycle events, login, normal request flow |
| `visionpulse.errors` | `logs/errors.log` | Every captured error (level ≥ ERROR, with traceback) |
| `visionpulse.inference` | `logs/inference.log` | Provider load, inference timing, defect % |
| `visionpulse.warnings` | `logs/warnings.log` | MQTT disconnects, queue overflow, recoverable degradation |

[`core/logging_system/`](backend/core/logging_system/) provides thin convenience modules:

```python
from core.logging_system.runtime_logger import info as log_runtime
from core.logging_system.inference_logger import info as log_inference

log_runtime('MQTT connected to broker')
log_inference('Inference ok provider=%s time_ms=%.2f', name, ms)
```

All four loggers `propagate=False` so messages don't double-write through the root logger.

---

## Authentication & Middleware

### JWT flow

```
POST /api/auth/login/
  request body:  {email, password}
  response body: {access, user}
  response cookie: refresh_token   (httpOnly, SameSite=Lax, secure=False in dev)
```

The frontend keeps `access` in memory. Subsequent requests send `Authorization: Bearer <access>`. When `access` expires, the frontend hits `POST /api/auth/token/refresh/` — the middleware lifts the refresh cookie into the Authorization header, SimpleJWT rotates it (old refresh is blacklisted), and returns a new access. Logout blacklists the current refresh and clears the cookie.

### Middleware stack (in order)

```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.request_logging_middleware.RequestLoggingMiddleware',
    'core.middleware.authentication_middleware.JWTAuthCookieMiddleware',
    'core.middleware.rate_limit_middleware.RateLimitMiddleware',
]
```

### Rate limiting

Path-scoped via `RATE_LIMIT_PATHS` in `settings/base.py`:

```python
RATE_LIMIT_PATHS = {
    '/api/auth/login/':    {'limit': 5, 'window': 60},
    '/api/auth/register/': {'limit': 5, 'window': 60},
}
```

5 requests per IP per 60-second sliding window. Returns 429 with a JSON body. The cache backend is `LocMemCache` in dev — switch to Redis for multi-process production.

---

## API Endpoints

| Path | Method | Auth | Purpose |
|---|---|---|---|
| `/admin/` | GET | session (staff) | Django admin |
| `/api/auth/register/` | POST | none | Create user |
| `/api/auth/login/` | POST | none | Login, returns access + sets refresh cookie |
| `/api/auth/token/refresh/` | POST | cookie | Rotate refresh, return new access |
| `/api/auth/logout/` | POST | JWT | Blacklist refresh + clear cookie |
| `/api/auth/me/` | GET | JWT | Current user profile |
| `/api/inference/infer/` | POST (multipart) | AllowAny (dev) | Run inference, return masked image + defect metrics |
| `/api/monitoring/metrics/` | GET | AllowAny | Live telemetry snapshot |

Switch the inference + monitoring endpoints to `IsAuthenticated` for production by changing `permission_classes` in their views.

---

## Database Models

### `users.User` — Custom user

| Field | Type | Notes |
|---|---|---|
| `email` | `EmailField(unique=True)` | `USERNAME_FIELD` |
| `full_name` | `CharField(255)` | `REQUIRED_FIELDS = ['full_name']` |
| `is_active` / `is_staff` | `BooleanField` | Standard flags |
| `created_at` / `updated_at` | `DateTimeField` | Audit |

### `inference.InferenceRun` — Per-call mirror row

| Field | Type | Notes |
|---|---|---|
| `user` | `FK → User (nullable)` | Set when the call is authenticated |
| `model_name`, `provider_name` | `CharField` | Which engine ran |
| `line_id`, `station_id` | `CharField` | For multi-station deployments |
| `confidence_threshold` | `Float` | Threshold actually used (after clamp) |
| `inference_time_ms` | `Float` | End-to-end model time |
| `chip_detected`, `defect_detected` | `Bool` | Quick filters in admin |
| `defect_area_mm2`, `defect_percentage` | `Float` | Same numbers as the JSONL row |
| `created_at` | `DateTime` | Indexed for the admin's reverse-chrono list |

`measurements.jsonl` is the canonical store; `InferenceRun` exists so the Django admin lists past runs without parsing the JSONL file.

---

## Settings & Environment

### `config/settings/`

- **`base.py`** — everything shared. Reads `.env` at import time via `django-environ`.
- **`development.py`** — `DEBUG=True`, looser CORS, friendlier error pages.
- **`production.py`** — `DEBUG=False`, hardened cookie flags, expects `DATABASE_URL` to point at Postgres.

`manage.py` defaults to `config.settings.development`; set `DJANGO_SETTINGS_MODULE=config.settings.production` in production.

### `.env` keys

```ini
# Django
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3        # or postgres://user:pass@host:5432/db

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
REFRESH_COOKIE_SECURE=False              # True in production (HTTPS only)

# Django superuser bootstrap
DJANGO_SUPERUSER_EMAIL=...
DJANGO_SUPERUSER_PASSWORD=...
DJANGO_SUPERUSER_USERNAME=...

# MQTT (Mosquitto)
MQTT_ENABLED=True
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_CLIENT_ID=visionpulse-backend
MQTT_KEEPALIVE=60
MQTT_QOS=1
MQTT_RECONNECT_MIN_DELAY=1
MQTT_RECONNECT_MAX_DELAY=60

# Monitoring
MONITORING_ENABLED=True
MONITORING_INTERVAL_SECONDS=5
MONITORING_PUBLISH_TO_MQTT=True

# Inference
INFERENCE_DEFAULT_PROVIDER=stub          # stub | rf_detr | tensorrt
INFERENCE_DEFAULT_CONFIDENCE_THRESHOLD=0.5
INFERENCE_CHIP_PHYSICAL_AREA_MM2=200
INFERENCE_DEFAULT_LINE_ID=line-1
INFERENCE_DEFAULT_STATION_ID=station-1
```

---

## Running the Backend

### One-time setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env                   # fill in SECRET_KEY etc.
python manage.py migrate
python manage.py createsuperuser --no-input    # uses DJANGO_SUPERUSER_* from .env
```

### Mosquitto broker

```powershell
winget install EclipseFoundation.Mosquitto -e --accept-source-agreements --accept-package-agreements --silent
Start-Service mosquitto
```

The installer registers Mosquitto as a Windows service with `StartType=Automatic`, so it survives reboots. Verify:

```powershell
Test-NetConnection -ComputerName localhost -Port 1883
mosquitto_sub -h localhost -t 'visionpulse/#' -t 'ic_inspection/#' -v
```

### Run the API server

```powershell
python manage.py runserver
```

On startup you'll see:

```
INFO visionpulse.runtime Monitoring scheduler started (interval=5s, publish=True)
INFO visionpulse.runtime MQTT client starting (host=localhost port=1883)
INFO visionpulse.runtime Subscribed to command topic: ic_inspection/command/station-1
INFO visionpulse.runtime MQTT connected to broker
```

### Smoke-test inference

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/inference/infer/ `
  -F "image=@sample.jpg" `
  -F "model=stub"
```

Returns 200 with `output_image` as a `data:image/jpeg;base64,…` URL ready for `<img src>`.

### Smoke-test monitoring

```powershell
curl.exe http://127.0.0.1:8000/api/monitoring/metrics/
```

---

## Testing

### Running tests

```powershell
python manage.py test                          # all apps
python manage.py test apps.users               # one app
python manage.py test apps.users.tests.LoginTest
python manage.py test --keepdb                 # keep test DB between runs
python manage.py test -v 2                     # verbose
```

### Current coverage

- **`apps/users/tests.py`** — 31 tests for registration, login, refresh, logout, /me, JWT rotation.
- The other apps' `tests.py` files are empty placeholders to be filled in (a real suite for `apps.inference` is the highest-priority gap).

### Gotcha — rate-limit cache state across tests

The rate-limit middleware uses `LocMemCache`, which persists for the lifetime of the test process. `BaseAuthTest.setUp` therefore calls `cache.clear()` before each test, so login/register tests in one class don't poison the next class's bucket.

---

## Engineering Standards

> **Spec A.8** — modularity, typed interfaces, docstrings, linting, reliability, scalability.

| Standard | How it's enforced in this codebase |
|---|---|
| Modular architecture | Strict `apps/` vs `core/` split. Each concern (MQTT, monitoring, errors, persistence) is its own subpackage. |
| Typed public interfaces | Python type hints on every public function, dataclasses for DTOs (`InferenceRequest`, `InferenceResponse`, `Detection`, `ErrorEvent`, `QueuedMessage`). |
| Docstrings | One-line module docstring referencing the spec section; multi-line on non-trivial functions. |
| No unhandled exceptions in prod paths | Every external boundary (MQTT, NVML, psutil, disk I/O, model load) is wrapped and routed to the Error Node System. |
| Recovery for transient failures | MQTT auto-reconnect + offline queue; psutil/NVML collectors degrade to `None`; JSONL write returns `False` instead of raising. |
| Persistent logging | Four-file logger writes to disk; logs survive restarts. |
| Scalability | New provider = one file + one registry entry. New MQTT topic = one constant in `topics.py`. New telemetry metric = one new collector + one line in `telemetry.py`. |

---

## Future Extensions

| Work item | Where it slots in |
|---|---|
| **Replace `StubProvider` with real RF-DETR / TRT** | Drop model artifacts into `core/ai_engine/models/`, fill in `RfDetrProvider.load()` and `.infer()` (and the TRT equivalent). Flip `INFERENCE_DEFAULT_PROVIDER` in `.env`. |
| **WebSocket push of results** | `apps/websocket/` is scaffolded. Add a Channels `Consumer` and `routing.py`, broadcast each `InferenceResponse` from `inference_service.execute_inference`. |
| **Camera calibration endpoints** | `apps/calibration/` is scaffolded. Add models for calibration matrices, expose CRUD endpoints. |
| **Postgres + Redis** | Set `DATABASE_URL=postgres://...`, change `CACHES['default']['BACKEND']` to `django.core.cache.backends.redis.RedisCache`. Rate limiter and queue both benefit. |
| **Docker + GPU runtime** | The multi-stage `Dockerfile` (spec A.7.2) builds on `nvidia/cuda` base, copies the Python deps stage in, and exposes 8000. Compose adds `mqtt` service using `eclipse-mosquitto:2`. |
| **Authentication on inference** | Switch `InferView.permission_classes` to `(IsAuthenticated,)` and have the frontend send `Authorization: Bearer <access>`. |
