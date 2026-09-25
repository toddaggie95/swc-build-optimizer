"""Compare CP-SAT with exhaustive search through the independent validator."""

import itertools

import pytest
from pydantic import ValidationError

from swc_build_optimizer.models import City, Placement
from swc_build_optimizer.solve_models import AdditionRequest, SolveRequest
from swc_build_optimizer.solver import solve_city
from swc_build_optimizer.validation import validate


def placement(name, x=0, y=0, facility_id=1, orientation="v", fixed=True):
    return Placement(
        id=name, facility_id=facility_id, x=x, y=y, orientation=orientation, fixed=fixed
    )


def brute_force(city, catalog, inventory):
    """Tiny-grid reference: no solver constraints or solver geometry helpers."""
    choices = []
    for i, fid in enumerate(inventory):
        f = catalog.by_id()[fid]
        choices.append(
            [
                placement(f"new-{i}", x, y, fid, orientation)
                for orientation in (("v",) if f.width == f.height else ("v", "h"))
                for x in range(city.width)
                for y in range(city.height)
            ]
        )
    for trial in itertools.product(*choices):
        if validate(
            city.model_copy(update={"placements": city.placements + trial}), catalog
        ).geometry_valid:
            return True
    return False


@pytest.mark.parametrize("inventory", [(1,), (2,), (1, 1), (1, 2), (2, 2), (1, 1, 1, 1)])
@pytest.mark.parametrize("symmetry", [False, True])
def test_tiny_free_layout_matches_exhaustive_search(catalog, inventory, symmetry):
    empty = City(name="tiny", width=3, height=3)
    expected = brute_force(empty, catalog, inventory)
    city = empty.model_copy(
        update={
            "placements": tuple(
                placement(f"p{i}", facility_id=fid) for i, fid in enumerate(inventory)
            )
        }
    )
    # All anchors intentionally overlap: they are hints, not fixed constraints.
    result = solve_city(SolveRequest(city=city, mode="free", symmetry_breaking=symmetry), catalog)
    assert (result.status == "FEASIBLE") is expected
    assert result.status in ("FEASIBLE", "PROVEN_INFEASIBLE")
    if result.city:
        assert validate(result.city, catalog).geometry_valid
        assert result.objective_value is None
        assert result.best_bound is None


def test_fixed_search_matches_bruteforce_maximum(catalog):
    city = City(name="fixed", width=3, height=3, placements=(placement("original", fixed=False),))
    expected = max(n for n in range(4) if brute_force(city, catalog, (1,) * n))
    result = solve_city(
        SolveRequest(
            city=city,
            goal="max_additions",
            additions=(AdditionRequest(facility_id=1, max_count=3),),
        ),
        catalog,
    )
    assert result.status == "PROVEN_OPTIMAL"
    assert result.additions_placed == result.objective_value == expected
    assert result.best_bound == expected
    assert result.relative_gap == 0
    assert result.city.placements[0] == city.placements[0]


def test_full_side_strip_and_border_are_enforced(catalog):
    # A vertical 1x3 at x=0 spans all rows: west is a border, only east is free.
    city = City(
        name="no border road", width=3, height=3, placements=(placement("bar", facility_id=2),)
    )
    with pytest.raises(ValueError, match="baseline"):
        solve_city(SolveRequest(city=city), catalog)
    free = solve_city(SolveRequest(city=city, mode="free"), catalog)
    assert free.status == "FEASIBLE"
    assert validate(free.city, catalog).geometry_valid


def test_fixed_rotation_and_explicit_free_locks(catalog):
    p = placement("bar", 1, 1, 2, "h")
    city = City(name="locked", width=5, height=4, placements=(p,))
    result = solve_city(
        SolveRequest(
            city=city,
            mode="free",
            locked_ids=("bar",),
            additions=(AdditionRequest(facility_id=1, min_count=1, max_count=1),),
        ),
        catalog,
    )
    assert result.status == "FEASIBLE"
    assert result.city.placements[0] == p


def test_square_locked_orientation_is_preserved(catalog):
    city = City(
        name="square orientation",
        width=3,
        height=3,
        placements=(placement("square", orientation="h"),),
    )
    result = solve_city(SolveRequest(city=city), catalog)
    assert result.city.placements == city.placements


def test_oversized_optional_facility_does_not_make_model_infeasible(catalog):
    result = solve_city(
        SolveRequest(
            city=City(name="tiny", width=3, height=3),
            goal="max_additions",
            additions=(AdditionRequest(facility_id=7, max_count=1),),
        ),
        catalog,
    )
    assert result.status == "PROVEN_OPTIMAL"
    assert result.additions_placed == 0


def test_oversized_required_facility_is_infeasible(catalog):
    result = solve_city(
        SolveRequest(
            city=City(name="tiny", width=3, height=3),
            additions=(AdditionRequest(facility_id=7, min_count=1, max_count=1),),
        ),
        catalog,
    )
    assert result.status == "PROVEN_INFEASIBLE"
    assert result.city is None
    assert result.geometry_valid is None
    assert result.objective_value is None
    assert result.best_bound is None


