"""Run from any directory after installing the package."""

import json
from pathlib import Path

from swc_build_optimizer.models import AssumptionSet, Catalog, City, PlanetScenario
from swc_build_optimizer.solve_models import SolveRequest, SolveResult

MODELS = {"catalog": Catalog, "city": City, "assumptions": AssumptionSet, "planet": PlanetScenario}
MODELS.update({"solve-request": SolveRequest, "solve-result": SolveResult})


def schema_for(model):
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", **model.model_json_schema()}


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "schemas"
    target.mkdir(exist_ok=True)
    for name, model in MODELS.items():
        (target / f"{name}.schema.json").write_text(
            json.dumps(schema_for(model), indent=2) + "\n", encoding="utf-8"
        )
