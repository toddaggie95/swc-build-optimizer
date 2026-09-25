import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .catalog import load_catalog
from .models import City
from .placements import legal_additions
from .validation import validate


def main() -> int:
    parser = argparse.ArgumentParser(description="SWC geometry tools (not full build approval)")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "additions"):
        command = sub.add_parser(name)
        command.add_argument("city", type=Path)
        if name == "additions":
            command.add_argument("--facility-id", type=int, required=True)
    sub.add_parser("solver-smoke")
    args = parser.parse_args()
    try:
        if args.command == "solver-smoke":
            from .solver import smoke_check

            result = smoke_check()
            print(json.dumps(result, indent=2))
            return 0 if result["status"] == "OPTIMAL" else 1
        city = City.model_validate_json(args.city.read_text(encoding="utf-8"))
        catalog = load_catalog()
        if args.command == "validate":
            result = validate(city, catalog)
            print(json.dumps({"geometry_valid": result.geometry_valid, **asdict(result)}, indent=2))
            return 0 if result.geometry_valid else 1
        additions = legal_additions(city, catalog, args.facility_id)
        print(
            json.dumps(
                {
                    "count": len(additions),
                    "scope": "single_addition_geometry_only",
                    "placements": [p.model_dump() for p in additions],
                },
                indent=2,
            )
        )
        return 0
    except (ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
