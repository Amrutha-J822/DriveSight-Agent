"""SQLite data layer for the Fleet Safety Review Platform.

Tables
------
users                  Reviewer / manager / driver accounts (mock auth in Phase 1).
drivers                The people whose driving is being reviewed.
cases                  One per uploaded dashcam video.
detected_events        Per-event rows so each can be approved/dismissed/escalated.
coaching_recommendations  Auto-generated coaching briefs attached to a case/driver.
driver_comments        Driver replies on their own cases.

A handful of demo users + drivers are seeded on first boot so the UI has
something to render immediately.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import sqlite3
from typing import Any, Iterable

from app.config import DB_PATH


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


SCHEMA: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL CHECK (role IN ('driver','reviewer','manager')),
        driver_id TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS drivers (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        employee_id TEXT NOT NULL UNIQUE,
        vehicle_id TEXT,
        risk_score INTEGER NOT NULL DEFAULT 50,
        total_events INTEGER NOT NULL DEFAULT 0,
        approved_events INTEGER NOT NULL DEFAULT 0,
        dismissed_events INTEGER NOT NULL DEFAULT 0,
        escalated_events INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cases (
        id TEXT PRIMARY KEY,
        driver_id TEXT NOT NULL REFERENCES drivers(id),
        reviewer_id TEXT REFERENCES users(id),
        video_filename TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'new'
            CHECK (status IN ('new','processing','review','approved','dismissed','escalated','resolved','failed')),
        progress INTEGER NOT NULL DEFAULT 0,
        ai_summary TEXT,
        brief_json TEXT,
        reviewer_notes TEXT,
        error TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS detected_events (
        id TEXT PRIMARY KEY,
        case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        event_type TEXT NOT NULL,
        timestamp_seconds REAL NOT NULL,
        severity TEXT NOT NULL DEFAULT 'medium'
            CHECK (severity IN ('info','low','medium','high','critical')),
        confidence REAL NOT NULL DEFAULT 0.5,
        description TEXT NOT NULL,
        evidence_json TEXT,
        status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending','approved','dismissed','escalated')),
        dismissal_reason TEXT,
        escalation_notes TEXT,
        reviewer_id TEXT REFERENCES users(id),
        reviewed_at TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS coaching_recommendations (
        id TEXT PRIMARY KEY,
        driver_id TEXT NOT NULL REFERENCES drivers(id),
        case_id TEXT REFERENCES cases(id) ON DELETE SET NULL,
        recommendation_text TEXT NOT NULL,
        reason TEXT NOT NULL,
        acknowledged INTEGER NOT NULL DEFAULT 0,
        acknowledged_at TEXT,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS driver_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
        driver_id TEXT NOT NULL REFERENCES drivers(id),
        text TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
)


def _migrate_cases_constraint(connection: sqlite3.Connection) -> None:
    """Rebuild ``cases`` table if its CHECK constraint is missing 'resolved'."""
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='cases'"
    ).fetchone()
    if not row or "'resolved'" in (row["sql"] or ""):
        return
    connection.executescript(
        """
        ALTER TABLE cases RENAME TO _cases_old;
        CREATE TABLE cases (
            id TEXT PRIMARY KEY,
            driver_id TEXT NOT NULL REFERENCES drivers(id),
            reviewer_id TEXT REFERENCES users(id),
            video_filename TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new'
                CHECK (status IN ('new','processing','review','approved','dismissed','escalated','resolved','failed')),
            progress INTEGER NOT NULL DEFAULT 0,
            ai_summary TEXT,
            brief_json TEXT,
            reviewer_notes TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO cases SELECT * FROM _cases_old;
        DROP TABLE _cases_old;
        """
    )


def init_db() -> None:
    with get_connection() as connection:
        for statement in SCHEMA:
            connection.execute(statement)
        _migrate_cases_constraint(connection)
    seed_demo_data()


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

DEMO_DRIVERS: tuple[dict[str, Any], ...] = (
    {"id": "drv_john", "name": "John Smith", "employee_id": "EMP-1042", "vehicle_id": "VAN-102"},
    {"id": "drv_maria", "name": "Maria Lee", "employee_id": "EMP-1187", "vehicle_id": "VAN-104"},
    {"id": "drv_alex", "name": "Alex Rivera", "employee_id": "EMP-1233", "vehicle_id": "TRK-209"},
)

DEMO_USERS: tuple[dict[str, Any], ...] = (
    {
        "id": "usr_sarah",
        "name": "Sarah Chen",
        "email": "sarah@fleet.demo",
        "role": "reviewer",
        "driver_id": None,
    },
    {
        "id": "usr_marcus",
        "name": "Marcus Patel",
        "email": "marcus@fleet.demo",
        "role": "manager",
        "driver_id": None,
    },
    {
        "id": "usr_john",
        "name": "John Smith",
        "email": "john@fleet.demo",
        "role": "driver",
        "driver_id": "drv_john",
    },
)


def seed_demo_data() -> None:
    with get_connection() as connection:
        existing = connection.execute("SELECT COUNT(*) FROM drivers").fetchone()[0]
        if existing:
            return
        now = utc_now()
        for driver in DEMO_DRIVERS:
            connection.execute(
                """
                INSERT INTO drivers (id, name, employee_id, vehicle_id, risk_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (driver["id"], driver["name"], driver["employee_id"], driver["vehicle_id"], 50, now),
            )
        for user in DEMO_USERS:
            connection.execute(
                """
                INSERT INTO users (id, name, email, role, driver_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user["id"], user["name"], user["email"], user["role"], user["driver_id"], now),
            )


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


def get_user(user_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def list_users() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM users ORDER BY role, name").fetchall()
    return [dict(row) for row in rows]


def insert_user(user_id: str, name: str, email: str, role: str, driver_id: str | None) -> dict[str, Any]:
    now = utc_now()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO users (id, name, email, role, driver_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, email, role, driver_id, now),
        )
    return get_user(user_id) or {}


def update_user(user_id: str, name: str, email: str, role: str, driver_id: str | None) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET name = ?, email = ?, role = ?, driver_id = ? WHERE id = ?",
            (name, email, role, driver_id, user_id),
        )
    return get_user(user_id) or {}


def delete_user(user_id: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM users WHERE id = ?", (user_id,))


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------


def get_driver(driver_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,)).fetchone()
    return dict(row) if row else None


def list_drivers() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM drivers ORDER BY name").fetchall()
    return [dict(row) for row in rows]


def insert_driver(driver_id: str, name: str, employee_id: str, vehicle_id: str | None) -> dict[str, Any]:
    now = utc_now()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO drivers (id, name, employee_id, vehicle_id, risk_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (driver_id, name, employee_id, vehicle_id, 50, now),
        )
    return get_driver(driver_id) or {}


def update_driver(driver_id: str, name: str, employee_id: str, vehicle_id: str | None) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute(
            "UPDATE drivers SET name = ?, employee_id = ?, vehicle_id = ? WHERE id = ?",
            (name, employee_id, vehicle_id, driver_id),
        )
    return get_driver(driver_id) or {}


def delete_driver(driver_id: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM drivers WHERE id = ?", (driver_id,))


def adjust_driver_counters(
    driver_id: str,
    *,
    risk_delta: int = 0,
    approved_delta: int = 0,
    dismissed_delta: int = 0,
    escalated_delta: int = 0,
    total_delta: int = 0,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE drivers SET
              risk_score = MAX(0, MIN(100, risk_score + ?)),
              approved_events = approved_events + ?,
              dismissed_events = dismissed_events + ?,
              escalated_events = escalated_events + ?,
              total_events = total_events + ?
            WHERE id = ?
            """,
            (risk_delta, approved_delta, dismissed_delta, escalated_delta, total_delta, driver_id),
        )


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------


def create_case(case_id: str, driver_id: str, reviewer_id: str | None, filename: str) -> None:
    now = utc_now()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO cases (id, driver_id, reviewer_id, video_filename, status, progress, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'processing', 0, ?, ?)
            """,
            (case_id, driver_id, reviewer_id, filename, now, now),
        )


VALID_CASE_STATUSES: frozenset[str] = frozenset(
    {"new", "processing", "review", "approved", "dismissed", "escalated", "resolved", "failed"}
)


def update_case_progress(case_id: str, status: str, progress: int, error: str | None = None) -> None:
    """Update case progress. ``status`` must be one of VALID_CASE_STATUSES; unknown values
    are coerced to 'processing' so a creative WebSocket message can't crash the DB."""
    safe_status = status if status in VALID_CASE_STATUSES else "processing"
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE cases
            SET status = ?, progress = ?, error = ?, updated_at = ?
            WHERE id = ?
            """,
            (safe_status, progress, error, utc_now(), case_id),
        )


def save_case_brief(case_id: str, brief: dict[str, Any]) -> None:
    """Brief produced after processing completes. Case enters 'review' status."""
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE cases
            SET status = 'review', progress = 100,
                ai_summary = ?, brief_json = ?, error = NULL, updated_at = ?
            WHERE id = ?
            """,
            (brief.get("verdict"), json.dumps(brief), utc_now(), case_id),
        )


