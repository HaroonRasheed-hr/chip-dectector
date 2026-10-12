# Chip Detector

Chip Detector is a web application for analyzing images with object detection.
Upload an image or choose an example to view the resulting image with detected
instances marked. The project includes a Next.js interface and a Django
backend that provides the detection API.

## Purpose

The purpose of Chip Detector is to support visual inspection of chip images by
making image-based detection results easy to run and review. The backend also
provides user accounts, detection calibration, system monitoring, and optional
MQTT messaging.

## Requirements

- Python 3.10 or later
- Node.js and npm

The project uses SQLite by default. An MQTT broker is only needed if you want
to use the MQTT features.

## Run the project on Windows

Open PowerShell in the project folder and run:

```powershell
python -m venv backend\venv
.\backend\venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Open `backend\.env` and replace the sample `SECRET_KEY` value with a private
key. Keep the real `.env` file private.

Start the application from the project folder:

```powershell
python run.py
```

The first run builds the frontend. The launcher then applies database
migrations, collects static files, and starts the Django server. Open
http://127.0.0.1:8000/ in a browser to use the application.

To run without rebuilding the frontend after it has already been built:

```powershell
python run.py --no-build
```

## Main pages and API

- `/` - application home
- `/login/` and `/register/` - user account pages
- `/detection/` - upload an image and review detection results
- `/api/inference/infer/` - image detection endpoint
- `/api/monitoring/metrics/` - system monitoring data
