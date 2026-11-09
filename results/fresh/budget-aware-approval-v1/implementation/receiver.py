"""An experiment-only receiver with atomic action/receipt storage."""

from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
import uuid


class Ledger:
    """Store a note as the side effect, optionally deduplicating operation IDs."""

    def __init__(self, path: Path, *, protected: bool) -> None:
        self.path = path
        self.protected = protected
        with closing(sqlite3.connect(path, timeout=30)) as conn, conn:
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY, operation_id TEXT NOT NULL, message TEXT NOT NULL, receipt TEXT NOT NULL)")
            if protected:
                conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS unique_operation ON entries(operation_id)")

    def record(self, operation_id: str, message: str) -> tuple[str, bool]:
        """Commit one action or return its receipt; reject changed contents."""
        with closing(sqlite3.connect(self.path, timeout=30)) as conn, conn:
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("BEGIN IMMEDIATE")
            if self.protected:
                existing = conn.execute("SELECT message, receipt FROM entries WHERE operation_id = ?", (operation_id,)).fetchone()
                if existing is not None:
                    if existing[0] != message:
                        msg = "Operation ID already used with different contents; no new action recorded."
                        raise ValueError(msg)
                    return existing[1], True
            receipt = json.dumps({
                "operation_id": operation_id, "message": message,
                "receipt_id": str(uuid.uuid4()), "status": "recorded",
            }, sort_keys=True)
            conn.execute("INSERT INTO entries(operation_id, message, receipt) VALUES (?, ?, ?)", (operation_id, message, receipt))
        return receipt, False

    def entries(self) -> list[dict[str, str]]:
        """Read committed receipts, in order of application."""
        with closing(sqlite3.connect(self.path, timeout=30)) as conn, conn:
            return [json.loads(row[0]) for row in conn.execute("SELECT receipt FROM entries ORDER BY id")]
