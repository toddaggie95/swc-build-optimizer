"""Exact rectangle/access CP-SAT model, independently validated before release."""

import hashlib
import itertools
import time
from dataclasses import dataclass

import ortools
from ortools.sat.python import cp_model

from .models import Catalog, City, Placement
from .solve_models import SolveRequest, SolveResult
from .validation import validate


@dataclass
class _Rectangle:
    placement: Placement
    added: bool
    mandatory: bool
    locked: bool
    present: cp_model.IntVar
    rotated: cp_model.IntVar
    x: cp_model.IntVar
    y: cp_model.IntVar
    right: cp_model.IntVar
    bottom: cp_model.IntVar
    sides: dict[str, cp_model.IntVar]


def _fingerprint(value) -> str:
    return hashlib.sha256(value.model_dump_json().encode("utf-8")).hexdigest()


def _less_equal(model, lhs, rhs, name):
    literal = model.new_bool_var(name)
    model.add(lhs <= rhs).only_enforce_if(literal)
    model.add(lhs > rhs).only_enforce_if(literal.Not())
    return literal


def _build(request: SolveRequest, catalog: Catalog):
    model = cp_model.CpModel()
    city = request.city
    types = catalog.by_id()
    unknown = (
        {p.facility_id for p in city.placements} | {a.facility_id for a in request.additions}
    ) - types.keys()
    if unknown:
        raise ValueError(f"Unknown facility types: {sorted(unknown)}")
    if request.mode == "fixed" and not validate(city, catalog).geometry_valid:
        raise ValueError("Fixed mode requires a geometrically valid baseline city")
    locked_ids = (
        {p.id for p in city.placements} if request.mode == "fixed" else set(request.locked_ids)
    )
    # Invalid free-layout hints are allowed, but an invalid locked subset is not.
    locked_city = city.model_copy(
        update={"placements": tuple(p for p in city.placements if p.id in locked_ids)}
    )
    if not validate(locked_city, catalog).geometry_valid:
        raise ValueError("Locked facilities do not form a geometrically valid baseline")
    specs = [(p, False, True, p.id in locked_ids) for p in city.placements]
    used_ids = {p.id for p in city.placements}
    for addition in request.additions:
        for i in range(addition.max_count):
            name = f"add-{addition.facility_id}-{i + 1}"
            while name in used_ids:
                name += "_"
            used_ids.add(name)
            specs.append(
                (
                    Placement(id=name, facility_id=addition.facility_id, x=0, y=0, fixed=False),
                    True,
                    i < addition.min_count,
                    False,
                )
            )
    rectangles, xs, ys = [], [], []
    for p, added, mandatory, locked in specs:
        f = types[p.facility_id]
        prefix = p.id
        present = model.new_bool_var(prefix + ".present")
        if mandatory:
            model.add(present == 1)
        rotated = model.new_bool_var(prefix + ".rotated")
        if f.width == f.height and not locked:
            model.add(rotated == 0)
        width = f.width + (f.height - f.width) * rotated
        height = f.height + (f.width - f.height) * rotated
        x = model.new_int_var(0, city.width - 1, prefix + ".x")
        y = model.new_int_var(0, city.height - 1, prefix + ".y")
        right = model.new_int_var(0, city.width + max(f.width, f.height), prefix + ".right")
        bottom = model.new_int_var(0, city.height + max(f.width, f.height), prefix + ".bottom")
        model.add(right == x + width)
        model.add(bottom == y + height)
        model.add(right <= city.width).only_enforce_if(present)
        model.add(bottom <= city.height).only_enforce_if(present)
        xs.append(model.new_optional_interval_var(x, width, right, present, prefix + ".ix"))
        ys.append(model.new_optional_interval_var(y, height, bottom, present, prefix + ".iy"))
        if locked:
            model.add(x == p.x)
            model.add(y == p.y)
            model.add(rotated == (p.orientation == "h"))
        elif not added and request.use_hints:
            w, h = (f.width, f.height) if p.orientation == "v" else (f.height, f.width)
            if 0 <= p.x <= city.width - w and 0 <= p.y <= city.height - h:
                model.add_hint(x, p.x)
                model.add_hint(y, p.y)
                model.add_hint(rotated, int(p.orientation == "h" and f.width != f.height))
        sides = {
            side: model.new_bool_var(prefix + "." + side)
            for side in ("north", "south", "east", "west")
        }
        for side in sides.values():
            model.add(side <= present)
        model.add(sum(sides.values()) >= 2 * present)
        model.add(y >= 1).only_enforce_if(sides["north"])
        model.add(bottom <= city.height - 1).only_enforce_if(sides["south"])
        model.add(x >= 1).only_enforce_if(sides["west"])
        model.add(right <= city.width - 1).only_enforce_if(sides["east"])
        rectangles.append(
            _Rectangle(p, added, mandatory, locked, present, rotated, x, y, right, bottom, sides)
        )
    model.add_no_overlap_2d(xs, ys)
    for a, b in itertools.combinations(rectangles, 2):
        prefix = a.placement.id + "/" + b.placement.id
        # Relations describe B relative to A. Gaps are one full empty cell.
        left = _less_equal(model, b.right, a.x, prefix + ".left")
        right = _less_equal(model, a.right, b.x, prefix + ".right")
        above = _less_equal(model, b.bottom, a.y, prefix + ".above")
        below = _less_equal(model, a.bottom, b.y, prefix + ".below")
        left_gap = _less_equal(model, b.right + 1, a.x, prefix + ".left_gap")
        right_gap = _less_equal(model, a.right + 1, b.x, prefix + ".right_gap")
        above_gap = _less_equal(model, b.bottom + 1, a.y, prefix + ".above_gap")
        below_gap = _less_equal(model, a.bottom + 1, b.y, prefix + ".below_gap")
        # Given non-overlap, a strip is empty of B iff B is in one of three
        # other directions, or in this direction separated by >= 1 empty cell.
        for rectangle, other, choices in (
            (
                a,
                b,
                {
                    "north": [left, right, below, above_gap],
                    "south": [left, right, above, below_gap],
                    "west": [above, below, right, left_gap],
                    "east": [above, below, left, right_gap],
                },
            ),
            (
                b,
                a,
                {
                    "north": [left, right, above, below_gap],
                    "south": [left, right, below, above_gap],
                    "west": [above, below, left, right_gap],
                    "east": [above, below, right, left_gap],
                },
            ),
        ):
            for side, alternatives in choices.items():
                model.add_bool_or(alternatives).only_enforce_if(
                    [rectangle.sides[side], other.present]
                )
    if request.symmetry_breaking:
        groups = {}
        for r in rectangles:
            if not r.locked:
                groups.setdefault((r.placement.facility_id, r.mandatory), []).append(r)
        for group in groups.values():
            group.sort(key=lambda r: (r.added, r.placement.y, r.placement.x, r.placement.id))
            for a, b in zip(group, group[1:]):
                model.add(a.present >= b.present)
                model.add(a.y * city.width + a.x < b.y * city.width + b.x).only_enforce_if(
                    [a.present, b.present]
                )
    if request.goal == "max_additions":
        model.maximize(sum(r.present for r in rectangles if r.added))
    return model, rectangles