def set_case_status(case_id: str, status: str, reviewer_notes: str | None = None) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE cases
            SET status = ?, reviewer_notes = COALESCE(?, reviewer_notes), updated_at = ?
            WHERE id = ?
            """,
            (status, reviewer_notes, utc_now(), case_id),
        )


def get_case(case_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    return _hydrate_case(dict(row)) if row else None


def list_cases(*, driver_id: str | None = None, statuses: Iterable[str] | None = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM cases"
    clauses: list[str] = []
    params: list[Any] = []
    if driver_id:
        clauses.append("driver_id = ?")
        params.append(driver_id)
    if statuses:
        status_list = list(statuses)
        placeholder = ",".join(["?"] * len(status_list))
        clauses.append(f"status IN ({placeholder})")
        params.extend(status_list)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at DESC"
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [_hydrate_case(dict(row)) for row in rows]


def _hydrate_case(case: dict[str, Any]) -> dict[str, Any]:
    case["brief"] = json.loads(case.pop("brief_json") or "null")
    case["events"] = list_case_events(case["id"])
    case["driver"] = get_driver(case["driver_id"])
    case["comments"] = list_driver_comments(case["id"])
    return case


# ---------------------------------------------------------------------------
# Detected events
# ---------------------------------------------------------------------------


def insert_event(
    event_id: str,
    case_id: str,
    event_type: str,
    timestamp_seconds: float,
    severity: str,
    confidence: float,
    description: str,
    evidence: dict[str, Any],
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO detected_events
                (id, case_id, event_type, timestamp_seconds, severity, confidence,
                 description, evidence_json, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                event_id,
                case_id,
                event_type,
                round(timestamp_seconds, 2),
                severity,
                confidence,
                description,
                json.dumps(evidence),
                utc_now(),
            ),
        )


def get_event(event_id: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM detected_events WHERE id = ?", (event_id,)).fetchone()
    if not row:
        return None
    event = dict(row)
    event["evidence"] = json.loads(event.pop("evidence_json") or "{}")
    return event


def list_case_events(case_id: str) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM detected_events WHERE case_id = ? ORDER BY timestamp_seconds",
            (case_id,),
        ).fetchall()
    out = []
    for row in rows:
        event = dict(row)
        event["evidence"] = json.loads(event.pop("evidence_json") or "{}")
        out.append(event)
    return out


def update_event_decision(
    event_id: str,
    *,
    status: str,
    reviewer_id: str,
    dismissal_reason: str | None = None,
    escalation_notes: str | None = None,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE detected_events
            SET status = ?, reviewer_id = ?, reviewed_at = ?,
                dismissal_reason = COALESCE(?, dismissal_reason),
                escalation_notes = COALESCE(?, escalation_notes)
            WHERE id = ?
            """,
            (status, reviewer_id, utc_now(), dismissal_reason, escalation_notes, event_id),
        )


