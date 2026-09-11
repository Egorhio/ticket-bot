"""
SQLite-база для хранения задач мониторинга цен.
Поле origins хранит JSON-массив городов отправления (один или несколько).
"""

import json
import aiosqlite
from datetime import datetime

DB_PATH = "monitors.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS monitors (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id     INTEGER NOT NULL,
                origins     TEXT NOT NULL,
                destination TEXT NOT NULL,
                travel_date TEXT NOT NULL,
                days_range  INTEGER NOT NULL DEFAULT 2,
                threshold   INTEGER NOT NULL,
                active      INTEGER NOT NULL DEFAULT 1,
                notified    INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL
            )
        """)
        # Миграция: переименовать старое поле origin → origins (если БД уже существует)
        try:
            await db.execute("ALTER TABLE monitors RENAME COLUMN origin TO origins")
        except Exception:
            pass
        await db.commit()


async def add_monitor(
    chat_id: int,
    origins: list[str],
    destination: str,
    travel_date: str,
    days_range: int,
    threshold: int,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO monitors
               (chat_id, origins, destination, travel_date, days_range, threshold, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (chat_id, json.dumps(origins, ensure_ascii=False), destination,
             travel_date, days_range, threshold, datetime.now().isoformat()),
        )
        await db.commit()
        return cursor.lastrowid


def _decode_origins(row: dict) -> dict:
    """Декодирует поле origins из JSON в список."""
    raw = row.get("origins", "[]")
    try:
        row["origins"] = json.loads(raw)
    except Exception:
        # Обратная совместимость: если хранилась строка без JSON
        row["origins"] = [raw]
    return row


async def get_active_monitors() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM monitors WHERE active = 1")
        rows = await cursor.fetchall()
        return [_decode_origins(dict(r)) for r in rows]


async def get_user_monitors(chat_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM monitors WHERE chat_id = ? AND active = 1 ORDER BY id",
            (chat_id,),
        )
        rows = await cursor.fetchall()
        return [_decode_origins(dict(r)) for r in rows]


async def deactivate_monitor(monitor_id: int, chat_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE monitors SET active = 0 WHERE id = ? AND chat_id = ?",
            (monitor_id, chat_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def mark_notified(monitor_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE monitors SET notified = 1 WHERE id = ?",
            (monitor_id,),
        )
        await db.commit()
