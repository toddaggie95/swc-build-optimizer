# SWC Build Optimizer

Optimization tools for Star Wars Combine city layouts and eventual planet-wide
facility planning. This initial release provides **deterministic geometry**, a
curated catalog, versioned schemas, City Designer URL import/export, and an
OR-Tools CP-SAT dependency smoke test. It does not yet optimize cities or score
planet economics.

## Run it

Python 3.11 or newer; Python 3.11/3.12 are covered by the CI configuration.

```sh
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell, instead:
# .\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q
swc-build validate tests/fixtures/mine_low_er_4_garage_hr50.city.json
swc-build additions tests/fixtures/mine_low_er_4_garage_hr50.city.json --facility-id 1
swc-build solver-smoke
```

If PowerShell activation is unavailable, call `.venv\Scripts\python.exe` and
`.venv\Scripts\swc-build.exe` directly. No game login or API credentials are needed.
The historical fixture should report `geometry_valid: true`, zero additions, and
the separate solver smoke test should report `OPTIMAL` with objective/bound 2.
That `OPTIMAL` applies only to a tiny dependency check, never to the historical city.

## Implemented rules and limits

- Placement grid: 20×20, zero-based coordinates; full footprints must fit.
- No overlapping facility footprints; `v` uses catalog dimensions, `h` swaps them.
- Every building needs at least two completely unoccupied adjacent side strips.
  **City borders are not roads.** Every cell in a qualifying strip must be in bounds.
- Every proposed addition revalidates access for every existing facility.
- Validation reports geometry only. Power, terrain, special restrictions and
  economics are explicitly unchecked. An empty cell is not necessarily buildable.
- Additions are individual alternatives; they are not guaranteed mutually compatible.

The **Mine Low ER - 4 Garage + HR50** fixture preserves the exact user-supplied URL,
29 placements, orientation, inventory and Designer state. Its fixed layout is
saturated under these rules. Global repacking optimality is **unknown**.

## Project map

| Path | Purpose |
| --- | --- |
| `src/swc_build_optimizer/` | Strict models, geometry, validation, additions, URL codec, CLI |
| `src/swc_build_optimizer/data/facilities.json` | Single packaged canonical facility subset |
| `schemas/` | Generated JSON Schema contracts, version 1 |
| `data/assumptions.json` | Evidence and uncertainty register; no speculative economic defaults |
| `data/scenarios/` | Planet input scaffold, without an economic implementation |
| `tests/fixtures/` | Historical layout and independent expected regression facts |
| `docs/` | Rules, provenance, architecture and next milestones |

Read [geometry rules](docs/geometry.md), [architecture and roadmap](docs/architecture.md),
[data and assumptions](docs/data.md), and [historical provenance](docs/provenance.md).

## Development

```sh
python scripts/export_schemas.py
python -m ruff check .
python -m pytest -q
```

Schemas are generated from the Pydantic models; tests detect drift and validate
every canonical example. Dependency ranges live in `pyproject.toml`;
`constraints-tested.txt` captures the tested Python 3.12 Windows environment.
To reproduce those versions on Python 3.12, install with
`python -m pip install -c constraints-tested.txt -e ".[dev]"`.
The constraints file is a tested snapshot, not a universal cross-platform lock.

Use [OR-Tools' installation guidance](https://developers.google.com/optimization/install/python)
for platform-specific prerequisites. API/data acquisition remains the responsibility
of `swc-personal-analytics`; this repository consumes explicit data contracts.
