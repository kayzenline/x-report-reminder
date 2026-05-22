import sqlite3
from pathlib import Path


CREATE_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS accounts (
    handle      TEXT PRIMARY KEY,
    twitter_id  TEXT,
    added_at    TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

CREATE_PROCESSED = """
CREATE TABLE IF NOT EXISTS processed_articles (
    url             TEXT PRIMARY KEY,
    tweet_id        TEXT NOT NULL,
    account_handle  TEXT NOT NULL,
    processed_at    TEXT NOT NULL DEFAULT (datetime('now')),
    note_path       TEXT NOT NULL
)
"""


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(CREATE_ACCOUNTS)
    conn.execute(CREATE_PROCESSED)
    conn.commit()
    return conn


def add_account(conn: sqlite3.Connection, handle: str) -> bool:
    handle = handle.lstrip("@").lower()
    try:
        conn.execute("INSERT INTO accounts (handle) VALUES (?)", (handle,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def remove_account(conn: sqlite3.Connection, handle: str) -> bool:
    handle = handle.lstrip("@").lower()
    cur = conn.execute("DELETE FROM accounts WHERE handle = ?", (handle,))
    conn.commit()
    return cur.rowcount > 0


def list_accounts(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT handle, twitter_id, added_at FROM accounts ORDER BY added_at"
    ).fetchall()
    return [dict(r) for r in rows]


def update_twitter_id(conn: sqlite3.Connection, handle: str, twitter_id: str) -> None:
    conn.execute(
        "UPDATE accounts SET twitter_id = ? WHERE handle = ?", (twitter_id, handle)
    )
    conn.commit()


def is_processed(conn: sqlite3.Connection, url: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM processed_articles WHERE url = ?", (url,)
    ).fetchone()
    return row is not None


def mark_processed(
    conn: sqlite3.Connection,
    url: str,
    tweet_id: str,
    handle: str,
    note_path: str,
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO processed_articles
            (url, tweet_id, account_handle, note_path)
        VALUES (?, ?, ?, ?)
        """,
        (url, tweet_id, handle, note_path),
    )
    conn.commit()
