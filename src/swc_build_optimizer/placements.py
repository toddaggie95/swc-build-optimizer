"""Exhaustive single-addition search, not joint or global optimization."""

from .models import Catalog, City, Placement
from .validation import validate


def legal_additions(city: City, catalog: Catalog, facility_id: int) -> tuple[Placement, ...]:
    if not validate(city, catalog).geometry_valid:
        raise ValueError("Cannot enumerate additions to an invalid baseline city")
    facility = catalog.by_id().get(facility_id)
    if facility is None:
        raise ValueError(f"Unknown facility type {facility_id}")
    candidate_id = "addition"
    existing_ids = {p.id for p in city.placements}
    while candidate_id in existing_ids:
        candidate_id += "_"
    orientations = ("v",) if facility.width == facility.height else ("v", "h")
    results = []
    for orientation in orientations:
        for y in range(city.height):
            for x in range(city.width):
                p = Placement(
                    id=candidate_id,
                    facility_id=facility_id,
                    x=x,
                    y=y,
                    orientation=orientation,
                    fixed=False,
                )
                trial = city.model_copy(update={"placements": city.placements + (p,)})
                # Revalidate every existing building as well as the candidate.
                if validate(trial, catalog).geometry_valid:
                    results.append(p)
    return tuple(results)
