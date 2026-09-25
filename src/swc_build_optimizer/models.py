"""Canonical, strict models. JSON schemas are generated from these definitions."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Evidence(Model):
    status: Literal["user_confirmed", "documented", "empirical", "assumption", "unknown"]
    source: str = Field(min_length=1)
    note: str = Field(min_length=1)


class FacilityType(Model):
    id: int = Field(ge=1, description="City Designer ID; not an SWC API entity ID")
    name: str = Field(min_length=1)
    width: int = Field(ge=1, description="Width in vertical (v) orientation")
    height: int = Field(ge=1, description="Height in vertical (v) orientation")
    evidence: Evidence


class Catalog(Model):
    schema_version: Literal[1] = 1
    facilities: tuple[FacilityType, ...]

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [f.id for f in self.facilities]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate facility type IDs")
        return self

    def by_id(self) -> dict[int, FacilityType]:
        return {f.id: f for f in self.facilities}


class Placement(Model):
    id: str = Field(min_length=1)
    facility_id: int = Field(ge=1)
    x: int
    y: int
    orientation: Literal["v", "h"] = "v"
    fixed: bool = True


class City(Model):
    schema_version: Literal[1] = 1
    name: str = Field(min_length=1)
    width: int = Field(default=20, ge=1)
    height: int = Field(default=20, ge=1)
    placements: tuple[Placement, ...] = ()
    designer_state: str = Field(default="", pattern=r"^(\|[^|]*\|[^|]*)?$")
    source_url: str | None = None

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [p.id for p in self.placements]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate placement IDs")
        return self


class Assumption(Model):
    id: str = Field(min_length=1)
    domain: Literal["geometry", "power", "terrain", "economics", "policy"]
    statement: str = Field(min_length=1)
    evidence: Evidence
    enabled: bool = False
    value: float | None = None
    units: str | None = None


class AssumptionSet(Model):
    schema_version: Literal[1] = 1
    assumptions: tuple[Assumption, ...]

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [a.id for a in self.assumptions]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate assumption IDs")
        return self


class PlanetScenario(Model):
    """Data contract only: no implicit economic formulas or default targets."""

    schema_version: Literal[1] = 1
    name: str = Field(min_length=1)
    cities: tuple[City, ...] = ()
    assumptions: AssumptionSet
    economic_model_id: str | None = None
