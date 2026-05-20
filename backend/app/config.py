from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = Path(os.getenv("DRIVESIGHT_DB_PATH", BASE_DIR / "data" / "drivesight.db"))
UPLOAD_DIR = Path(os.getenv("DRIVESIGHT_UPLOAD_DIR", BASE_DIR / "uploads"))

_raw_yolo_model_path = os.getenv("YOLO_MODEL_PATH", "").strip()
YOLO_MODEL_PATH = (
    str((BASE_DIR / _raw_yolo_model_path).resolve())
    if _raw_yolo_model_path and not Path(_raw_yolo_model_path).is_absolute()
    else _raw_yolo_model_path
)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "local").strip().lower()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com").rstrip("/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()

_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]
