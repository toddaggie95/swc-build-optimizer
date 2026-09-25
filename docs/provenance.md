# Planning provenance and regression history

Authoritative design reference supplied by the user:
[SWC Planet/City Planning](chatgpt-conversation://6ab2d99f-e97c-83ea-868f-a8f0c2798c11).
This document records the accepted direction, not every earlier assistant claim.

The exact first of nine Designer URLs was supplied in user turn
`0b050e99-8d65-47f7-8207-23326b009bfb`. It is preserved unmodified in the historical
city fixture's `source_url`, with 29 decoded placements and opaque state `|4|v`.
Expected inventory: 5 Council Flats, 3 Power Generators, 4 Hotels, 4 Offices,
4 Taverns, 4 Garages, 2 Palaces, 2 Skyscraper 100s and 1 High Rise 50.

User correction `a0edb3c9-523e-4d21-b086-032634811eeb` explicitly stated that the
border cannot be treated as a road. Earlier assistant claims of 24 legal 1×1,
9 legal 1×3 and 4 legal 1×5 placements were withdrawn and are **not** acceptance
criteria. The corrected fixed-city result is zero legal 1×1 additions, while
preserving at least two full in-city free sides for every facility.

The source conversation also corrected the placement grid from 22×22 to 20×20,
distinguished fixed-layout saturation from global repacking optimality, separated
this repository from API analytics, and clarified that existing TFF planets already
have shielding. Existing shields are constraints, not a new per-city build target.

The earlier generated handoff Markdown was not exposed as an attachment by the
conversation reader. This seed was reconstructed from the actual retrieved turns
and original URL, not from an invented copy of that handoff.

External implementation references checked during initialization (2026-09-25):

- [SWC City Designer](https://www.swcombine.com/citydesigner/) exposes the two-sides
  free check. This alone does not establish every rule or exception.
- [OR-Tools Python installation](https://developers.google.com/optimization/install/python)
  documents the supported pip installation route.
- [OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver)
  is the planned city constraint-solver backend. The seed only smoke-tests it.

The regression tests independently reproduce the corrected result from the saved
coordinates. They do not prove equivalence to all SWC build mechanics or optimality
across alternate arrangements.
