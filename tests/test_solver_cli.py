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
