"""Download SMARD series for a date range and save one CSV per series.

Example:
    python -m ingestion.download_smard --start 2026-09-14 --end 2026-09-21

Dates are calendar days in German time. The end date is not included.
"""

import argparse
import csv
import logging
import time
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from ingestion.smard_client import (
    clean_points,
    fetch_chunk,
    fetch_chunk_starts,
    make_session,
    select_chunks,
)
from ingestion.smard_series import RESOLUTION, SERIES, SmardSeries

BERLIN = ZoneInfo("Europe/Berlin")
PAUSE_SECONDS = 0.2  # short break between requests so we go easy on the server
CSV_COLUMNS = ["filter_id", "region", "resolution", "timestamp_ms", "value", "fetched_at"]

log = logging.getLogger(__name__)


def berlin_midnight_ms(day: date) -> int:
    """Epoch milliseconds of 00:00 German time on the given day."""
    midnight = datetime(day.year, day.month, day.day, tzinfo=BERLIN)
    return int(midnight.timestamp() * 1000)


def download_series(
    session, series: SmardSeries, start_ms: int, end_ms: int, fetched_at: str
) -> list[dict]:
    """All non-empty points of one series in the range, as raw rows."""
    chunk_starts = fetch_chunk_starts(session, series.filter_id, series.region, RESOLUTION)
    rows = []
    for chunk_start in select_chunks(chunk_starts, start_ms, end_ms):
        points = fetch_chunk(session, series.filter_id, series.region, RESOLUTION, chunk_start)
        for timestamp_ms, value in clean_points(points, start_ms, end_ms):
            rows.append(
                {
                    "filter_id": series.filter_id,
                    "region": series.region,
                    "resolution": RESOLUTION,
                    "timestamp_ms": timestamp_ms,
                    "value": value,
                    "fetched_at": fetched_at,
                }
            )
        time.sleep(PAUSE_SECONDS)
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download SMARD time series to CSV files.")
    parser.add_argument(
        "--start", type=date.fromisoformat, required=True, help="first day (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end", type=date.fromisoformat, required=True, help="day after the last day (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--out", type=Path, default=Path("data/smard"), help="output folder (default: data/smard)"
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    if args.end <= args.start:
        raise SystemExit("--end must be later than --start")

    start_ms = berlin_midnight_ms(args.start)
    end_ms = berlin_midnight_ms(args.end)
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    session = make_session()

    for series in SERIES:
        rows = download_series(session, series, start_ms, end_ms, fetched_at)
        write_csv(rows, args.out / f"{series.name}.csv")
        if rows:
            log.info("%s: %d rows", series.name, len(rows))
        else:
            log.warning("%s: no data in this range", series.name)


if __name__ == "__main__":
    main()