def test_historical_fixed_proves_zero_additions(historical, catalog):
    result = solve_city(
        SolveRequest(
            city=historical,
            goal="max_additions",
            additions=(AdditionRequest(facility_id=1, max_count=1),),
        ),
        catalog,
    )
    assert result.status == "PROVEN_OPTIMAL"
    assert result.additions_placed == 0
    assert result.city.placements == historical.placements
    result = solve_city(
        SolveRequest(
            city=historical, additions=(AdditionRequest(facility_id=1, min_count=1, max_count=1),)
        ),
        catalog,
    )
    assert result.status == "PROVEN_INFEASIBLE"


def test_timeout_is_not_infeasibility(historical, catalog):
    result = solve_city(
        SolveRequest(
            city=historical,
            mode="free",
            time_limit_seconds=1e-9,
            additions=(AdditionRequest(facility_id=1, min_count=1, max_count=1),),
        ),
        catalog,
    )
    assert result.status == "UNKNOWN"
    assert result.city is None
    assert result.best_bound is None


def test_no_solution_extraction_without_independent_validation(catalog, monkeypatch):
    from swc_build_optimizer import solver
    from swc_build_optimizer.validation import Issue, ValidationResult

    actual = solver.validate
    calls = 0

    def reject_result(city, catalog):
        nonlocal calls
        calls += 1
        if calls <= 2:
            return actual(city, catalog)
        return ValidationResult((Issue("test_failure", (), "validator rejected result"),))

    monkeypatch.setattr(solver, "validate", reject_result)
    with pytest.raises(RuntimeError, match="invalid geometry"):
        solve_city(SolveRequest(city=City(name="empty")), catalog)


def test_unknown_facility_fails_closed(catalog):
    with pytest.raises(ValueError, match="Unknown facility"):
        solve_city(
            SolveRequest(
                city=City(name="empty"), additions=(AdditionRequest(facility_id=999, max_count=1),)
            ),
            catalog,
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(time_limit_seconds=0.0),
        dict(time_limit_seconds=float("inf")),
        dict(workers=0),
        dict(locked_ids=("missing",)),
    ],
)
def test_bad_options_rejected(kwargs):
    with pytest.raises(ValidationError):
        SolveRequest(city=City(name="empty"), **kwargs)


def test_bad_counts_rejected():
    with pytest.raises(ValidationError):
        AdditionRequest(facility_id=1, min_count=2, max_count=1)


def test_result_provenance_and_reproducibility(catalog):
    request = SolveRequest(
        city=City(name="tiny", width=3, height=3),
        additions=(AdditionRequest(facility_id=1, min_count=2, max_count=2),),
    )
    a, b = solve_city(request, catalog), solve_city(request, catalog)
    assert a.city == b.city
    assert a.request_sha256 == b.request_sha256
    assert len(a.catalog_sha256) == 64
    assert a.solver_version
    assert a.rules_version == "geometry-v1"
    assert "economics" in a.unchecked
    assert a.total_seconds >= a.solve_seconds >= 0


def test_every_two_rectangle_configuration_matches_validator(catalog):
    """Pin variables after model construction, bypassing baseline pre-validation.

    This checks rejected layouts too, catching overconstraints as well as false
    positives in every directional access clause, with both bar orientations.
    """
    from ortools.sat.python import cp_model

    from swc_build_optimizer.models import Catalog, Evidence, FacilityType
    from swc_build_optimizer.solver import _build

    catalog = Catalog(
        facilities=catalog.facilities
        + (
            FacilityType(
                id=900,
                name="Synthetic square",
                width=2,
                height=2,
                evidence=Evidence(
                    status="assumption", source="unit-test", note="Synthetic footprint"
                ),
            ),
        )
    )
    for orientation, bx, by, sx, sy in itertools.product(
        ("v", "h"), range(4), range(4), range(3), range(3)
    ):
        if (orientation == "v" and by > 1) or (orientation == "h" and bx > 1):
            continue
        city = City(
            name="pair",
            width=4,
            height=4,
            placements=(placement("bar", bx, by, 2, orientation), placement("square", sx, sy, 900)),
        )
        expected = validate(city, catalog).geometry_valid
        model, rectangles = _build(
            SolveRequest(city=city, mode="free", use_hints=False, symmetry_breaking=False), catalog
        )
        for rectangle, p in zip(rectangles, city.placements):
            model.add(rectangle.x == p.x)
            model.add(rectangle.y == p.y)
            model.add(rectangle.rotated == int(p.orientation == "h"))
        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 1
        status = solver.solve(model)
        assert status in (cp_model.OPTIMAL, cp_model.INFEASIBLE)
        assert (status == cp_model.OPTIMAL) is expected, city


def test_historical_free_inventory_can_recover_known_solution(historical, catalog):
    result = solve_city(
        SolveRequest(city=historical, mode="free", time_limit_seconds=15.0), catalog
    )
    assert result.status == "FEASIBLE"
    assert len(result.city.placements) == 29


def test_generated_ids_cannot_replace_existing_inventory(catalog):
    city = City(name="ID collision", width=4, height=4, placements=(placement("add-1-1"),))
    result = solve_city(
        SolveRequest(
            city=city, additions=(AdditionRequest(facility_id=1, min_count=1, max_count=1),)
        ),
        catalog,
    )
    assert {p.id for p in result.city.placements} == {"add-1-1", "add-1-1_"}
