# City solver contract v0.2

`SolveRequest` and `SolveResult` have committed JSON schemas generated from
`solve_models.py`. The solver uses the same catalog and geometry-v1 rules as the
validator; it does not call the validator as a placement oracle during search.

## Scope and modes

Every input placement is mandatory and retains its identity and facility type.
`fixed` locks all of their coordinates and orientations even if `fixed` metadata
is false. It requires a valid baseline. `free` allows every original placement to
move, even if its metadata says `fixed: true`; `locked_ids` explicitly preserves
selected originals. This override is intentional and requires requesting free mode.
It is appropriate for designing a new city, not moving buildings in a live city.
Invalid original coordinates may be discarded as hints in free mode; an invalid
locked subset is rejected. Removing other rectangles cannot harm free-side access,
so a locked subset already lacking access cannot be repaired by additions.

Each addition entry has one unique catalog facility ID, `min_count` and `max_count`.
The first minimum-count instances are mandatory; remaining instances are optional.
All original inventory is retained. Generated IDs cannot collide with originals.
Oversized optional facilities can be omitted rather than making the model invalid.
An unknown catalog ID is an input error, never a guessed dimension.

`feasibility` has no objective and may stop at any valid inventory within the
requested limits. `max_additions` maximizes the total number of added facilities
within those same limits. It does not maximize income or occupied area, choose
unrequested types, or prove anything about inventories outside those limits.

## Formulation

Each instance has presence, orientation, integer top-left position, right/bottom
edges and four side-selection Booleans. Oriented width and height are affine
expressions of the rotation Boolean. Optional x/y intervals feed NoOverlap2D.
Present instances must be fully in bounds and select at least two free sides.
A selected border-facing side is forbidden by its own in-bounds strip constraint.

For each rectangle pair, eight exactly reified comparisons describe left/right,
above/below, and those same directions with at least one empty cell of separation.
Given non-overlap, A's north strip is clear of B iff B is left, right, below, or
above with a full one-cell gap. Analogous clauses implement the other sides and
both directions of the pair. Clauses apply only to selected sides and present
neighbors. Road strips may overlap other road strips. The side-selection flags
are witnesses, not an exact count of all possible free sides.

Interchangeable unlocked instances of the same catalog type and mandatory/optional
class are ordered by row-major anchor; optional presence is ordered too. This
removes labeling symmetry without removing geometric possibilities. Locked
instances are excluded. Square rotation is normalized only when unlocked.
No restrictions are added from historical hints. `use_hints` and
`symmetry_breaking` can be disabled for experiments.

The independent validator checks the final extracted city. Additional assertions
check original inventory, locked coordinates/orientations and requested counts.
A failed check raises an error; no invalid city is released as a successful result.
The test suite compares tiny free-layout searches with exhaustive enumeration and
pins all 144 in-bounds bar/square configurations on a 4×4 grid to compare the
solver's clauses against both valid and invalid validator outcomes.

## Status and evidence

| Status | Meaning | CLI exit |
| --- | --- | --- |
| FEASIBLE | Independently validated layout; no optimum claimed | 0 |
| PROVEN_OPTIMAL | Addition-count optimum proved for this request | 0 |
| PROVEN_INFEASIBLE | No solution to this request under geometry-v1 | 1 |
| UNKNOWN | No incumbent or infeasibility proof before stopping | 3 |
| MODEL_INVALID | CP-SAT rejected the generated model | 2 |

Input/file errors also exit 2. CP-SAT's raw `OPTIMAL` for a satisfaction problem is
mapped to `FEASIBLE`, not to an optimization claim. The result contains the raw
status as well. `city`, validation and count are null when no solution exists.
Objective, upper bound and gap are populated only for an optimization run with
an incumbent; otherwise they are null. Gap is `(bound-objective)/max(1,abs(objective))`.
For a proven optimum it is zero. Never interpret a missing value as zero.

Results include solver version, seed, workers, hints/symmetry options, geometry rule
version, assumption identifiers and SHA-256 fingerprints of the canonical catalog
and complete request JSON. The saved request and catalog are needed to reproduce a
run. One worker and fixed seed support repeatability; wall-time limits and different
hardware/builds can still affect outcomes. Multiple workers are nondeterministic.

`time_limit_seconds` bounds the CP-SAT search, not Python model building, result
validation or disk I/O. Build, solve and total times are separate. Pairwise access
model size is quadratic in the maximum instance count; this version targets city
scale, not an unbounded planet-sized monolithic solve.

Power, terrain, special rules and economics remain unchecked in every result.
The fixture catalog retains historical-assumption provenance. A geometric witness
is not a current-game construction approval or a claim that the addition earns money.

## Run and consume

```sh
swc-build solve examples/fixed-additions.request.json --output result.json
```

The result's `city` uses the existing City schema. The benchmark script additionally
writes a standalone city file and Designer URL only when a valid solution exists.
It requires a new output directory so a failed/unknown run cannot leave a stale
layout looking like its result. Generic `solve --output` overwrites that result file
and always records the actual status.
