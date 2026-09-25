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
    -> CP-SAT city solver (future)
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

OR-Tools is installed as a dependency and exercised by a real, deterministic
one-worker CP-SAT solve. That test is deliberately not a city solver.

## Next: city solver v0.2

Support validation, fixed-city addition optimization, and free-layout inventory
search as separate modes. Fixed mode must preserve every original coordinate,
orientation and facility; existing shields are immovable like other facilities.
Free-layout mode may use historical placements as hints, never as extra constraints
unless requested. Benchmark placement-indexed Boolean candidates against native
optional rectangles/NoOverlap2D; consider redundant cumulative constraints and
symmetry breaking based on measured results. Access constraints must match the
deterministic validator, including damage to existing facilities.

The first free-layout question is whether the exact historical inventory of
29 facilities plus a 1×1 can fit. It remains unanswered. A time limit or failed
search does not prove infeasibility. Keep feasibility explanation (assumption
cores) separate from economic objective optimization.

Future result contracts must include status, objective, bound, gap (when defined),
time limit, elapsed time, solver version/parameters, rule/catalog versions,
assumption IDs and independent validation. Distinguish VALID_ONLY, FEASIBLE or
BEST_FOUND, PROVEN_OPTIMAL, PROVEN_INFEASIBLE, UNKNOWN and MODEL_INVALID. Report
proofs only under the encoded rules and searched problem scope.

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
