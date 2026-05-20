from __future__ import annotations

from datetime import datetime, timezone
import json
import sqlite3
from typing import Any

from app.config import DB_PATH


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                status TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                verdict TEXT,
                confidence REAL,
                brief_json TEXT,
                events_json TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL,
                action TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(report_id) REFERENCES reports(id)
            )
            """
        )


def create_report(report_id: str, filename: str) -> None:
    now = utc_now()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO reports (id, filename, status, progress, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (report_id, filename, "queued", 0, now, now),
        )


def update_report_progress(report_id: str, status: str, progress: int, error: str | None = None) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE reports
            SET status = ?, progress = ?, error = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, progress, error, utc_now(), report_id),
        )


def save_report_result(report_id: str, events: list[dict[str, Any]], brief: dict[str, Any]) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE reports
            SET status = ?, progress = ?, verdict = ?, confidence = ?,
                events_json = ?, brief_json = ?, error = NULL, updated_at = ?
            WHERE id = ?
            """,
            (
                "complete",
                100,
                brief.get("verdict"),
                brief.get("confidence"),
                json.dumps(events),
                json.dumps(brief),
                utc_now(),
                report_id,
            ),
        )


def row_to_report(row: sqlite3.Row) -> dict[str, Any]:
    report = dict(row)
    report["events"] = json.loads(report.pop("events_json") or "[]")
    report["brief"] = json.loads(report.pop("brief_json") or "null")
    report["feedback"] = list_feedback(report["id"])
    return report


def get_report(report_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    return row_to_report(row) if row else None


def list_reports() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
    return [row_to_report(row) for row in rows]


def add_feedback(report_id: str, action: str, note: str | None) -> dict[str, Any]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO feedback (report_id, action, note, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (report_id, action, note, utc_now()),
        )
        row = connection.execute("SELECT * FROM feedback WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


def list_feedback(report_id: str) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM feedback WHERE report_id = ? ORDER BY created_at DESC",
            (report_id,),
        ).fetchall()
    return [dict(row) for row in rows]
