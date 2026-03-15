"""
SQLite database layer for storing Strava activities.
"""

import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..config import Settings


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(Settings.DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS activities (
                id                    INTEGER PRIMARY KEY,
                name                  TEXT,
                type                  TEXT,
                sport_type            TEXT,
                workout_type          INTEGER,
                start_date_local      TEXT,
                timezone              TEXT,
                distance              REAL,
                moving_time           INTEGER,
                elapsed_time          INTEGER,
                total_elevation_gain  REAL,
                average_speed         REAL,
                max_speed             REAL,
                average_heartrate     REAL,
                max_heartrate         REAL,
                elev_high             REAL,
                elev_low              REAL,
                device_name           TEXT,
                trainer               INTEGER,
                commute               INTEGER,
                pr_count              INTEGER,
                kudos_count           INTEGER,
                achievement_count     INTEGER
            );

            CREATE TABLE IF NOT EXISTS activity_details (
                activity_id           INTEGER PRIMARY KEY,
                calories              INTEGER,
                suffer_score          INTEGER,
                perceived_exertion    REAL,
                average_cadence       REAL,
                average_watts         REAL,
                weighted_average_watts INTEGER,
                description           TEXT,
                gear_id               TEXT,
                splits_metric         TEXT,
                laps                  TEXT,
                FOREIGN KEY (activity_id) REFERENCES activities(id)
            );

            CREATE TABLE IF NOT EXISTS activity_map (
                activity_id           INTEGER PRIMARY KEY,
                summary_polyline      TEXT,
                FOREIGN KEY (activity_id) REFERENCES activities(id)
            );

            CREATE INDEX IF NOT EXISTS idx_activities_type
                ON activities(type);
            CREATE INDEX IF NOT EXISTS idx_activities_date
                ON activities(start_date_local);
        """)


def get_latest_activity_date() -> Optional[str]:
    """Return the start_date_local of the most recent stored activity, or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT MAX(start_date_local) FROM activities"
        ).fetchone()
        return row[0] if row else None


