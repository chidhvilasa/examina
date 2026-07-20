#!/usr/bin/env python
"""
Weekly alpha data snapshot exporter.

Standalone: uses only the Python standard library (sqlite3, json, os,
argparse, datetime) so it can run outside the EXAMINA virtual
environment against a copy of the production/alpha database file. It
never imports any `examina` module.

Usage:
    python scripts/export_alpha_snapshot.py --week 1

Writes two kinds of output to alpha-data/week{N}/:
  - raw_feedback.json / raw_incorrect.json — individual records,
    anonymized (no report_id, no timestamps, only response values; the
    original report_id is replaced by a row index). Never committed to
    the repository (see .gitignore) — Constitution Principle 7.
  - week{N}_summary.json — aggregate metrics only, with version
    provenance. Committed to the repository.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

_DEFAULT_PRISM_VERSION = "0.3.2"
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _resolve_db_path(database_url: str) -> str:
    """Strip a `sqlite:///` (or `sqlite://`) prefix, if present, to get
    a plain filesystem path sqlite3.connect() can open directly."""
    if database_url.startswith("sqlite:///"):
        return database_url[len("sqlite:///") :]
    if database_url.startswith("sqlite://"):
        return database_url[len("sqlite://") :]
    return database_url


def _parse_created_at(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _rows_within_past_week(rows: list[sqlite3.Row], cutoff: datetime) -> list[sqlite3.Row]:
    kept = []
    for row in rows:
        created_at = _parse_created_at(row["created_at"])
        if created_at is not None and created_at >= cutoff:
            kept.append(row)
    return kept


def _fetch_all(conn: sqlite3.Connection, table: str) -> list[sqlite3.Row]:
    cursor = conn.execute(f"SELECT * FROM {table}")  # noqa: S608 - table name is a fixed constant, never user input
    return cursor.fetchall()


def _distribution(values: list[str | None]) -> dict[str, int]:
    counter = Counter(v for v in values if v is not None)
    return dict(counter)


def _mean(values: list[int | float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def export_snapshot(week: int, database_url: str, output_dir: Path) -> dict[str, Any]:
    db_path = _resolve_db_path(database_url)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=7)

    try:
        report_rows = _rows_within_past_week(_fetch_all(conn, "reports"), cutoff)
        feedback_rows = _rows_within_past_week(_fetch_all(conn, "feedback"), cutoff)
        incorrect_rows = _rows_within_past_week(_fetch_all(conn, "incorrect_analyses"), cutoff)
    finally:
        conn.close()

    understandability_scores = [
        row["understandability_score"]
        for row in feedback_rows
        if row["understandability_score"] is not None
    ]
    changed_assessment_distribution = _distribution(
        [row["changed_assessment"] for row in feedback_rows]
    )
    workflow_adoption_distribution = _distribution(
        [row["would_use_in_workflow"] for row in feedback_rows]
    )
    most_useful_sections = _distribution([row["most_useful_section"] for row in feedback_rows])
    least_useful_sections = _distribution([row["least_useful_section"] for row in feedback_rows])

    metrics = {
        "total_analyses": len(report_rows),
        "total_feedback": len(feedback_rows),
        "mean_understandability": _mean(understandability_scores),
        "changed_assessment_distribution": changed_assessment_distribution,
        "workflow_adoption_distribution": workflow_adoption_distribution,
        "most_useful_sections": most_useful_sections,
        "least_useful_sections": least_useful_sections,
        "total_incorrect_reports": len(incorrect_rows),
    }

    examina_version = os.environ.get("EXAMINA_VERSION", "unknown")
    prism_version = os.environ.get("PRISM_VERSION", _DEFAULT_PRISM_VERSION)

    summary = {
        "snapshot_week": week,
        "snapshot_date": datetime.now(UTC).isoformat(),
        "examina_version": examina_version,
        "prism_version": prism_version,
        "bridge_version": "bridge:1.0",
        "metrics": metrics,
    }

    raw_feedback = [
        {
            "index": index,
            "understandability_score": row["understandability_score"],
            "most_useful_section": row["most_useful_section"],
            "least_useful_section": row["least_useful_section"],
            "changed_assessment": row["changed_assessment"],
            "would_use_in_workflow": row["would_use_in_workflow"],
            "missing_information": row["missing_information"],
        }
        for index, row in enumerate(feedback_rows)
    ]

    raw_incorrect = [
        {
            "index": index,
            "overall_confidence": row["overall_confidence"],
            "user_comment": row["user_comment"],
        }
        for index, row in enumerate(incorrect_rows)
    ]

    week_dir = output_dir / f"week{week}"
    week_dir.mkdir(parents=True, exist_ok=True)

    (week_dir / "raw_feedback.json").write_text(
        json.dumps(raw_feedback, indent=2), encoding="utf-8"
    )
    (week_dir / "raw_incorrect.json").write_text(
        json.dumps(raw_incorrect, indent=2), encoding="utf-8"
    )
    (week_dir / f"week{week}_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a weekly EXAMINA alpha data snapshot.")
    parser.add_argument("--week", type=int, required=True, help="Alpha week number (1, 2, ...)")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL", "examina_dev.db")
    output_dir = _REPO_ROOT / "alpha-data"

    summary = export_snapshot(week=args.week, database_url=database_url, output_dir=output_dir)

    print(f"Snapshot written: alpha-data/week{args.week}/")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
