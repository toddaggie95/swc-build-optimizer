import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from swc_build_optimizer.designer import parse_url, to_url
from swc_build_optimizer.models import AssumptionSet, Catalog, City, Placement, PlanetScenario

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "name,model,example",
    [
        ("catalog", Catalog, "src/swc_build_optimizer/data/facilities.json"),
        ("city", City, "tests/fixtures/mine_low_er_4_garage_hr50.city.json"),
        ("assumptions", AssumptionSet, "data/assumptions.json"),
        ("planet", PlanetScenario, "data/scenarios/empty_planet.json"),
    ],
)
def test_schemas_match_models_and_examples(name, model, example):
    schema = json.loads((ROOT / f"schemas/{name}.schema.json").read_text())
    assert schema == {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **model.model_json_schema(),
    }
    Draft202012Validator.check_schema(schema)
    raw = (ROOT / example).read_text(encoding="utf-8")
    Draft202012Validator(schema).validate(json.loads(raw))
    model.model_validate_json(raw)


@pytest.mark.parametrize(
    "values",
    [
        dict(x=True),
        dict(x=1.2),
        dict(x="1"),
        dict(orientation="q"),
        dict(fixed="false"),
        dict(typo=1),
    ],
)
def test_strict_input(values):
    with pytest.raises(ValidationError):
        Placement(**(dict(id="a", facility_id=1, x=0, y=0) | values))


def test_duplicate_placement_ids_rejected():
    p = Placement(id="same", facility_id=1, x=0, y=0)
    with pytest.raises(ValidationError, match="duplicate"):
        City(name="bad", placements=(p, p))


@pytest.mark.parametrize(
    "code", ["999,0,0,v;|4|v", "1,0,0,q;|4|v", "1,0,v", "1,0,0,v;;", "1,0,0,v;|4|v|unexpected"]
)
def test_malformed_or_unknown_designer_input(catalog, code):
    with pytest.raises(ValueError):
        parse_url("https://www.swcombine.com/citydesigner/?code=" + code, catalog)


def test_url_contract(catalog):
    with pytest.raises(ValueError):
        parse_url("https://example.com/?code=", catalog)
    with pytest.raises(ValueError):
        parse_url("https://www.swcombine.com/citydesigner/?code=&code=", catalog)
    with pytest.raises(ValueError):
        to_url(City(name="tiny", width=3))
    assert not parse_url("https://www.swcombine.com/citydesigner/?code=", catalog).placements


def test_economics_are_not_enabled_by_default():
    assumptions = AssumptionSet.model_validate_json((ROOT / "data/assumptions.json").read_text())
    assert all(
        not a.enabled and a.value is None
        for a in assumptions.assumptions
        if a.domain == "economics"
    )
