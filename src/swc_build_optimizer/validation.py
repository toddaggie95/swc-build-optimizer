"""Deterministic geometry validation; deliberately no economic/build approval."""

from dataclasses import dataclass

from .geometry import cells, free_sides, in_bounds
from .models import Catalog, City


@dataclass(frozen=True)
class Issue:
    code: str
    placement_ids: tuple[str, ...]
    message: str


@dataclass(frozen=True)
class ValidationResult:
    issues: tuple[Issue, ...]
    checked: tuple[str, ...] = ("catalog", "bounds", "overlap", "two_free_sides")
    unchecked: tuple[str, ...] = ("power", "terrain", "special_restrictions", "economics")

    @property
    def geometry_valid(self) -> bool:
        return not self.issues


def validate(city: City, catalog: Catalog) -> ValidationResult:
    types = catalog.by_id()
    issues = []
    footprints = {}
    for p in city.placements:
        if p.facility_id not in types:
            issues.append(Issue("unknown_facility", (p.id,), f"Unknown type {p.facility_id}"))
            continue
        footprint = cells(p, types[p.facility_id])
        footprints[p.id] = footprint
        if any(not in_bounds(c, city) for c in footprint):
            issues.append(Issue("out_of_bounds", (p.id,), "Complete footprint must be in bounds"))
    # Access on malformed geometry is misleading. Stop at bounds/catalog failures.
    if issues:
        return ValidationResult(tuple(issues), checked=("catalog", "bounds"))
    for i, a in enumerate(city.placements):
        for b in city.placements[i + 1 :]:
            if footprints[a.id] & footprints[b.id]:
                issues.append(Issue("overlap", (a.id, b.id), "Facility footprints overlap"))
    if issues:
        return ValidationResult(tuple(issues), checked=("catalog", "bounds", "overlap"))
    occupied = set().union(*footprints.values())
    for p in city.placements:
        sides = free_sides(p, types[p.facility_id], city, occupied)
        if len(sides) < 2:
            issues.append(Issue("insufficient_access", (p.id,), f"Only {len(sides)} free sides"))
    return ValidationResult(tuple(issues))
