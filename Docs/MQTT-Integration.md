# VisionPulse — MQTT Integration

How the backend talks to a Mosquitto broker: what it publishes, what it
subscribes to, how reconnection / queuing / logging works, and how to
test it end-to-end.

---

## Table of Contents

1. [Why MQTT](#1-why-mqtt)
2. [Components Overview](#2-components-overview)
3. [Configuration](#3-configuration)
4. [Lifecycle — Boot, Run, Shutdown](#4-lifecycle--boot-run-shutdown)
5. [Topic Map](#5-topic-map)
6. [Publishers](#6-publishers)
7. [Subscribers (Inbound Commands)](#7-subscribers-inbound-commands)
8. [Connection, Reconnect, and Offline Queue](#8-connection-reconnect-and-offline-queue)
9. [Logging — `logs/mqtt.log` and `logs/mqtt-result.log`](#9-logging--logsmqttlog-and-logsmqtt-resultlog)
10. [Running a Local Broker](#10-running-a-local-broker)
11. [Testing — sub / pub from the CLI](#11-testing--sub--pub-from-the-cli)
12. [How to Add a New Publisher / Subscriber](#12-how-to-add-a-new-publisher--subscriber)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Why MQTT

VisionPulse is split between a real-time inference / monitoring loop and
downstream consumers (dashboards, fleet management, alerting). MQTT
gives us:

- **Loose coupling** — the backend doesn't know or care which clients
  are listening. Anyone can `mosquitto_sub` and watch the bus.
- **Low-latency fan-out** — inference results and system telemetry
  reach every subscriber within a few milliseconds.
- **Durable QoS** — `QoS=1` (at-least-once) with broker-side persistence
  for retained messages.
- **Offline resilience** — when the broker is down, publishes are
  queued in-process and replayed on reconnect, so the production line
  never loses an event.

The integration follows specs **A.4.2** (full-stack MQTT) and
**B.5.1 / B.5.3** (AI-pipeline command + alert topics).

---

## 2. Components Overview

```
backend/
├── core/
│   └── mqtt/
│       ├── mqtt_client.py          ← singleton wrapper around paho.Client
│       ├── mqtt_connection.py      ← public start/stop/publish helpers
│       ├── queue_manager.py        ← in-memory queue (offline buffering)
│       ├── reconnect_handler.py    ← exponential-backoff delay
│       └── topics.py               ← topic constants (single source of truth)
├── apps/
│   └── mqtt_manager/
│       ├── apps.py                 ← Django AppConfig.ready() → start client
│       ├── services.py             ← start_mqtt_subsystem / stop_mqtt_subsystem
│       ├── publishers/
│       │   ├── status_publisher.py    → visionpulse/system/status
│       │   ├── monitor_publisher.py   → visionpulse/system/monitor
│       │   ├── result_publisher.py    → inference results (alias)
│       │   └── alert_publisher.py     → ic_inspection/.../alert
│       └── subscribers/
│           └── command_subscriber.py  ← ic_inspection/command/<station>
└── core/
    └── logging_system/
        ├── mqtt_logger.py           ← visionpulse.mqtt logger → logs/mqtt.log
        └── mqtt_result_logger.py    ← visionpulse.mqtt.result → logs/mqtt-result.log
```

The dependency direction is **always inward**: app-level publishers and
subscribers call into `core.mqtt.mqtt_connection`. Nothing else imports
`paho.mqtt.client` directly.

---

## 3. Configuration

All MQTT settings live in [`backend/.env`](../backend/.env), loaded by
`base.py` into the `MQTT` dict:

```dotenv
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
```

| Key | Purpose | Default |
| --- | --- | --- |
| `MQTT_ENABLED` | Master switch — when `False`, all publish/subscribe calls become no-ops. Useful for unit tests and offline development. | `False` |
| `MQTT_HOST` / `MQTT_PORT` | Broker address. | `localhost:1883` |
| `MQTT_USERNAME` / `MQTT_PASSWORD` | Optional Mosquitto credentials. | _empty_ |
| `MQTT_CLIENT_ID` | Must be **unique per broker connection**. Two clients with the same ID will kick each other off → endless reconnect loop. | `visionpulse-backend` |
| `MQTT_KEEPALIVE` | Seconds between PINGREQ heartbeats. | `60` |
| `MQTT_QOS` | Default QoS for publishes (0/1/2). | `1` |
| `MQTT_RECONNECT_MIN_DELAY` / `MQTT_RECONNECT_MAX_DELAY` | Bounds for the doubling backoff. | `1` / `60` |

The values are surfaced as `settings.MQTT` (see
[`backend/config/settings/base.py:177-188`](../backend/config/settings/base.py#L177-L188))
and consumed by `MQTTClient.__init__`.

---

## 4. Lifecycle — Boot, Run, Shutdown

### Startup sequence

```
manage.py runserver / gunicorn boots Django
        │
        ▼
django.apps.AppConfig.ready()  ──►  apps.mqtt_manager.apps.MqttManagerConfig.ready()
        │
        ▼
apps.mqtt_manager.services.start_mqtt_subsystem()
        ├── start_mqtt()                        (core/mqtt/mqtt_connection.py)
        │       └── MQTTClient.start()
        │             ├── construct paho.Client
        │             ├── attach on_connect / on_disconnect / on_message
        │             └── spawn 'mqtt-reconnect' daemon thread
        │
        ├── subscribe_to_commands()             (apps/.../command_subscriber.py)
        │       ├── client.set_command_handler(_handle_command)
        │       └── client.subscribe(ic_inspection/command/<station>)
        │
        └── publish_status('startup')           (status_publisher.py)
                  → visionpulse/system/status
```

Once `ready()` returns, the WSGI server starts accepting HTTP requests.
The MQTT client runs in a background thread, completely independent of
the Django request/response cycle.

### Recurring publishes

- **System telemetry** — [`core.monitoring.scheduler`](../backend/core/monitoring/) runs every
  `MONITORING_INTERVAL_SECONDS` (default 5) and publishes a snapshot to
  `visionpulse/system/monitor`.
- **Inference results** — every successful inference run calls
  `apps.inference.services.mqtt_service.publish_inference()` which
  fans out to four topics (see [§6](#6-publishers)).

### Shutdown

`stop_mqtt_subsystem()` publishes `visionpulse/system/status` with
`event=shutdown` and then calls `MQTTClient.stop()`, which:

1. Sets the stop event so the reconnect thread exits.
2. Calls `paho.Client.loop_stop()` and `disconnect()`.
3. Clears the singleton's client reference.

---

## 5. Topic Map

Single source of truth: [`backend/core/mqtt/topics.py`](../backend/core/mqtt/topics.py).

### Full-stack topics (spec A.4.2)

| Topic | Direction | Purpose |
| --- | --- | --- |
| `visionpulse/inference/results` | publish | Every inference run's full result payload (image, defect %, confidence, timing). |
| `visionpulse/system/errors` | publish | Cross-domain error events emitted by the General Error Node System. |
| `visionpulse/system/monitor` | publish | CPU/RAM/GPU telemetry snapshots, every 5 s. |
| `visionpulse/system/status` | publish | Lifecycle events (`startup`, `shutdown`, heartbeats). |

### AI-pipeline topics (spec B.5.1) — parameterised by line + station

| Helper | Pattern | Direction |
| --- | --- | --- |
| `ic_inspection_result(line, station)` | `ic_inspection/{line_id}/{station_id}/result` | publish |
| `ic_inspection_defect_area(line, station)` | `ic_inspection/{line_id}/{station_id}/defect_area` | publish |
| `ic_inspection_status(line, station)` | `ic_inspection/{line_id}/{station_id}/status` | publish |
| `ic_inspection_alert(line, station)` | `ic_inspection/{line_id}/{station_id}/alert` | publish |
| `ic_inspection_command(station)` | `ic_inspection/command/{station_id}` | **subscribe** |

> **Rule:** never hard-code a topic string. Always import the constant or
> the helper from `core.mqtt.topics` so renames stay safe.

---

## 6. Publishers

Every publisher is a thin function that builds a JSON payload and hands
it to `publish_json()` from `core.mqtt.mqtt_connection`. The client
serialises with `json.dumps(payload, separators=(',', ':'))` and routes
it according to broker reachability.

### `status_publisher.publish_status(event, **details)`

```python
publish_json(SYSTEM_STATUS, {
    'timestamp': utc_iso_timestamp(),
    'event': event,           # 'startup' | 'shutdown' | 'heartbeat' | …
    **details,
})
```

Used at boot/shutdown, can also be called for ad-hoc heartbeats.

### `monitor_publisher.publish_now()` & the scheduler

`collect_snapshot()` from `core.monitoring.telemetry` produces a dict of
CPU %, RAM, GPU util/mem (`pynvml`), disk, and timestamps. The scheduler
publishes one every `MONITORING_INTERVAL_SECONDS`.

### `alert_publisher.publish_alert(line, station, severity, **details)`

Triggered by `apps.inference.services.threshold_service` when a defect
percentage crosses a configured threshold (spec B.5.3). Payload:

```json
{
  "timestamp": "2026-05-16T21:30:00Z",
  "line_id": "line-1",
  "station_id": "station-1",
  "severity": "critical",
  "defect_percentage": 17.4,
  "threshold": 10.0
}
```

### `apps.inference.services.mqtt_service.publish_inference(req, resp)`

Called from the inference bridge after every run. Publishes:

1. `visionpulse/inference/results` — full payload (always).
2. `ic_inspection/<line>/<station>/result` — same payload, **only if a
   chip bbox was detected** (spec B.3 — no chip ⇒ invalid result).
3. `ic_inspection/<line>/<station>/defect_area` — defect area + %.
4. _(via alert_publisher)_ `ic_inspection/<line>/<station>/alert` if the
   defect % breaches the threshold.

### `result_publisher` (alias)

[`apps/mqtt_manager/publishers/result_publisher.py`](../backend/apps/mqtt_manager/publishers/result_publisher.py)
re-exports `publish_inference` under the spec-mandated path so external
callers referencing
`mqtt_manager.publishers.result_publisher.publish_result` resolve.

---

## 7. Subscribers (Inbound Commands)

Defined in
[`apps/mqtt_manager/subscribers/command_subscriber.py`](../backend/apps/mqtt_manager/subscribers/command_subscriber.py).

**Topic:** `ic_inspection/command/{station_id}` where `station_id`
defaults to `INFERENCE_DEFAULT_STATION_ID` (`station-1`).

**Supported payloads** (JSON):

| Payload | Effect |
| --- | --- |
| `{"action": "start"}` | Logged; intended to resume the inference pipeline. |
| `{"action": "stop"}` | Logged; intended to pause the inference pipeline. |
| `{"action": "set_threshold", "value": 0.6}` | Logged; intended to update the live confidence threshold. |
| anything else | Routed to `mqtt_error_handler.report(...)` and ends up in `logs/mqtt.log` + `logs/errors.log`. |

The subscription is wired in
`apps.mqtt_manager.services.start_mqtt_subsystem()` during Django's
`AppConfig.ready()`, so it survives the entire process lifetime. The
actual command effects (start/stop/threshold) currently log only; wire
them into the inference scheduler when product requirements firm up.

### Message flow

```
paho.Client (background loop) ─── msg ──► MQTTClient._on_message()
        │
        └─► self._command_handler(topic, payload)
                  │
                  └─► _handle_command(topic, payload)
                          │
                          ├─ json.loads(payload)
                          ├─ dispatch on `action`
                          └─ log_runtime('Command received: …')
```

---

## 8. Connection, Reconnect, and Offline Queue

Implemented in [`core/mqtt/mqtt_client.py`](../backend/core/mqtt/mqtt_client.py).

### Connection

`MQTTClient._connect_loop` runs in a daemon thread. It calls
`paho.Client.connect()`, then `loop_start()` (which spawns paho's own
network thread). Once connected, paho handles **all subsequent
reconnects** internally — the daemon thread only re-engages if the
**initial** connect fails.

### Backoff

[`core/mqtt/reconnect_handler.py`](../backend/core/mqtt/reconnect_handler.py)
provides `ExponentialBackoff`: starts at `RECONNECT_MIN_DELAY` (1 s),
doubles on every failure, capped at `RECONNECT_MAX_DELAY` (60 s),
reset on a successful connect.

### Offline queue

[`core/mqtt/queue_manager.py`](../backend/core/mqtt/queue_manager.py) —
thread-safe bounded deque (max 1000 messages). When `publish_json()` is
called and we're disconnected, the message is enqueued and logged as a
warning. On reconnect, `MQTTClient._drain_queue()` republishes
everything in order. If a publish fails again mid-drain, the message is
put back and draining halts until the next reconnect.

```
caller ──► publish_json(topic, payload)
              │
              ▼
       connected? ── no ─► queue.enqueue(msg)   (warning logged)
              │
              yes
              │
              ▼
       paho.publish() ── rc != 0 ─► queue.enqueue(msg)   (error logged)
```

### QoS

`QoS=1` (at-least-once) by default. Combined with the offline queue,
that gives **at-least-once delivery across broker outages**, at the cost
of allowing duplicates if the network blips during PUBACK. Consumers
should be idempotent (most are — they store by timestamp + station).

---

## 9. Logging — `logs/mqtt.log` and `logs/mqtt-result.log`

MQTT activity is split across **two complementary log files**, each
written by a dedicated named logger. Both files are appended in
real-time (each `logging.FileHandler` flushes per record), so external
`tail -f` / log shippers see new entries within milliseconds of the
event being emitted.

| File | Logger | Format | Purpose |
| --- | --- | --- | --- |
| `logs/mqtt.log` | `visionpulse.mqtt` | human-readable (`{levelname} {asctime} {name} {message}`) | Narrative MQTT history — lifecycle, queue, errors. Easy to skim by eye. |
| `logs/mqtt-result.log` | `visionpulse.mqtt.result` | **line-delimited JSON** | Structured per-event audit feed — every publish, receive, connection state change. Designed for `jq`, dashboards, or a log shipper. |

### 9.1 Narrative log — `logs/mqtt.log`

Routed through
[`core.logging_system.mqtt_logger`](../backend/core/logging_system/mqtt_logger.py).
The `visionpulse.mqtt` logger is wired to four handlers:

| Handler | File | Captured levels |
| --- | --- | --- |
| `mqtt_file` | `logs/mqtt.log` | INFO + above (full MQTT history) |
| `warnings_file` | `logs/warnings.log` | WARNING + above (cross-domain) |
| `errors_file` | `logs/errors.log` | ERROR + above (unified error audit) |
| `console` | stdout | INFO + above (runserver visibility) |

So if you only care about MQTT narrative, `tail -f backend/logs/mqtt.log`.
If you want every error the system has ever raised — MQTT or otherwise —
`tail -f backend/logs/errors.log`.

**Sample lines**

```
INFO    2026-05-16 21:16:40 visionpulse.mqtt MQTT client starting (host=localhost port=1883)
INFO    2026-05-16 21:16:40 visionpulse.mqtt Subscribed to command topic: ic_inspection/command/station-1
WARNING 2026-05-16 21:16:40 visionpulse.mqtt MQTT not connected — queued message for visionpulse/system/status (queue=2)
INFO    2026-05-16 21:16:40 visionpulse.mqtt MQTT connected to broker
INFO    2026-05-16 21:16:40 visionpulse.mqtt Replayed 2 queued MQTT messages
ERROR   2026-05-16 21:30:11 visionpulse.mqtt MQTT publish failed rc=4 topic=visionpulse/inference/results
```

**Adding your own narrative log lines**

```python
from core.logging_system import mqtt_logger

mqtt_logger.info('publishing batch (%d items)', len(batch))
mqtt_logger.warning('payload truncated — image size %d KB', size_kb)
mqtt_logger.error('alert publish refused for %s/%s', line, station)
```

### 9.2 Structured result feed — `logs/mqtt-result.log`

Every publish, receive, and connection event also lands in
`logs/mqtt-result.log` as **one JSON object per line**. Each record
includes the topic, an ISO-8601 UTC timestamp (millisecond precision),
the payload, and event-specific status fields — everything needed for
ingest into Grafana / Loki / ELK without further parsing.

The file is written exclusively to (`propagate=False` on the logger),
so JSON records never leak into `mqtt.log` or `errors.log`.

**Common fields** (every record)

| Field | Type | Notes |
| --- | --- | --- |
| `timestamp` | string | UTC, ISO-8601, ms precision, trailing `Z`. |
| `event` | string | `publish` \| `receive` \| `connection` \| `error`. |
| `topic` | string | MQTT topic (omitted for connection events). |
| `payload` | any | Original Python object. Strings longer than 512 chars are summarised as `<truncated, N chars>` — keeps base64 images from blowing up the file. |

**Publish records** — `event: "publish"`

| Field | Values |
| --- | --- |
| `status` | `ok` (broker accepted) \| `queued` (broker unreachable, buffered for replay) \| `failed` (publish error). |
| `qos` | `0` / `1` / `2`. |
| `retain` | boolean. |
| `error` | present when `status=failed` — error string. |
| `queue_depth` | present when `status=queued` — current offline-buffer length. |

**Receive records** — `event: "receive"`

Inbound message from a subscribed topic. `payload` is the decoded body
(parsed as JSON when possible, else the raw string).

**Connection records** — `event: "connection"`

| `state` | When |
| --- | --- |
| `starting` | `MQTTClient.start()` invoked. |
| `connected` | `on_connect` fired with `reason_code=0`. |
| `disconnected` | `on_disconnect` fired. |
| `connect_failed` | Initial connect raised — daemon thread will retry. |
| `connect_refused` | Broker responded with a non-zero reason code (auth/ACL). |
| `subscribed` | `subscribe()` succeeded. |
| `stopped` | `MQTTClient.stop()` finished. |
| `disabled` | `MQTT_ENABLED=False` — client did not start. |

The `detail` object on each connection record carries host/port, topic
& qos (for `subscribed`), or the underlying exception text (for
`connect_failed`).

**Error records** — `event: "error"`

Failures that aren't tied to a specific publish — e.g. payload decode
errors on inbound commands, command-handler exceptions, subscribe
errors. Always has `error`; usually has `topic` and a `context` object.

**Sample lines** (formatted across multiple lines for readability — the
real file has one record per line)

```jsonc
{"event":"connection","state":"starting","detail":{"host":"localhost","port":1883,"client_id":"visionpulse-backend"},"timestamp":"2026-05-16T16:28:50.700Z"}
{"event":"connection","state":"connected","detail":{"host":"localhost","port":1883},"timestamp":"2026-05-16T16:28:50.754Z"}
{"event":"connection","state":"subscribed","detail":{"topic":"ic_inspection/command/station-1","qos":1},"timestamp":"2026-05-16T16:28:50.755Z"}
{"event":"publish","topic":"visionpulse/system/status","status":"ok","qos":1,"retain":false,"payload":{"timestamp":"2026-05-16T16:28:50Z","event":"startup"},"timestamp":"2026-05-16T16:28:50.756Z"}
{"event":"publish","topic":"visionpulse/system/monitor","status":"queued","qos":1,"retain":false,"payload":{"timestamp":"2026-05-16T16:28:51Z","cpu":{"percent":8.8,"count_logical":8,"count_physical":4}, "...":"..."},"queue_depth":1,"timestamp":"2026-05-16T16:28:51.620Z"}
{"event":"receive","topic":"ic_inspection/command/station-1","payload":{"action":"set_threshold","value":0.6},"timestamp":"2026-05-16T16:32:14.221Z"}
{"event":"publish","topic":"visionpulse/inference/results","status":"failed","qos":1,"retain":false,"payload":{"...":"..."},"error":"paho rc=4","timestamp":"2026-05-16T16:35:08.117Z"}
{"event":"error","topic":"ic_inspection/command/station-1","error":"command payload not JSON: ValueError('Expecting value: line 1 column 1 (char 0)')","context":{"raw_payload":"START NOW"},"timestamp":"2026-05-16T16:36:01.444Z"}
{"event":"connection","state":"stopped","timestamp":"2026-05-16T16:40:12.999Z"}
```

**Querying the feed with `jq`**

```bash
# Every publish that failed
jq -c 'select(.event=="publish" and .status=="failed")' backend/logs/mqtt-result.log

# Throughput per topic in the last 10 minutes
jq -r '.topic' backend/logs/mqtt-result.log | sort | uniq -c | sort -nr

# All inbound commands the backend received
jq -c 'select(.event=="receive")' backend/logs/mqtt-result.log

# Connection flaps (paired connect / disconnect inside the same minute)
jq -c 'select(.event=="connection") | {ts:.timestamp, s:.state}' backend/logs/mqtt-result.log
```

PowerShell equivalent (no `jq` install required):

```powershell
Get-Content backend\logs\mqtt-result.log |
    ForEach-Object { $_ | ConvertFrom-Json } |
    Where-Object { $_.event -eq 'publish' -and $_.status -eq 'failed' }
```

**Adding your own structured records**

```python
from core.logging_system import mqtt_result_logger

mqtt_result_logger.log_publish(
    'my/topic',
    {'hello': 'world'},
    'ok',
    qos=1,
    retain=False,
)
mqtt_result_logger.log_receive('my/topic', {'hello': 'world'})
mqtt_result_logger.log_connection('connected', host='localhost', port=1883)
mqtt_result_logger.log_error(
    'gateway timeout',
    topic='my/topic',
    upstream='broker-2.internal',
)
```

> **Payload truncation:** any string field longer than 512 chars is
> replaced with `<truncated, N chars>`. The original byte count is
> preserved so you can see *that* a big payload went out, just not
> *what* every byte of it was. Tune `_MAX_FIELD_LEN` in
> [`mqtt_result_logger.py`](../backend/core/logging_system/mqtt_result_logger.py)
> if you need the full body for debugging.

---

## 10. Running a Local Broker

VisionPulse expects a Mosquitto broker on `localhost:1883`. The simplest
setups:

### Windows — Mosquitto installer

```powershell
# 1. Install from https://mosquitto.org/download/ (default path C:\Program Files\mosquitto)
# 2. Start the service:
Start-Service mosquitto

# Or run inline (no service):
cd "C:\Program Files\mosquitto"
.\mosquitto.exe -v
```

### macOS / Linux — Homebrew / apt

```bash
brew install mosquitto                # macOS
sudo apt-get install -y mosquitto     # Debian/Ubuntu

mosquitto -v                          # foreground, verbose
```

### Docker

```bash
docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto:2
```

Authentication is **disabled by default** in Mosquitto 2.x — for local
development that's fine. For production, configure
`/etc/mosquitto/mosquitto.conf` with `allow_anonymous false` and
`password_file`, then set `MQTT_USERNAME` / `MQTT_PASSWORD` in `.env`.

---

## 11. Testing — sub / pub from the CLI

### Watch everything VisionPulse publishes

```powershell
cd "C:\Program Files\mosquitto"
.\mosquitto_sub.exe -h localhost -t "visionpulse/#" -v
```

```bash
mosquitto_sub -h localhost -t 'visionpulse/#' -v
```

You should immediately see a `visionpulse/system/status` message
(`event: startup`) on backend boot, then `visionpulse/system/monitor`
snapshots every 5 s.

### Watch the AI-pipeline topics

```bash
mosquitto_sub -h localhost -t 'ic_inspection/#' -v
```

### Send a command to the backend

```bash
mosquitto_pub -h localhost \
    -t ic_inspection/command/station-1 \
    -m '{"action":"set_threshold","value":0.6}'
```

You should see in `logs/mqtt.log`:

```
INFO ... visionpulse.mqtt Command received: set_threshold=0.6 (topic=ic_inspection/command/station-1)
```

### Health-check from a Python shell

```python
from core.mqtt.mqtt_connection import get_mqtt_client, publish_json
get_mqtt_client().is_connected            # → True
publish_json('visionpulse/test', {'hello': 'world'})  # → True if connected
```

---

## 12. How to Add a New Publisher / Subscriber

### Adding a publisher

1. Add a topic constant or helper in
   [`core/mqtt/topics.py`](../backend/core/mqtt/topics.py).
2. Drop a new file in `apps/mqtt_manager/publishers/` exporting a
   single function that builds the payload and calls `publish_json`:

   ```python
   from core.mqtt.mqtt_connection import publish_json
   from core.mqtt.topics import MY_NEW_TOPIC
   from core.persistence.jsonl_writer import utc_iso_timestamp

   def publish_my_event(**details) -> None:
       publish_json(MY_NEW_TOPIC, {
           'timestamp': utc_iso_timestamp(),
           **details,
       })
   ```
3. Call it from wherever the domain event originates.

### Adding a subscriber

1. Add the topic helper in `topics.py`.
2. Create the handler in `apps/mqtt_manager/subscribers/`:

   ```python
   from core.mqtt.mqtt_client import get_mqtt_client
   from core.mqtt.topics import my_topic
   from core.logging_system import mqtt_logger

   def subscribe_to_my_events(arg: str) -> None:
       client = get_mqtt_client()
       if not client.enabled:
           return
       topic = my_topic(arg)
       client.set_command_handler(_handle)   # one handler per process
       client.subscribe(topic)
       mqtt_logger.info('Subscribed to %s', topic)

   def _handle(topic: str, payload: str) -> None:
       ...
   ```
3. Wire it into `apps.mqtt_manager.services.start_mqtt_subsystem()` so
   it runs on boot.

> **Caveat:** the current `MQTTClient` only supports **one** command
> handler at a time (`set_command_handler`). If you need a router across
> multiple inbound topics, extend `_on_message` to dispatch by topic.

---

## 13. Troubleshooting

| Symptom | Likely cause / Fix |
| --- | --- |
| Backend logs `MQTT disabled — client not started`. | `MQTT_ENABLED=False` in `.env`. Flip it to `True` and restart. |
| Backend logs `MQTT not connected — queued message for …` forever. | No broker reachable at `MQTT_HOST:MQTT_PORT`. Start Mosquitto or fix the host/port. |
| Logs flap `MQTT connected` → `MQTT disconnected` every ~1 s. | **Duplicate `CLIENT_ID`** — two processes (e.g. `runserver` autoreload + a stale instance, or two `manage.py` shells with `RUN_MAIN`) sharing the same `MQTT_CLIENT_ID`. Either set distinct IDs per process or stop the duplicate. |
| `MQTT connect refused reason_code=4 (bad username/password)`. | Broker has `allow_anonymous false`; set `MQTT_USERNAME` / `MQTT_PASSWORD`. |
| `MQTT publish failed rc=4`. | Disconnected mid-publish — message has been re-queued automatically; will replay on reconnect. |
| Subscriber doesn't fire. | Confirm the topic matches **exactly** (case-sensitive). Run `mosquitto_sub -t 'ic_inspection/#' -v` to verify the broker is forwarding messages. Check `MQTTClient.set_command_handler` was called — only the **last** registration wins. |
| `mqtt.log` is empty. | Either `MQTT_ENABLED=False`, or you're tailing the wrong logs directory. The active path is `backend/logs/mqtt.log`. |
| `mqtt-result.log` is empty. | Same root causes as above. Also confirm `visionpulse.mqtt.result` is listed under `LOGGING['loggers']` in [`base.py`](../backend/config/settings/base.py); if the logger isn't declared, Python silently drops the records. |
| Payload field shows `<truncated, N chars>`. | By design — strings over 512 chars are summarised to keep base64 images out of the log. Edit `_MAX_FIELD_LEN` in [`mqtt_result_logger.py`](../backend/core/logging_system/mqtt_result_logger.py) if you need the full body. |

---

## File reference

| Path | Role |
| --- | --- |
| [`backend/core/mqtt/mqtt_client.py`](../backend/core/mqtt/mqtt_client.py) | Singleton client (connect, publish, subscribe, queue drain). |
| [`backend/core/mqtt/mqtt_connection.py`](../backend/core/mqtt/mqtt_connection.py) | Public `start_mqtt` / `stop_mqtt` / `publish_json` helpers. |
| [`backend/core/mqtt/queue_manager.py`](../backend/core/mqtt/queue_manager.py) | Thread-safe offline-message FIFO. |
| [`backend/core/mqtt/reconnect_handler.py`](../backend/core/mqtt/reconnect_handler.py) | Exponential-backoff helper. |
| [`backend/core/mqtt/topics.py`](../backend/core/mqtt/topics.py) | Topic constants + helpers. |
| [`backend/apps/mqtt_manager/apps.py`](../backend/apps/mqtt_manager/apps.py) | `AppConfig.ready()` boots the subsystem. |
| [`backend/apps/mqtt_manager/services.py`](../backend/apps/mqtt_manager/services.py) | `start_mqtt_subsystem` / `stop_mqtt_subsystem`. |
| [`backend/apps/mqtt_manager/publishers/*.py`](../backend/apps/mqtt_manager/publishers/) | One publisher per spec topic. |
| [`backend/apps/mqtt_manager/subscribers/command_subscriber.py`](../backend/apps/mqtt_manager/subscribers/command_subscriber.py) | Inbound command router. |
| [`backend/core/logging_system/mqtt_logger.py`](../backend/core/logging_system/mqtt_logger.py) | Narrative MQTT log helpers (`info` / `warning` / `error`) → `mqtt.log`. |
| [`backend/core/logging_system/mqtt_result_logger.py`](../backend/core/logging_system/mqtt_result_logger.py) | Structured JSON event helpers (`log_publish` / `log_receive` / `log_connection` / `log_error`) → `mqtt-result.log`. |
| [`backend/config/settings/base.py`](../backend/config/settings/base.py) | `MQTT` dict + `LOGGING` (handler + logger). |
| [`backend/.env`](../backend/.env) | Per-environment MQTT credentials and tuning. |
