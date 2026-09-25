# Historical HR50 benchmark: fixed saturation, successful repacking

Input: `Mine Low ER - 4 Garage + HR50`, all 29 original facilities, plus one required
Personal Residence (catalog ID 1, 1×1). Rules: geometry-v1, including border-is-not-road.
The original historical fixture and its zero-addition acceptance test remain unchanged.

| Run | Budget / workers | Actual solve time | Result |
| --- | --- | --- | --- |
| [Fixed](hr50-fixed/result.json) | 30s / 1 | ~0.028s | PROVEN_INFEASIBLE |
| [Free, initial](hr50-free-30s/result.json) | 30s / 1 | ~30.012s | UNKNOWN |
| [Free, longer](hr50-free-120s-8workers/result.json) | 120s / 8 | ~34.332s | FEASIBLE |

The longer run found **30 facilities occupying 324 cells**, keeping exactly the
original inventory and adding one 1×1 at `(0,19,v)`. The original facilities move;
this is a design for rearrangement/new construction, not an addition to the
unchanged historical city. Both new and original facilities pass the independent
geometry validator. Power and economics have not been evaluated.

This witness answers the original existence question: **the historical inventory
can be repacked to fit one additional 1×1**. It does not prove 30 is the maximum.
The earlier UNKNOWN run was a timeout, not contradictory evidence of impossibility.

- [Saved solution city](hr50-free-120s-8workers/city.json)
- [SWC Designer URL](hr50-free-120s-8workers/designer-url.txt) (open/copy the URL in this file)
- [Exact request](hr50-free-120s-8workers/request.json)
- [Full result and provenance](hr50-free-120s-8workers/result.json)
- Regression witness: `tests/fixtures/hr50_plus_one_repacked.city.json`

OR-Tools 9.15.6755, seed 0, hints and symmetry breaking enabled. Multiworker output
and timings are not reproducible bit-for-bit; the saved witness itself is stable
and is revalidated by CI without repeating the longer search.

```sh
python scripts/benchmark_historical.py --mode fixed --output-dir work/hr50-fixed
python scripts/benchmark_historical.py --mode free --seconds 120 --workers 8 --output-dir work/hr50-free
```

Use fresh output directories. Requests include the entire input city and result
records fingerprint both request and catalog. This is one measured rectangle-model
benchmark, not a comparison against a placement-indexed solver.
