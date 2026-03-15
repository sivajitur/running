"""
Marathon Training Coach — MCP Server

Exposes Strava running history to Claude via the Model Context Protocol.
Run locally via stdio; add to claude_desktop_config.json to use with Claude Desktop.
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Ensure the project root is on the path so src imports work
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP
from src.data.database import (
    init_db,
    query_activities,
    query_activity_with_details,
    get_summary_stats,
    get_weekly_mileage,
    get_latest_activity_date,
    get_activity_count,
    upsert_activities,
)
from src.data.strava_client import StravaClient
from src.config import Settings

# ---------------------------------------------------------------------------
# Server bootstrap
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="marathon-coach",
    instructions=(
        "You are a marathon training coach with full access to the athlete's "
        "Strava running history. Use the tools below to fetch data before "
        "answering. Always ground your advice in the actual numbers."
    ),
)

# Ensure DB exists on startup
init_db()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _meters_to_miles(m: float) -> float:
    return round(m / 1609.34, 2) if m else 0.0


def _seconds_to_hms(s: int) -> str:
    if not s:
        return "00:00:00"
    h, rem = divmod(int(s), 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


def _pace_str(avg_speed_ms: float) -> str:
    """Convert m/s to min:sec per mile string."""
    if not avg_speed_ms:
        return "N/A"
    miles_per_sec = avg_speed_ms / 1609.34
    min_per_mile = 1 / (miles_per_sec * 60)
    mins = int(min_per_mile)
    secs = int((min_per_mile - mins) * 60)
    return f"{mins}:{secs:02d} /mi"


def _format_activity(a: dict) -> dict:
    """Return a human-friendly version of a raw activity row."""
    return {
        "id": a["id"],
        "name": a["name"],
        "date": (a.get("start_date_local") or "")[:10],
        "type": a["type"],
        "workout_type": a.get("workout_type"),
        "distance_miles": _meters_to_miles(a.get("distance", 0)),
        "moving_time": _seconds_to_hms(a.get("moving_time")),
        "pace": _pace_str(a.get("average_speed", 0)),
        "avg_heartrate": a.get("average_heartrate"),
        "max_heartrate": a.get("max_heartrate"),
        "elev_gain_ft": round((a.get("total_elevation_gain") or 0) * 3.28084, 0),
        "device": a.get("device_name"),
        "pr_count": a.get("pr_count", 0),
    }


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def sync_from_strava(months_back: int = 3) -> str:
    """
    Pull recent activities from Strava and store them in the local database.
    Call this to refresh data before querying if the athlete has run recently.

    Args:
        months_back: How many months of history to fetch (default 3, max 12).
    """
    months_back = min(max(months_back, 1), 12)
    try:
        client = StravaClient()
        activities = client.get_activities(months_back=months_back)
        count = upsert_activities(activities)
        return f"Synced {count} activities from the last {months_back} month(s). Database now has {get_activity_count()} total activities."
    except Exception as e:
        return f"Sync failed: {e}"


@mcp.tool()
def get_recent_runs(limit: int = 10) -> str:
    """
    Return the most recent runs with key stats.

    Args:
        limit: Number of runs to return (default 10, max 50).
    """
    limit = min(max(limit, 1), 50)
    rows = query_activities(activity_type="Run", limit=limit)
    if not rows:
        return "No runs found in the database. Try calling sync_from_strava first."
    formatted = [_format_activity(r) for r in rows]
    return json.dumps(formatted, indent=2)


@mcp.tool()
def get_runs_in_range(start_date: str, end_date: str) -> str:
    """
    Return all runs between two dates.

    Args:
        start_date: ISO date string, e.g. '2025-01-01'
        end_date:   ISO date string, e.g. '2025-03-31'
    """
    rows = query_activities(
        activity_type="Run",
        limit=200,
        start_date=start_date,
        end_date=end_date,
    )
    if not rows:
        return f"No runs found between {start_date} and {end_date}."
    formatted = [_format_activity(r) for r in rows]
    return json.dumps(formatted, indent=2)


@mcp.tool()
def get_long_runs(min_miles: float = 13.0, limit: int = 20) -> str:
    """
    Return runs over a given distance — useful for tracking long run progression.

    Args:
        min_miles: Minimum distance in miles (default 13.0).
        limit:     Max results to return (default 20).
    """
    min_meters = min_miles * 1609.34
    rows = query_activities(
        activity_type="Run",
        limit=limit,
        min_distance_m=min_meters,
    )
    if not rows:
        return f"No runs found over {min_miles} miles."
    formatted = [_format_activity(r) for r in rows]
    return json.dumps(formatted, indent=2)


@mcp.tool()
def get_run_detail(activity_id: int) -> str:
    """
    Return full detail for a single run including splits, cadence, and calories.

    Args:
        activity_id: The Strava activity ID (visible in get_recent_runs output).
    """
    row = query_activity_with_details(activity_id)
    if not row:
        return f"Activity {activity_id} not found."

    result = _format_activity(row)
    result.update({
        "calories": row.get("calories"),
        "suffer_score": row.get("suffer_score"),
        "avg_cadence": row.get("average_cadence"),
        "avg_watts": row.get("average_watts"),
        "description": row.get("description"),
        "splits_metric": json.loads(row["splits_metric"]) if row.get("splits_metric") else None,
    })
    return json.dumps(result, indent=2)


@mcp.tool()
def get_training_summary() -> str:
    """
    Return overall training statistics: total miles, average pace, heart rate trends, etc.
    Good for a high-level picture of the athlete's fitness.
    """
    stats = get_summary_stats(activity_type="Run")
    if not stats or stats.get("total_activities") == 0:
        return "No run data in the database. Try calling sync_from_strava first."

    stats["total_moving_time"] = _seconds_to_hms(stats.pop("total_moving_time_s", 0))
    return json.dumps(stats, indent=2)


@mcp.tool()
def get_weekly_mileage_trend(weeks: int = 12) -> str:
    """
    Return week-by-week mileage for the last N weeks.
    Use this to assess training load, taper, or ramp rate.

    Args:
        weeks: Number of weeks to look back (default 12).
    """
    rows = get_weekly_mileage(weeks=weeks)
    if not rows:
        return "No data available. Try calling sync_from_strava first."
    return json.dumps(rows, indent=2)


@mcp.tool()
def get_db_status() -> str:
    """
    Return the number of stored activities and the date of the most recent one.
    Useful to check if a sync is needed before answering questions.
    """
    count = get_activity_count()
    latest = get_latest_activity_date()
    return json.dumps({
        "total_activities_stored": count,
        "most_recent_activity_date": (latest or "none")[:10],
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
