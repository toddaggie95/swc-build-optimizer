import json
from collections import Counter
from pathlib import Path

from swc_build_optimizer.designer import parse_url, to_url
from swc_build_optimizer.geometry import cells
from swc_build_optimizer.placements import legal_additions
from swc_build_optimizer.validation import validate


def test_exact_historical_reconstruction_and_saturation(historical, catalog):
    expected = json.loads(
        (Path(__file__).parent / "fixtures/mine_low_er_4_garage_hr50.expected.json").read_text()
    )
    assert parse_url(historical.source_url, catalog, name=historical.name) == historical
    assert len(historical.placements) == expected["facility_count"] == 29
    assert Counter(str(p.facility_id) for p in historical.placements) == expected["inventory"]
    assert all(p.fixed for p in historical.placements)
    assert historical.designer_state == "|4|v"
    occupied = set().union(
        *(cells(p, catalog.by_id()[p.facility_id]) for p in historical.placements)
    )
    assert len(occupied) == expected["occupied_cells"] == 323
    assert validate(historical, catalog).geometry_valid is expected["geometry_valid"]
    assert len(legal_additions(historical, catalog, 1)) == expected["legal_single_additions"] == 0
    assert expected["global_repacking_status"] == "not_tested"


def test_designer_round_trip(historical, catalog):
    restored = parse_url(to_url(historical), catalog)
    assert restored.placements == historical.placements
    assert restored.designer_state == historical.designer_state
