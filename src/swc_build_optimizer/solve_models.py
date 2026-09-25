"""Versioned city-search inputs and evidence-bearing results."""

from typing import Literal

from pydantic import Field, model_validator

from .models import City, Model


class AdditionRequest(Model):
    facility_id: int = Field(ge=1)
    min_count: int = Field(default=0, ge=0)
    max_count: int = Field(ge=0)

    @model_validator(mode="after")
    def ordered_counts(self):
        if self.min_count > self.max_count:
            raise ValueError("min_count must not exceed max_count")
        return self


class SolveRequest(Model):
    schema_version: Literal[1] = 1
    city: City
    mode: Literal["fixed", "free"] = "fixed"
    goal: Literal["feasibility", "max_additions"] = "feasibility"
    additions: tuple[AdditionRequest, ...] = ()
    locked_ids: tuple[str, ...] = ()
    time_limit_seconds: float = Field(default=30.0, gt=0, allow_inf_nan=False)
    workers: int = Field(default=1, ge=1, le=32)
    random_seed: int = Field(default=0, ge=0, le=2147483647)
    use_hints: bool = True
    symmetry_breaking: bool = True

    @model_validator(mode="after")
    def unique_references(self):
        types = [a.facility_id for a in self.additions]
        if len(types) != len(set(types)):
            raise ValueError("Use one addition request per facility type")
        if len(self.locked_ids) != len(set(self.locked_ids)):
            raise ValueError("Duplicate locked_ids")
        if set(self.locked_ids) - {p.id for p in self.city.placements}:
            raise ValueError("locked_ids must identify existing placements")
        return self


class SolveResult(Model):
    schema_version: Literal[1] = 1
    status: Literal["FEASIBLE", "PROVEN_OPTIMAL", "PROVEN_INFEASIBLE", "UNKNOWN", "MODEL_INVALID"]
    cp_sat_status: str
    mode: Literal["fixed", "free"]
    goal: Literal["feasibility", "max_additions"]
    scope: Literal["geometry_only"] = "geometry_only"
    city: City | None = None
    geometry_valid: bool | None = None
    additions_placed: int | None = None
    objective_value: int | None = None
    best_bound: float | None = None
    relative_gap: float | None = None
    build_seconds: float
    solve_seconds: float
    total_seconds: float
    time_limit_seconds: float
    workers: int
    random_seed: int
    use_hints: bool
    symmetry_breaking: bool
    solver_version: str
    rules_version: Literal["geometry-v1"] = "geometry-v1"
    catalog_sha256: str
    request_sha256: str
    assumption_ids: tuple[str, ...] = ("border-is-not-road", "placement-grid")
    unchecked: tuple[str, ...] = ("power", "terrain", "special_restrictions", "economics")
    model_stats: str
    message: str
