# Geometry contract v1

The authoritative project direction is the supplied planning conversation and
the user's correction that **the border cannot be treated as a road**.
This contract formalizes that interpretation; it does not claim complete parity
with every current SWC construction exception.

Coordinates are integer, zero-based `(x, y)`, x increasing right and y increasing
down. A placement anchors its top-left occupied cell. Catalog width/height describe
`v`; `h` exchanges them. Bounds use the entire oriented rectangle, not its anchor.
The normal Designer grid is 20×20 (0–19). The conversation's 22×22 / 484 figure
concerns planetary area accounting and is never a placement-grid dimension.
Small custom grids exist for tests and cannot be exported as Designer URLs.

For a width `w`, height `h` rectangle at `(x,y)`, the side strips are:

| Side | Cells |
| --- | --- |
| North | `(i, y-1)` for `x <= i < x+w` |
| South | `(i, y+h)` for `x <= i < x+w` |
| West | `(x-1, j)` for `y <= j < y+h` |
| East | `(x+w, j)` for `y <= j < y+h` |

A side is free iff **all** its cells are inside the grid and unoccupied. Never
clip an out-of-grid strip or count it as empty. A single occupied cell blocks the
entire side. Two qualifying sides may be adjacent or opposite. Diagonal cells do
not count. This version imposes no separate global road-connectivity constraint.
That omission is explicit, not evidence that such a rule could never apply.

Validation proceeds through catalog/bounds, then collisions, then access. Earlier
structural failures stop later checks to avoid misleading access diagnoses.
Every issue has a stable code and affected placement IDs. Malformed input (such
as noninteger coordinates, duplicate IDs or unknown fields) fails schema/model
validation first. Negative integer coordinates are accepted as input so the
geometry validator can diagnose out-of-bounds placement.

`legal_additions` enumerates every anchor and distinct orientation, in orientation,
row, column order. It refuses an invalid baseline and rechecks the **whole city**
for each trial. It never moves or mutates existing placements, even when their
`fixed` metadata is false. Square rotations are deduplicated. Results are single
addition alternatives, not a jointly feasible set and not economic recommendations.

## Historical acceptance criterion

`Mine Low ER - 4 Garage + HR50` must reconstruct 29 facilities and 323 occupied
cells, validate under this contract, and return exactly zero 1×1 additions.
The HR50 at `(8,0,v)` already occupies the former mine reservation. Do not create
an additional vacant 5×5 reserve. Zero single-square additions proves saturation
of that **fixed geometry** under this model; no free-layout solver has run.

The validator explicitly leaves power, terrain, special restrictions, facility
exceptions, construction order, ownership and planet economics to future layers.
The `geometry_valid` flag must not be presented as complete build authorization.
