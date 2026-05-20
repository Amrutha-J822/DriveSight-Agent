# DriveSight Agent

DriveSight Agent is a beginner-friendly full-stack dashcam risk review app. Users upload a video, the FastAPI backend samples frames with OpenCV, optionally runs YOLO object detection, extracts structured driving risk events, asks an LLM-compatible service for a Driving Risk Brief, and stores reports plus reviewer feedback in SQLite. The React + TypeScript frontend shows upload status, WebSocket progress, report cards, an event timeline, and approve/dismiss/escalate feedback buttons.

## Project Structure

```text
DriveSight Agent/
  backend/
    main.py
    app/
      routers/          FastAPI routes and WebSocket endpoint
      services/         OpenCV, YOLO, risk rules, LLM client, background job
      database.py       SQLite setup and simple query helpers
      schemas.py        Pydantic request/response models
    requirements.txt
    .env.example
  frontend/
    src/
      components/       Dashboard UI components
      api.ts            REST and WebSocket client helpers
      types.ts          Shared frontend types
    package.json
```

## What The App Detects

- Vehicles, pedestrians, and stop signs from YOLO when `YOLO_MODEL_PATH` points to a local model.
- A fallback OpenCV red-shape stop-sign approximation when YOLO is not configured.
- Close-following approximation when a vehicle box is large and low in the frame.
- Lane drift placeholder logic using simple lane-line estimation. This is intentionally marked as placeholder logic and should be replaced with a dedicated lane model for production.
- A Driving Risk Brief with `verdict`, `confidence`, `evidence`, `recommended_action`, and `key_questions`.

## Windows Setup

These steps use PowerShell.

### 1. Install prerequisites

Install:

- Python 3.11 or newer from [python.org](https://www.python.org/downloads/)
- Node.js LTS from [nodejs.org](https://nodejs.org/)
- Git from [git-scm.com](https://git-scm.com/)

After installing, open a new PowerShell window and check:

```powershell
python --version
node --version
npm --version
```

### 2. Start the backend

From the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend will run at:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

### 3. Optional YOLO setup

The app runs without YOLO, but object detection is much better with it.

```powershell
pip install ultralytics
```

Download a YOLO model such as `yolov8n.pt`, save it somewhere like:

```text
C:\models\yolov8n.pt
```

Then edit `backend\.env`:

```env
YOLO_MODEL_PATH=C:\models\yolov8n.pt
```

Restart the backend after changing `.env`.

### 4. Optional LLM setup

By default, the backend uses a local heuristic brief generator so the app works immediately.

To use an OpenAI-compatible LLM service, edit `backend\.env`:

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://api.openai.com
LLM_API_KEY=your_api_key_here
LLM_MODEL=gpt-4o-mini
```

Restart the backend after changing `.env`.

### 5. Start the frontend

Open a second PowerShell window from the project root:

```powershell
cd frontend
npm install
npm run dev
```

The dashboard will run at:

```text
http://localhost:5173
```

## Daily Development

Backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev
```

## API Overview

- `POST /api/reports/upload` uploads a dashcam video and starts background processing.
- `GET /api/reports` lists saved reports.
- `GET /api/reports/{report_id}` returns one report with events, brief, and feedback.
- `POST /api/reports/{report_id}/feedback` saves `approve`, `dismiss`, or `escalate`.
- `WS /ws/progress/{report_id}` streams processing progress.

## Notes For Beginners

- SQLite data is created automatically in `backend/data/drivesight.db`.
- Uploaded videos are stored in `backend/uploads/`.
- The local heuristic brief keeps the app usable without an API key.
- The lane drift and close-following rules are approximations for learning and prototyping. Do not use this as production safety tooling without stronger models, calibration, and human review.
