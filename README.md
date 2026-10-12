# Chip Detector

Chip Detector is a web application for uploading chip images and reviewing
object-detection results. It combines a Next.js frontend with a Django REST
backend. In the standard setup, Django serves both the frontend and the API
from one local server.

## Purpose

The project provides a place to inspect chip images, view marked detection
results, and record measurements such as detected defect area and percentage.
It also includes account management, a system metrics endpoint, and optional
MQTT messaging for connecting results and monitoring data to other systems.

## What the application does

- Displays a web interface with login, registration, and image detection pages.
- Accepts an image upload or a built-in example image for processing.
- Sends image files to the Django inference endpoint and displays the returned
  output image.
- Returns detection details such as class, confidence, bounding box, chip and
  defect status, estimated defect area, and inference duration.
- Records inference measurements in a JSONL file and mirrors run summaries to
  the Django database.
- Exposes a system metrics endpoint for CPU, memory, disk, GPU, and uptime
  information. GPU data availability depends on the host and its installed
  support libraries.
- Provides optional MQTT publishing and command subscription when an MQTT
  broker is configured.
- Includes backend modules for user accounts, calibration services, monitoring,
  inference, MQTT, and WebSocket support.

### Current detection behavior

The default provider is `stub`. It returns a sample chip box and defect box and
draws a red overlay so the upload-to-result flow can be tried without a model.
This is demonstration output and does not analyze the actual image contents.
The RF-DETR and TensorRT providers are placeholders and are not implemented.

The detection page displays model names, but its current request does not send
the selected name to the backend. Provider routing is controlled by the
backend's `INFERENCE_DEFAULT_PROVIDER` setting.

## Project layout

```text
backend/
  apps/
    users/          Registration, login, logout, token refresh, and user details
    inference/      Image endpoint, provider bridge, result processing, storage
    monitoring/     Host metrics endpoint and telemetry support
    calibration/    Calibration services and view code
    mqtt_manager/   MQTT publishers and command subscriber
    websocket/      WebSocket consumer and routing support
  config/           Django settings, URL configuration, WSGI and ASGI entry points
  core/              Shared middleware, logging, MQTT, monitoring, and frontend views
  scripts/           Frontend build helper
  requirements.txt   Python dependencies
  .env.example       Backend environment variable template
  manage.py          Django management command
frontend/
  src/app/           Next.js pages and detection flow
  src/components/    Page layout, forms, and detection components
  package.json       Frontend dependencies and commands
run.py               Builds the frontend and starts the Django server
```

Calibration and WebSocket modules are present in the source tree. Their
endpoints are not currently included in the main Django URL configuration.

## Requirements

- Python 3.10 or later
- Node.js and npm

The development database is SQLite and is created locally by Django. MQTT is
optional and requires a reachable broker if enabled.

## Setup and run on Windows

Open PowerShell in the project folder and create the Python environment:

```powershell
python -m venv backend\venv
.\backend\venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Edit `backend\.env` and replace the sample `SECRET_KEY` value with a private
key. Django reads this file when it starts. Do not share or commit your real
`.env` file.

Start the application from the project folder:

```powershell
python run.py
```

The launcher builds the Next.js static export, applies Django database
migrations, collects static files, and starts the Django development server.
The frontend and API are then available at:

- Application: `http://127.0.0.1:8000/`
- Django admin: `http://127.0.0.1:8000/admin/`
- API base: `http://127.0.0.1:8000/api/`

The frontend build helper installs npm dependencies when needed. For a
subsequent start where the existing frontend build should be reused, run:

```powershell
python run.py --no-build
```

This option requires an existing frontend build in `frontend\out`.

### Run frontend and backend separately

For frontend development, start Django in one PowerShell window:

```powershell
.\backend\venv\Scripts\Activate.ps1
Set-Location backend
python manage.py migrate
python manage.py runserver
```

In a second window, configure the frontend to call that backend and start
Next.js:

```powershell
Set-Location frontend
npm install
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000"
npm run dev
```

Open `http://localhost:3000/`. `NEXT_PUBLIC_API_URL` should be the backend
origin, without an `/api` suffix. The Django CORS and CSRF settings include
localhost development origins by default.