# ---------------------------------------------------------------------------
# Coaching recommendations
# ---------------------------------------------------------------------------


def insert_coaching(rec_id: str, driver_id: str, case_id: str | None, text: str, reason: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO coaching_recommendations
                (id, driver_id, case_id, recommendation_text, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (rec_id, driver_id, case_id, text, reason, utc_now()),
        )


def list_coaching(driver_id: str) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM coaching_recommendations WHERE driver_id = ? ORDER BY created_at DESC",
            (driver_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def acknowledge_coaching(rec_id: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE coaching_recommendations SET acknowledged = 1, acknowledged_at = ? WHERE id = ?",
            (utc_now(), rec_id),
        )


# ---------------------------------------------------------------------------
# Driver comments
# ---------------------------------------------------------------------------


def insert_driver_comment(case_id: str, driver_id: str, text: str) -> dict[str, Any]:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO driver_comments (case_id, driver_id, text, created_at) VALUES (?, ?, ?, ?)",
            (case_id, driver_id, text, utc_now()),
        )
        row = connection.execute(
            "SELECT * FROM driver_comments WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def list_driver_comments(case_id: str) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM driver_comments WHERE case_id = ? ORDER BY created_at",
            (case_id,),
        ).fetchall()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Analytics for the manager dashboard
# ---------------------------------------------------------------------------


def analytics_summary() -> dict[str, Any]:
    with get_connection() as connection:
        total_cases = connection.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        reviewed_cases = connection.execute(
            "SELECT COUNT(*) FROM cases WHERE status IN ('approved','dismissed','escalated')"
        ).fetchone()[0]
        pending_escalations = connection.execute(
            "SELECT COUNT(*) FROM cases WHERE status = 'escalated'"
        ).fetchone()[0]

        decided = connection.execute(
            "SELECT COUNT(*) FROM detected_events WHERE status IN ('approved','dismissed','escalated')"
        ).fetchone()[0]
        dismissed = connection.execute(
            "SELECT COUNT(*) FROM detected_events WHERE status = 'dismissed'"
        ).fetchone()[0]
        false_positive_rate = (dismissed / decided) if decided else 0.0

        most_common_row = connection.execute(
            """
            SELECT event_type, COUNT(*) AS occurrences
            FROM detected_events
            WHERE status = 'approved'
            GROUP BY event_type
            ORDER BY occurrences DESC
            LIMIT 1
            """
        ).fetchone()

        high_risk_drivers = connection.execute(
            "SELECT id, name, risk_score FROM drivers WHERE risk_score >= 70 ORDER BY risk_score DESC LIMIT 5"
        ).fetchall()

    return {
        "total_cases": total_cases,
        "reviewed_cases": reviewed_cases,
        "pending_escalations": pending_escalations,
        "false_positive_rate": round(false_positive_rate, 3),
        "most_common_event": most_common_row["event_type"] if most_common_row else None,
        "high_risk_drivers": [dict(row) for row in high_risk_drivers],
    }
