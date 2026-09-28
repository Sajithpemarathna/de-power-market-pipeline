from datetime import date, datetime, timezone

from ingestion.download_smard import berlin_midnight_ms, download_series
from ingestion.smard_client import chunk_url, index_url
from ingestion.smard_series import SmardSeries


def utc_ms(*args) -> int:
    return int(datetime(*args, tzinfo=timezone.utc).timestamp() * 1000)


def test_berlin_midnight_in_winter_is_23_utc():
    assert berlin_midnight_ms(date(2026, 1, 1)) == utc_ms(2025, 12, 31, 23)


def test_berlin_midnight_in_summer_is_22_utc():
    assert berlin_midnight_ms(date(2026, 7, 1)) == utc_ms(2026, 6, 30, 22)


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class FakeSession:
    """Answers with canned JSON per URL, so tests never touch the network."""

    def __init__(self, payloads):
        self.payloads = payloads

    def get(self, url, timeout):
        return FakeResponse(self.payloads[url])


def test_download_series_builds_raw_rows_and_skips_empty_slots():
    series = SmardSeries(4169, "price_day_ahead", region="DE-LU")
    week_start = berlin_midnight_ms(date(2026, 9, 21))
    quarter = 15 * 60 * 1000
    session = FakeSession(
        {
            index_url(4169, "DE-LU", "quarterhour"): {"timestamps": [week_start]},
            chunk_url(4169, "DE-LU", "quarterhour", week_start): {
                "meta_data": {"version": 1},
                "series": [
                    [week_start, 85.3],
                    [week_start + quarter, -4.9],
                    [week_start + 2 * quarter, None],
                ],
            },
        }
    )

    rows = download_series(
        session, series, week_start, week_start + 3 * quarter, "2026-09-27T10:00:00+00:00"
    )

    assert [(r["timestamp_ms"], r["value"]) for r in rows] == [
        (week_start, 85.3),
        (week_start + quarter, -4.9),
    ]
    assert rows[0]["filter_id"] == 4169
    assert rows[0]["region"] == "DE-LU"
    assert rows[0]["fetched_at"] == "2026-09-27T10:00:00+00:00"
