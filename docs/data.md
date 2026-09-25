# Canonical data and assumption policy

Pydantic definitions in `models.py` are the schema source. Run
`python scripts/export_schemas.py` after changing contracts. Each JSON document
has `schema_version: 1`; incompatible future changes require a version/migration
decision. JSON Schema checks shape; runtime validators additionally reject duplicate
facility, placement and assumption IDs. All model collections are immutable tuples.

The packaged `facilities.json` is the only canonical facility catalog. It includes
the nine types in the historical fixture plus the Personal Residence 1×1 probe.
Dimensions and Designer mappings are historical planning assumptions with source
provenance, not an exhaustive freshly verified game database. SWC's current facility
rules endpoint was access-protected during initialization, so no claim of current
catalog verification is made. Unknown IDs fail closed; add a sourced entry explicitly.

`data/assumptions.json` separates user-confirmed planning rules, historical modeling
assumptions, empirical estimates, documented facts and unknowns. Every record carries
source and note, an explicit enabled flag, and optional value/units. Unknown does
not mean zero. `enabled` is scenario/research metadata; it cannot disable a hard
geometry check in this release. Versioned rule profiles may be added later.

The planet scenario is a contract scaffold containing cities, assumption records
and an optional economic model ID. There is no evaluator, no default employment
target, no income prediction and no assumed FIM/MNSF/RNF/SBR equation. Planet area
484 remains disabled pending independent confirmation of its role in formulas.
Power data is also absent rather than silently defaulted to zero consumption.

Future facility extensions should attach per-field provenance for power, jobs,
flats, terrain eligibility and restrictions, with effective date/model version and
uncertainty where applicable. Facility mapping changes require regression review.
Observed game measurements should preserve their context, not masquerade as universal
rules. Do not commit credentials, private exports or player-specific API snapshots.

The Designer codec preserves order/orientation and the `|4|v` state suffix. It uses
standard query decoding and canonical percent-encoded export. It does not fetch
URLs or execute content. `to_url` serializes a 20×20 model, including invalid geometry
for diagnosis; callers must run `validate` before treating exports as proposals.