def solve_city(request: SolveRequest, catalog: Catalog) -> SolveResult:
    """Search only the requested inventory; proofs are scoped to geometry-v1."""
    start = time.perf_counter()
    model, rectangles = _build(request, catalog)
    model_error = model.validate()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = request.time_limit_seconds
    solver.parameters.num_search_workers = request.workers
    solver.parameters.random_seed = request.random_seed
    built = time.perf_counter()
    raw = cp_model.MODEL_INVALID if model_error else solver.solve(model)
    solved = time.perf_counter()
    cp_status = solver.status_name(raw)
    status = {
        cp_model.OPTIMAL: "PROVEN_OPTIMAL" if request.goal == "max_additions" else "FEASIBLE",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "PROVEN_INFEASIBLE",
        cp_model.UNKNOWN: "UNKNOWN",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
    }[raw]
    solution = None
    count = objective = bound = gap = geometry_valid = None
    if raw in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        placements = []
        count = 0
        for r in rectangles:
            if solver.boolean_value(r.present):
                count += int(r.added)
                placements.append(
                    r.placement.model_copy(
                        update={
                            "x": solver.value(r.x),
                            "y": solver.value(r.y),
                            "orientation": "h" if solver.boolean_value(r.rotated) else "v",
                        }
                    )
                )
        solution = City(
            name=request.city.name,
            width=request.city.width,
            height=request.city.height,
            placements=tuple(placements),
            designer_state=request.city.designer_state,
        )
        report = validate(solution, catalog)
        if not report.geometry_valid:
            raise RuntimeError(f"Solver produced invalid geometry: {report.issues}")
        by_id = {p.id: p for p in solution.placements}
        for original in request.city.placements:
            if original.id not in by_id or by_id[original.id].facility_id != original.facility_id:
                raise RuntimeError("Solver lost original inventory")
            if (request.mode == "fixed" or original.id in request.locked_ids) and by_id[
                original.id
            ] != original:
                raise RuntimeError("Solver moved a locked placement")
        for addition in request.additions:
            actual = sum(
                p.facility_id == addition.facility_id
                for p in solution.placements
                if p.id not in {q.id for q in request.city.placements}
            )
            if not addition.min_count <= actual <= addition.max_count:
                raise RuntimeError("Solver violated requested addition counts")
        geometry_valid = True
        if request.goal == "max_additions":
            objective = count
            bound = solver.best_objective_bound
            gap = max(0.0, bound - objective) / max(1, abs(objective))
    message = {
        "FEASIBLE": "Independently validated layout found; no optimization proof claimed.",
        "PROVEN_OPTIMAL": "Maximum addition count proved within the requested inventory and geometry rules.",
        "PROVEN_INFEASIBLE": "Requested inventory proved infeasible under the encoded geometry rules.",
        "UNKNOWN": "Search ended without a solution or infeasibility proof.",
        "MODEL_INVALID": model_error or "CP-SAT rejected the model.",
    }[status]
    return SolveResult(
        status=status,
        cp_sat_status=cp_status,
        mode=request.mode,
        goal=request.goal,
        city=solution,
        geometry_valid=geometry_valid,
        additions_placed=count,
        objective_value=objective,
        best_bound=bound,
        relative_gap=gap,
        build_seconds=built - start,
        solve_seconds=solved - built,
        total_seconds=time.perf_counter() - start,
        time_limit_seconds=request.time_limit_seconds,
        workers=request.workers,
        random_seed=request.random_seed,
        use_hints=request.use_hints,
        symmetry_breaking=request.symmetry_breaking,
        solver_version=ortools.__version__,
        catalog_sha256=_fingerprint(catalog),
        request_sha256=_fingerprint(request),
        model_stats=model.model_stats(),
        message=message,
    )


def smoke_check() -> dict:
    model = cp_model.CpModel()
    x = model.new_int_var(0, 2, "x")
    model.maximize(x)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    status = solver.solve(model)
    return {
        "status": solver.status_name(status),
        "objective": solver.objective_value,
        "best_bound": solver.best_objective_bound,
    }
