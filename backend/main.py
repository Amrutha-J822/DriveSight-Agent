from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS
from app.database import init_db
from app.routers import analytics, cases, drivers, users, ws

app = FastAPI(title="DriveSight Fleet Safety Review API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(users.router)
app.include_router(drivers.router)
app.include_router(cases.router)
app.include_router(analytics.router)
app.include_router(ws.router)
