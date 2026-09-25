# Architecture and staged delivery

The optimizer is separate from `swc-personal-analytics` (API acquisition and
analytics). Human research/workbooks remain external; exchange versioned JSON
rather than embedding a changing spreadsheet or private game data in this repo.

Intended flow:

```text
catalog + input city / Designer URL
    -> strict canonical model
    -> deterministic validator
    -> candidate placement generator
    -> CP-SAT city solver
    -> city alternative / Pareto pool (future)
    -> planet evaluator and allocation search (future)
    -> economic reevaluation and local improvements (future)
    -> independent final validation
    -> proposal + Designer URL
```

## Implemented: geometry foundation

Pure geometry has no dependency on solver state or economic assumptions. The
canonical catalog is packaged with the library so installed command-line tools
work outside a repository checkout. Models reject unknown fields and coercion;
their generated schemas are committed for other tools. Designer IDs are not API
entity IDs. URL parsing rejects unknown catalog entries instead of inventing sizes.
The state suffix is preserved as opaque metadata and is not a placement.

OR-Tools runs both the dependency smoke test and the actual city solver. The smoke
test remains separate from city search and cannot imply city optimality.

## Implemented: city solver v0.2

Validation, fixed-city addition optimization, and free-layout inventory search are
separate modes. Fixed mode preserves every original coordinate, orientation and
facility; once catalogued, shields receive the same treatment as other facilities.
Free-layout mode uses original placements as optional hints and supports explicit
locked IDs. The implementation uses optional rectangles/NoOverlap2D, reified pairwise
direction/gap relationships for access, and symmetry breaking among interchangeable
unlocked instances. All solutions are independently validated, including preservation
of existing inventory and fixed placements. See [solver contract](solver.md).

The first free-layout question is answered: the exact historical inventory of
29 facilities plus a 1×1 fits. The saved witness passes the validator. A 30-second
single-worker search returned UNKNOWN; an eight-worker run found a solution in
about 34 seconds within a 120-second budget. This is an existence result, not a
proof of the greatest possible count. See [benchmarks](../benchmarks/README.md).

Result contracts include status, objective/bound/gap when applicable, time limit,
build/search/total time, solver version/settings, rule version, catalog/request
fingerprints, assumption IDs and independent validation. Feasibility search does
not claim optimality even when CP-SAT uses its OPTIMAL satisfaction status.

Further solver research: compare a placement-indexed formulation, benchmark
redundant cumulative constraints, add economic values only through an explicit
objective contract, and implement dedicated infeasibility explanations. No
performance claim between unimplemented formulations is made.

## Later: planet feedback loop

Planet targets are priorities, alternatives and marginal values unless explicitly
mandatory. City search generates several efficient alternatives. The planet layer
chooses combinations, recalculates whole-planet consequences, then revises targets.
Do not score a Hotel vs two Garages only by isolated income: power, employment,
flats, ER, crime, saturation, occupied area and preserved geometry can all change
the choice. Extra power generation can unlock value and consumes geometry itself.

Implement economic evaluators as named/versioned models with explicit assumption
sets and uncertainty. Unknown FIM or saturation mechanics must not silently become
hard-coded truth. Avoid one enormous CP-SAT equation for secret/nonlinear economics.
Do not equate occupancy maximization with income maximization.

Test in order: tiny geometry cases, historical layouts, deliberately constructed
planet scenarios with known expected tradeoffs, then real planets (Chamble I was
identified as the initial end-to-end candidate). Synthetic economic fixtures must
be labeled synthetic; no real planet data is seeded here.

## Definition of done for later build-ready output

Expand/snapshot sourced catalog data; validate power, terrain, special restrictions
and explicit reservations; preserve existing facilities; verify URL parity against
the Designer; independently validate solver output; and identify all assumed
economic formulas. This seed intentionally stops before claiming those capabilities.
