"""
services/api_service.py
------------------------
Thin wrapper around the Cricbuzz Cricket API (hosted on RapidAPI).

Handles:
  - authentication headers
  - retries with exponential backoff
  - JSON parsing / error normalization
  - a graceful "not configured" mode so the rest of the app can render
    placeholder UI instead of crashing when no API key is present yet.

Every public function returns a plain Python dict/list (already
JSON-decoded) or raises ApiError, so callers never touch `requests`
objects directly.
"""

import time
import requests

import config


class ApiError(Exception):
    """Raised for any Cricbuzz API failure (network, HTTP, or parsing)."""


def _get(endpoint: str, params: dict | None = None, retries: int = 3, timeout: int = 8) -> dict:
    if not config.API_CONFIGURED:
        raise ApiError(
            "No Cricbuzz API key configured. Add CRICBUZZ_API_KEY to your .env file "
            "(see .env.example) to enable live data."
        )

    url = f"{config.CRICBUZZ_BASE_URL}{endpoint}"
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=config.CRICBUZZ_HEADERS, params=params, timeout=timeout)
            if resp.status_code == 429:
                # rate-limited -- back off and retry
                time.sleep(1.5 * attempt)
                last_error = ApiError("Rate limited by Cricbuzz API (429). Retrying...")
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            last_error = ApiError(f"Cricbuzz API request failed: {e}")
            time.sleep(0.8 * attempt)

    raise last_error


# ---------------------------------------------------------------------------
# Public endpoint wrappers
# ---------------------------------------------------------------------------
def get_live_matches() -> dict:
    """Current live matches across all formats."""
    return _get("/matches/v1/live")


def get_recent_matches() -> dict:
    """Recently completed matches."""
    return _get("/matches/v1/recent")


def get_upcoming_matches() -> dict:
    """Upcoming scheduled matches."""
    return _get("/matches/v1/upcoming")


def get_match_scorecard(match_id: int) -> dict:
    """Full scorecard for a given match id."""
    return _get(f"/mcenter/v1/{match_id}/scard")


def get_icc_rankings(format_type: str = "batsmen", category: str = "men", match_format: str = "test") -> dict:
    """
    ICC player rankings.
    format_type:  'batsmen' | 'bowlers' | 'allrounders'
    category:     'men' | 'women'
    match_format: 'test' | 'odi' | 't20'
    """
    params = {
        "formatType": match_format,
        "isWomen": "1" if category == "women" else "0",
    }
    return _get(f"/stats/v1/rankings/{format_type}", params=params)


def get_series_list(year: int | None = None) -> dict:
    """International series, optionally filtered by year."""
    endpoint = "/series/v1/international" if year is None else f"/series/v1/archives/international/{year}"
    return _get(endpoint)


def search_players(name: str) -> dict:
    """Search players by name."""
    return _get("/stats/v1/player/search", params={"plrN": name})
