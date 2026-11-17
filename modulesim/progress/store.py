"""Progress (Simplified): saves each attempt in one SQLite table. No analytics.

Interface:
    save_attempt(attempt) -> attempt id
    latest(student_id) -> attempt dict or None
    attempts(student_id) -> list of attempt dicts, newest first

SQLite keeps the whole database in one ordinary file. The code creates the
file the first time it runs, so it is never part of the submission.
"""

import json
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    module TEXT NOT NULL,
    event_title TEXT NOT NULL,
    response_id TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    topics TEXT NOT NULL,
    band TEXT NOT NULL,
    flagged INTEGER NOT NULL,
    result TEXT NOT NULL,
    feedback TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


class ProgressStore:
    def __init__(self, db_path: str):
        self._db_path = db_path
        # ":memory:" keeps one shared connection, so tests leave no file behind.
        self._memory = sqlite3.connect(":memory:", check_same_thread=False) if db_path == ":memory:" else None
        db = self._connect()
        try:
            db.execute(SCHEMA)
            db.commit()
        finally:
            if db is not self._memory:
                db.close()

    def _connect(self) -> sqlite3.Connection:
        return self._memory or sqlite3.connect(self._db_path)

    def save_attempt(self, attempt: dict) -> int:
        row = (
            attempt["student_id"], attempt["module"], attempt["result"]["event_title"],
            attempt["result"]["response_id"], attempt["reasoning"],
            json.dumps(attempt.get("topics", [])), attempt["feedback"]["band"],
            int(attempt["feedback"].get("flagged", False)),
            json.dumps(attempt["result"]), json.dumps(attempt["feedback"]),
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        db = self._connect()
        try:
            cursor = db.execute(
                "INSERT INTO attempts (student_id, module, event_title, response_id, reasoning,"
                " topics, band, flagged, result, feedback, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
            db.commit()
            return cursor.lastrowid
        finally:
            if db is not self._memory:
                db.close()

    def attempts(self, student_id: str) -> list[dict]:
        db = self._connect()
        try:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM attempts WHERE student_id = ? ORDER BY id DESC",
                              (student_id,)).fetchall()
        finally:
            if db is not self._memory:
                db.close()
        return [self._to_dict(r) for r in rows]

    def latest(self, student_id: str) -> dict | None:
        found = self.attempts(student_id)
        return found[0] if found else None

    @staticmethod
    def _to_dict(row) -> dict:
        d = dict(row)
        for key in ("topics", "result", "feedback"):
            d[key] = json.loads(d[key])
        d["flagged"] = bool(d["flagged"])
        return d
