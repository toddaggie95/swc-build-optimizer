from pathlib import Path

import pytest

from swc_build_optimizer.catalog import load_catalog
from swc_build_optimizer.models import City

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def catalog():
    return load_catalog()


@pytest.fixture
def historical():
    return City.model_validate_json(
        (ROOT / "tests/fixtures/mine_low_er_4_garage_hr50.city.json").read_text(encoding="utf-8")
    )
