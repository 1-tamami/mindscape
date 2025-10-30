#!/usr/bin/env python3
"""
Push questions from the local SQLite database (instance/questions.db)
into the Render-hosted PostgreSQL database.

Usage:
    export DB_URI="postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME"
    python scripts/import_questions.py --truncate

The --truncate flag is optional; use it if you want to wipe the remote table
before inserting the 924 records.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
from typing import List, Dict, Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


SQLITE_PATH = os.path.join("instance", "questions.db")


def load_sqlite_rows(sqlite_path: str) -> List[Dict[str, Any]]:
    """Read all rows from the local SQLite questions table."""
    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(
            f"SQLite database not found at {sqlite_path}. "
            "Make sure you're running this from the project root."
        )

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, category, depth, stage, question,
                   exclude_for_students, created_at, updated_at
            FROM questions
            ORDER BY id
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_engine(db_uri: str) -> Engine:
    """Create a SQLAlchemy engine for the remote Postgres database."""
    if not db_uri:
        raise ValueError(
            "DB_URI environment variable is not set. "
            "Set it or pass --db-uri."
        )
    return create_engine(db_uri, future=True)


def upsert_rows(engine: Engine, rows: List[Dict[str, Any]], truncate: bool) -> None:
    """Insert rows into Postgres, optionally truncating the table first."""
    if not rows:
        print("No rows found in SQLite database. Nothing to import.")
        return

    insert_stmt = text(
        """
        INSERT INTO questions
            (id, category, depth, stage, question,
             exclude_for_students, created_at, updated_at)
        VALUES
            (:id, :category, :depth, :stage, :question,
             :exclude_for_students, :created_at, :updated_at)
        ON CONFLICT (id) DO NOTHING
        """
    )

    with engine.begin() as conn:
        if truncate:
            print("Truncating remote questions table...")
            conn.execute(text("TRUNCATE TABLE questions RESTART IDENTITY CASCADE"))

        print(f"Inserting {len(rows)} rows...")
        conn.execute(insert_stmt, rows)

    print("Import complete.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import questions into Render DB")
    parser.add_argument(
        "--db-uri",
        dest="db_uri",
        default=os.getenv("DB_URI"),
        help="Postgres DB URI (defaults to DB_URI env var)",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate the remote table before inserting",
    )
    args = parser.parse_args()

    rows = load_sqlite_rows(SQLITE_PATH)
    print(f"Loaded {len(rows)} rows from {SQLITE_PATH}.")

    engine = get_engine(args.db_uri)
    upsert_rows(engine, rows, truncate=args.truncate)


if __name__ == "__main__":
    main()