def upsert_activities(activities: List[Dict[str, Any]]) -> int:
    """
    Insert or replace activities from Strava API response.
    Returns the number of rows upserted.
    """
    rows = []
    map_rows = []

    for a in activities:
        rows.append((
            a.get("id"),
            a.get("name"),
            a.get("type"),
            a.get("sport_type"),
            a.get("workout_type"),
            a.get("start_date_local"),
            a.get("timezone"),
            a.get("distance"),
            a.get("moving_time"),
            a.get("elapsed_time"),
            a.get("total_elevation_gain"),
            a.get("average_speed"),
            a.get("max_speed"),
            a.get("average_heartrate"),
            a.get("max_heartrate"),
            a.get("elev_high"),
            a.get("elev_low"),
            a.get("device_name"),
            int(a.get("trainer", False)),
            int(a.get("commute", False)),
            a.get("pr_count", 0),
            a.get("kudos_count", 0),
            a.get("achievement_count", 0),
        ))

        polyline = (a.get("map") or {}).get("summary_polyline")
        if polyline:
            map_rows.append((a["id"], polyline))

    with get_connection() as conn:
        conn.executemany("""
            INSERT OR REPLACE INTO activities (
                id, name, type, sport_type, workout_type,
                start_date_local, timezone,
                distance, moving_time, elapsed_time, total_elevation_gain,
                average_speed, max_speed,
                average_heartrate, max_heartrate,
                elev_high, elev_low,
                device_name, trainer, commute,
                pr_count, kudos_count, achievement_count
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, rows)

        if map_rows:
            conn.executemany("""
                INSERT OR REPLACE INTO activity_map (activity_id, summary_polyline)
                VALUES (?,?)
            """, map_rows)

    return len(rows)


def upsert_activity_details(activity_id: int, details: Dict[str, Any]) -> None:
    """Insert or replace detail data for a single activity."""
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO activity_details (
                activity_id, calories, suffer_score, perceived_exertion,
                average_cadence, average_watts, weighted_average_watts,
                description, gear_id, splits_metric, laps
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            activity_id,
            details.get("calories"),
            details.get("suffer_score"),
            details.get("perceived_exertion"),
            details.get("average_cadence"),
            details.get("average_watts"),
            details.get("weighted_average_watts"),
            details.get("description"),
            details.get("gear_id"),
            json.dumps(details.get("splits_metric")) if details.get("splits_metric") else None,
            json.dumps(details.get("laps")) if details.get("laps") else None,
        ))


def query_activities(
    activity_type: str = "Run",
    limit: int = 20,
    offset: int = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_distance_m: Optional[float] = None,
    max_distance_m: Optional[float] = None,
) -> List[Dict]:
    """Query activities with optional filters. Returns list of dicts."""
    conditions = []
    params = []

    if activity_type:
        conditions.append("type = ?")
        params.append(activity_type)
    if start_date:
        conditions.append("start_date_local >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("start_date_local <= ?")
        params.append(end_date)
    if min_distance_m is not None:
        conditions.append("distance >= ?")
        params.append(min_distance_m)
    if max_distance_m is not None:
        conditions.append("distance <= ?")
        params.append(max_distance_m)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.extend([limit, offset])

    with get_connection() as conn:
        rows = conn.execute(f"""
            SELECT * FROM activities
            {where}
            ORDER BY start_date_local DESC
            LIMIT ? OFFSET ?
        """, params).fetchall()

    return [dict(r) for r in rows]


def query_activity_with_details(activity_id: int) -> Optional[Dict]:
    """Return a single activity joined with its detail row."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT a.*, d.calories, d.suffer_score, d.perceived_exertion,
                   d.average_cadence, d.average_watts, d.weighted_average_watts,
                   d.description, d.gear_id, d.splits_metric, d.laps,
                   m.summary_polyline
            FROM activities a
            LEFT JOIN activity_details d ON a.id = d.activity_id
            LEFT JOIN activity_map m ON a.id = m.activity_id
            WHERE a.id = ?
        """, (activity_id,)).fetchone()
    return dict(row) if row else None


def get_summary_stats(activity_type: str = "Run") -> Dict[str, Any]:
    """Return aggregate stats for a given activity type."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*)                        AS total_activities,
                ROUND(SUM(distance) / 1609.34, 2) AS total_miles,
                ROUND(AVG(distance) / 1609.34, 2) AS avg_miles,
                ROUND(MAX(distance) / 1609.34, 2) AS max_miles,
                ROUND(MIN(distance) / 1609.34, 2) AS min_miles,
                ROUND(AVG(average_heartrate), 0)  AS avg_hr,
                ROUND(MAX(max_heartrate), 0)       AS max_hr,
                SUM(moving_time)                  AS total_moving_time_s,
                ROUND(AVG(total_elevation_gain) * 3.28084, 0) AS avg_elevation_gain_ft
            FROM activities
            WHERE type = ?
        """, (activity_type,)).fetchone()
    return dict(row) if row else {}


def get_weekly_mileage(weeks: int = 12) -> List[Dict]:
    """Return weekly mileage totals for the last N weeks."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                strftime('%Y-W%W', start_date_local) AS week,
                ROUND(SUM(distance) / 1609.34, 2)    AS total_miles,
                COUNT(*)                              AS run_count,
                ROUND(AVG(average_heartrate), 0)      AS avg_hr
            FROM activities
            WHERE type = 'Run'
              AND start_date_local >= date('now', ? || ' days')
            GROUP BY week
            ORDER BY week DESC
        """, (f"-{weeks * 7}",)).fetchall()
    return [dict(r) for r in rows]


def get_activity_count() -> int:
    """Return total number of stored activities."""
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0]


def load_all_activities() -> List[Dict]:
    """Return all stored activities ordered by date descending."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM activities ORDER BY start_date_local DESC"
        ).fetchall()
    return [dict(r) for r in rows]
