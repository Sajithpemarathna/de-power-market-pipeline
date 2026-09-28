from ingestion.smard_client import chunk_url, clean_points, index_url, select_chunks

WEEK_MS = 7 * 24 * 60 * 60 * 1000


def test_index_url():
    assert index_url(410, "DE", "quarterhour") == (
        "https://www.smard.de/app/chart_data/410/DE/index_quarterhour.json"
    )


def test_chunk_url_repeats_filter_and_region():
    assert chunk_url(4169, "DE-LU", "quarterhour", 1789941600000) == (
        "https://www.smard.de/app/chart_data/4169/DE-LU/4169_DE-LU_quarterhour_1789941600000.json"
    )


def test_select_chunks_returns_only_overlapping_weeks():
    starts = [0, WEEK_MS, 2 * WEEK_MS, 3 * WEEK_MS]
    selected = select_chunks(starts, start_ms=WEEK_MS + 1, end_ms=2 * WEEK_MS + 1)
    assert selected == [WEEK_MS, 2 * WEEK_MS]


def test_select_chunks_treats_last_chunk_as_open_ended():
    starts = [0, WEEK_MS]
    selected = select_chunks(starts, start_ms=5 * WEEK_MS, end_ms=6 * WEEK_MS)
    assert selected == [WEEK_MS]


def test_clean_points_drops_nulls_and_points_outside_range():
    points = [[1000, 10.5], [2000, None], [3000, -3.2], [4000, 7.0]]
    assert clean_points(points, start_ms=1000, end_ms=4000) == [(1000, 10.5), (3000, -3.2)]
