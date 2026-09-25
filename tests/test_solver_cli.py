import json
import subprocess
import sys
from pathlib import Path

from swc_build_optimizer.solver import smoke_check


def test_real_ortools_solve():
    assert smoke_check() == {"status": "OPTIMAL", "objective": 2.0, "best_bound": 2.0}


def test_cli_validation_reports_scope():
    path = Path(__file__).parent / "fixtures/mine_low_er_4_garage_hr50.city.json"
    result = subprocess.run(
        [sys.executable, "-m", "swc_build_optimizer.cli", "validate", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["geometry_valid"]
    assert "economics" in report["unchecked"]


def test_cli_invalid_file_is_nonzero(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"name":"bad", "width":0}')
    result = subprocess.run(
        [sys.executable, "-m", "swc_build_optimizer.cli", "validate", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "error:" in result.stderr


def test_solve_cli_writes_validated_result(tmp_path):
    request = Path(__file__).resolve().parents[1] / "examples/fixed-additions.request.json"
    output = tmp_path / "result.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "swc_build_optimizer.cli",
            "solve",
            str(request),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text())
    assert payload == json.loads(result.stdout)
    assert payload["geometry_valid"]
    assert payload["status"] == "PROVEN_OPTIMAL"
    assert payload["additions_placed"] == 4


def test_solve_cli_exit_codes(tmp_path):
    from swc_build_optimizer.models import City
    from swc_build_optimizer.solve_models import AdditionRequest, SolveRequest

    for limit, expected_status, code in [(30.0, "PROVEN_INFEASIBLE", 1), (1e-9, "UNKNOWN", 3)]:
        request = SolveRequest(
            city=City(name="tiny", width=3, height=3),
            time_limit_seconds=limit,
            additions=(AdditionRequest(facility_id=7, min_count=1, max_count=1),),
        )
        path = tmp_path / "request.json"
        path.write_text(request.model_dump_json())
        result = subprocess.run(
            [sys.executable, "-m", "swc_build_optimizer.cli", "solve", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == code, result.stderr
        assert json.loads(result.stdout)["status"] == expected_status
