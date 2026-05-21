# DriveSight Agent — Fleet Safety Review Platform

DriveSight Agent is a human-in-the-loop AI safety platform for fleet teams. A reviewer uploads a dashcam clip on behalf of a driver, the FastAPI backend extracts driving-risk events with OpenCV (and optionally YOLO), and the reviewer then **approves**, **dismisses**, or **escalates** each event. Decisions update the driver's risk score, generate coaching recommendations, and feed manager analytics. The React + TypeScript frontend renders three role-based portals.

## Roles & portals (Phase 1)

- **Reviewer** — sees the Case Queue, opens a case, decides each event (Approve / Dismiss with reason / Escalate with notes), finalizes the case.
- **Driver** — sees their own safety score, case history, and coaching recommendations; can acknowledge coaching and add a comment on their own case.
- **Manager** — sees the analytics dashboard (total cases, pending escalations, false-positive rate, top risk drivers) and can also act as a reviewer.

> Authentication in Phase 1 is a mock login picker (you choose a seeded user). Phase 2 swaps this for Firebase Google + Email/Password without changing the rest of the app — the backend already reads the user id from a request header.

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

## Deployment (Frontend on Vercel, Backend on Render)

The frontend (Vite + React) is hosted on Vercel. The backend (FastAPI + OpenCV + YOLO + WebSockets + SQLite) needs a long-running container with a persistent disk, so it is hosted on Render — Vercel's serverless functions cannot run it (size limits, no WebSockets, no persistent FS).

### 1. Deploy the backend to Render

1. Push this repo to GitHub (already at `https://github.com/Amrutha-J822/DriveSight-Agent`).
2. In the Render dashboard click **New → Blueprint** and select this repo. Render reads `render.yaml` and provisions a free web service named `drivesight-agent-api` running `uvicorn main:app`.
3. After creation, set the secret/optional env vars in the Render dashboard:
   - `ALLOWED_ORIGINS` — your Vercel URL, e.g. `https://drivesight-agent.vercel.app`
   - `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` — only if you want a real LLM; otherwise leave the local heuristic.
4. Render gives you a URL like `https://drivesight-agent-api.onrender.com`. Verify `https://<that-url>/api/health` returns `{"status":"ok"}`.

Notes on the free tier:

- Render's free web services have 512 MB RAM and sleep after 15 min of inactivity. First request after sleep takes ~30s to wake.
- The free tier does **not** support persistent disks. Reports and uploaded videos live in the container's ephemeral filesystem and are wiped when the container restarts or sleeps. Fine for a demo, not for production.
- `ultralytics`/YOLO is **not** installed by default because PyTorch alone exceeds 512 MB. The backend falls back to OpenCV heuristics. To enable YOLO, upgrade to the **Starter** plan ($7/mo), uncomment `ultralytics` in `backend/requirements.txt`, upload a `.pt` model, and set `YOLO_MODEL_PATH`.

### 2. Deploy the frontend to Vercel

1. Import the same GitHub repo into Vercel. The included `vercel.json` already sets the framework to `vite`, builds from `frontend/`, and outputs `frontend/dist`.
2. In **Project Settings → Environment Variables**, add:
   - `VITE_API_URL` = `https://drivesight-agent-api.onrender.com` (your Render URL)
3. Trigger a deploy (push to `main` or click **Redeploy**). Vercel builds the SPA and serves it.

After both are live, copy the Vercel URL back into `ALLOWED_ORIGINS` on Render so CORS lets the browser through.

### 3. CLI alternative

If you prefer the Vercel CLI:

```bash
npm i -g vercel
vercel login
vercel env add VITE_API_URL production   # paste the Render URL when prompted
vercel --prod
```

## Notes For Beginners

- SQLite data is created automatically in `backend/data/drivesight.db`.
- Uploaded videos are stored in `backend/uploads/`.
- The local heuristic brief keeps the app usable without an API key.
- The lane drift and close-following rules are approximations for learning and prototyping. Do not use this as production safety tooling without stronger models, calibration, and human review.