### Launcher options

```powershell
python run.py --host 127.0.0.1 --port 8000
python run.py --no-build
python run.py --no-migrate
python run.py --no-collectstatic
```

`--host` and `--port` change the address used by the server. The remaining
flags skip the named startup step. `python run.py --prod` selects production
settings and Gunicorn; it requires Gunicorn and an HTTPS-terminating reverse
proxy because production settings enforce secure connections.

## Configuration

The backend loads settings from `backend\.env`. The supplied
`backend\.env.example` contains the main development settings.

| Setting | Purpose |
|---------|---------|
| `SECRET_KEY` | Required Django signing key. Set a private value. |
| `DEBUG` | Enables or disables Django debug behavior. |
| `ALLOWED_HOSTS` | Comma-separated allowed host names. |
| `DATABASE_URL` | Optional database URL. SQLite is used when not set. |
| `CORS_ALLOWED_ORIGINS` | Origins permitted to call the API from a browser. |
| `CSRF_TRUSTED_ORIGINS` | Browser origins trusted for CSRF-protected requests. |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Access token lifetime in minutes. |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Refresh token lifetime in days. |
| `REFRESH_COOKIE_SECURE` | Set to `True` when serving over HTTPS. |
| `INFERENCE_DEFAULT_PROVIDER` | Provider selected by default. The default is `stub`. |
| `INFERENCE_DEFAULT_CONFIDENCE_THRESHOLD` | Default confidence threshold for inference. |
| `INFERENCE_CHIP_PHYSICAL_AREA_MM2` | Reference chip area used for defect area estimation. |
| `MQTT_ENABLED` | Enables the MQTT subsystem when set to `True`. |
| `MQTT_HOST`, `MQTT_PORT` | MQTT broker address and port. |
| `MQTT_USERNAME`, `MQTT_PASSWORD` | Optional broker credentials. |

Additional MQTT reconnect, quality-of-service, and monitoring options are
defined in `backend\config\settings\base.py`. PostgreSQL requires enabling
`psycopg2-binary` in `backend\requirements.txt` and providing a PostgreSQL
`DATABASE_URL`.

## Pages and API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Application home page |
| GET | `/login/` | Login page |
| GET | `/register/` | Registration page |
| GET | `/detection/` | Image upload and result page |
| POST | `/api/auth/register/` | Create a user account |
| POST | `/api/auth/login/` | Sign in and receive access token and refresh cookie |
| POST | `/api/auth/logout/` | Sign out and clear the refresh cookie |
| POST | `/api/auth/token/refresh/` | Refresh the access token using the refresh cookie |
| GET | `/api/auth/me/` | Return the authenticated user's details |
| POST | `/api/inference/infer/` | Submit an image and receive detection output |
| GET | `/api/monitoring/metrics/` | Return a host metrics snapshot |

The inference endpoint accepts a multipart form upload with an `image` field.
Optional fields include `model`, `confidence_threshold`, `line_id`, and
`station_id`. Its JSON response contains provider and model names, elapsed
time, confidence scores, detection bounding boxes, chip and defect flags,
estimated defect measurements, and an output image data URL when available.

User accounts use JWT authentication. The refresh token is stored in an
HTTP-only cookie. The current inference and metrics endpoints allow requests
without authentication.

## Data and integrations

- SQLite stores user accounts and inference run summaries by default.
- Inference records are also written to `backend\core\persistence\measurements.jsonl`.
- Defect area is estimated by comparing detected defect bounding-box areas
  with the chip bounding-box area, scaled by the configured physical chip area.
- MQTT is disabled by default. When enabled and connected, the backend can
  publish inference, status, monitoring, and alert messages and listen for
  command messages.
- Monitoring reports a live snapshot through the metrics endpoint. MQTT
  monitoring publication can be enabled separately in settings.

## Tests

Run backend Django tests from the project folder:

```powershell
Set-Location backend
python manage.py test
```

Run frontend tests:

```powershell
Set-Location frontend
npm test
```

For frontend coverage, use `npm run test:coverage`.
