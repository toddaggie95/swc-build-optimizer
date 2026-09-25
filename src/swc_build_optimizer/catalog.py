from importlib.resources import files

from .models import Catalog


def load_catalog() -> Catalog:
    return Catalog.model_validate_json(
        files("swc_build_optimizer").joinpath("data/facilities.json").read_text(encoding="utf-8")
    )
