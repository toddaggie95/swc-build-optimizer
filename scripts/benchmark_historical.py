"""Reproduce the fixed or free HR50 + one 1x1 feasibility benchmark."""

import argparse
from pathlib import Path

from swc_build_optimizer.catalog import load_catalog
from swc_build_optimizer.designer import to_url
from swc_build_optimizer.models import City
from swc_build_optimizer.solve_models import AdditionRequest, SolveRequest
from swc_build_optimizer.solver import solve_city


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("fixed", "free"), default="free")
    parser.add_argument("--seconds", type=float, default=30.0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    city = City.model_validate_json(
        (root / "tests/fixtures/mine_low_er_4_garage_hr50.city.json").read_text(encoding="utf-8")
    )
    request = SolveRequest(
        city=city,
        mode=args.mode,
        time_limit_seconds=args.seconds,
        workers=args.workers,
        additions=(AdditionRequest(facility_id=1, min_count=1, max_count=1),),
    )
    # A separate directory per run prevents confusing old solution files with a timeout.
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "request.json").write_text(
        request.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    result = solve_city(request, load_catalog())
    (args.output_dir / "result.json").write_text(
        result.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    if result.city:
        (args.output_dir / "city.json").write_text(
            result.city.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        (args.output_dir / "designer-url.txt").write_text(
            to_url(result.city) + "\n", encoding="utf-8"
        )
    print(f"{result.status}: {result.message}")
    print(f"Build {result.build_seconds:.3f}s; solve {result.solve_seconds:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
