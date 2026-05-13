from pathlib import Path
import importlib.util

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "probe_trivago_search.py"
spec = importlib.util.spec_from_file_location("probe_trivago_search", MODULE_PATH)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_normalize_child_ages_parses_csv_and_list_inputs():
    assert probe.normalize_child_ages("10, 7") == [10, 7]
    assert probe.normalize_child_ages([5, "8"]) == [5, 8]
    assert probe.normalize_child_ages("") == []


def test_replace_date_range_rewrites_existing_dr_segment():
    url = "https://www.trivago.com/en-US/lm/hotels-eniwa-japan?search=200-72064;dr-20260522-20260523"
    updated = probe.replace_date_range(url, "2026-06-25", "2026-06-26")
    assert updated.endswith("search=200-72064;dr-20260625-20260626")


def test_replace_date_range_adds_dr_segment_when_missing():
    url = "https://www.trivago.com/en-US/lm/hotels-eniwa-japan?search=200-72064"
    updated = probe.replace_date_range(url, "2026-06-25", "2026-06-26")
    assert updated.endswith("search=200-72064;dr-20260625-20260626")


def test_parse_guest_summary_extracts_guest_counts():
    assert probe.parse_guest_summary("2 Guests, 1 Room") == {
        "guests": 2,
        "rooms": 1,
        "adults": 2,
        "children": 0,
    }
    assert probe.parse_guest_summary("3 Guests, 2 Rooms") == {
        "guests": 3,
        "rooms": 2,
        "adults": 3,
        "children": 0,
    }


def test_build_guest_adjustments_returns_button_click_plan():
    plan = probe.build_guest_adjustments(
        current={"adults": 2, "children": 0, "rooms": 1},
        target={"adults": 3, "children": 1, "rooms": 1},
    )
    assert plan == [
        ("adults-amount-plus-button", 1),
        ("children-amount-plus-button", 1),
    ]

    plan = probe.build_guest_adjustments(
        current={"adults": 4, "children": 2, "rooms": 2},
        target={"adults": 3, "children": 1, "rooms": 1},
    )
    assert plan == [
        ("adults-amount-minus-button", 1),
        ("children-amount-minus-button", 1),
        ("rooms-amount-minus-button", 1),
    ]


def test_build_artifact_stem_includes_occupancy():
    stem = probe.build_artifact_stem(
        destination="Eniwa, Hokkaido, Japan",
        checkin="2026-06-25",
        checkout="2026-06-26",
        adults=3,
        child_ages=[10],
        rooms=2,
    )
    assert stem == "eniwa-hokkaido-japan_2026-06-25_2026-06-26_a3_c1_r2"
