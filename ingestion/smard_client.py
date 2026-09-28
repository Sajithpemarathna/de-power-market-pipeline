"""Small client for the SMARD chart data API (Bundesnetzagentur).

SMARD serves plain JSON files. Each series has an index file with the start
times of all weekly chunks, and one file per week with the values.

Data: Bundesnetzagentur | SMARD.de, licensed under CC BY 4.0.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

BASE_URL = "https://www.smard.de/app/chart_data"
TIMEOUT_SECONDS = 30


def make_session() -> requests.Session:
    """HTTP session that retries a few times on rate limits and server errors."""
    retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = "de-power-market-pipeline (portfolio project)"
    return session


def index_url(filter_id: int, region: str, resolution: str) -> str:
    return f"{BASE_URL}/{filter_id}/{region}/index_{resolution}.json"


def chunk_url(filter_id: int, region: str, resolution: str, chunk_start_ms: int) -> str:
    # SMARD wants the filter and region twice: in the folder and in the file name.
    file_name = f"{filter_id}_{region}_{resolution}_{chunk_start_ms}.json"
    return f"{BASE_URL}/{filter_id}/{region}/{file_name}"


def _get_json(session, url: str) -> dict:
    response = session.get(url, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def fetch_chunk_starts(session, filter_id: int, region: str, resolution: str) -> list[int]:
    """Start times (epoch ms) of all weekly chunks, oldest first."""
    payload = _get_json(session, index_url(filter_id, region, resolution))
    return sorted(payload["timestamps"])


def fetch_chunk(
    session, filter_id: int, region: str, resolution: str, chunk_start_ms: int
) -> list[list]:
    """Raw points of one week as [[timestamp_ms, value], ...]. Value can be None."""
    payload = _get_json(session, chunk_url(filter_id, region, resolution, chunk_start_ms))
    return payload["series"]


def select_chunks(chunk_starts: list[int], start_ms: int, end_ms: int) -> list[int]:
    """Chunks that overlap the range [start_ms, end_ms).

    A chunk runs until the next one starts. Weeks with a clock change are an
    hour shorter or longer, so we don't assume a fixed chunk length.
    """
    chunk_starts = sorted(chunk_starts)
    selected = []
    for i, chunk_start in enumerate(chunk_starts):
        is_last = i == len(chunk_starts) - 1
        chunk_end = float("inf") if is_last else chunk_starts[i + 1]
        if chunk_start < end_ms and chunk_end > start_ms:
            selected.append(chunk_start)
    return selected


def clean_points(points: list[list], start_ms: int, end_ms: int) -> list[tuple[int, float]]:
    """Drop empty slots and points outside [start_ms, end_ms).

    SMARD uses null for slots without data, for example the rest of the
    current week. Real gaps get caught later by the completeness tests.
    """
    return [
        (timestamp_ms, value)
        for timestamp_ms, value in points
        if value is not None and start_ms <= timestamp_ms < end_ms
    ]
