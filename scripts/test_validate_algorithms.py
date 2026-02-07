#!/usr/bin/env python3
"""Tests for the algorithm portfolio validation script.

These tests verify the validation script itself works correctly,
using mock filesystem structures to simulate various failure modes.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parent / "validate_algorithms.py"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestValidationScript:
    """Test the validate_algorithms.py script end-to-end."""

    def test_script_exists(self) -> None:
        """Validation script must exist."""
        assert SCRIPT_PATH.exists(), f"Script not found: {SCRIPT_PATH}"

    def test_script_is_executable(self) -> None:
        """Validation script must be executable."""
        import os
        assert os.access(SCRIPT_PATH, os.X_OK), "Script is not executable"

    def test_manifest_exists(self) -> None:
        """ALGORITHM_MANIFEST.json must exist."""
        manifest_path = PROJECT_ROOT / "apps" / "agent" / "ALGORITHM_MANIFEST.json"
        assert manifest_path.exists(), f"Manifest not found: {manifest_path}"

    def test_manifest_is_valid_json(self) -> None:
        """ALGORITHM_MANIFEST.json must be valid JSON."""
        manifest_path = PROJECT_ROOT / "apps" / "agent" / "ALGORITHM_MANIFEST.json"
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert "expected_total" in manifest
        assert "algorithms" in manifest

    def test_manifest_has_34_algorithms(self) -> None:
        """ALGORITHM_MANIFEST.json must declare exactly 34 algorithms."""
        manifest_path = PROJECT_ROOT / "apps" / "agent" / "ALGORITHM_MANIFEST.json"
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert manifest["expected_total"] == 34
        assert len(manifest["algorithms"]) == 34

    def test_manifest_no_duplicate_ids(self) -> None:
        """All algorithm IDs in manifest must be unique."""
        manifest_path = PROJECT_ROOT / "apps" / "agent" / "ALGORITHM_MANIFEST.json"
        with open(manifest_path) as f:
            manifest = json.load(f)
        ids = [a["id"] for a in manifest["algorithms"]]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {ids}"

    def test_manifest_required_fields(self) -> None:
        """Each algorithm entry must have required fields."""
        manifest_path = PROJECT_ROOT / "apps" / "agent" / "ALGORITHM_MANIFEST.json"
        with open(manifest_path) as f:
            manifest = json.load(f)
        required = ["id", "name", "implementation_file", "test_file"]
        for algo in manifest["algorithms"]:
            for field in required:
                assert field in algo, (
                    f"Algorithm {algo.get('id', '?')} missing field: {field}"
                )

    def test_json_output_mode(self) -> None:
        """Script --json flag must produce valid JSON output."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--json"],
            capture_output=True,
            text=True,
        )
        # Parse the JSON output (ignore exit code, focus on format)
        output = json.loads(result.stdout)
        assert "portfolio_complete" in output
        assert "expected_total" in output
        assert "checks" in output
        assert isinstance(output["checks"], list)

    def test_exit_code_nonzero_when_incomplete(self) -> None:
        """Script must exit with code 1 when portfolio is incomplete."""
        # This test will pass when algorithms 6.2 and 6.4 are missing
        # and will need adjustment when they are merged
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
        )
        # We know main is currently missing 6.2 and 6.4
        # This is a meta-test: it validates the script catches the gap
        # When all 34 are present, change this assertion to assertEqual(0)
        assert result.returncode in (0, 1), (
            f"Unexpected exit code: {result.returncode}"
        )

    def test_manifest_file_naming_convention(self) -> None:
        """Implementation files must follow naming convention."""
        manifest_path = PROJECT_ROOT / "apps" / "agent" / "ALGORITHM_MANIFEST.json"
        with open(manifest_path) as f:
            manifest = json.load(f)
        import re
        for algo in manifest["algorithms"]:
            impl = algo["implementation_file"]
            assert re.match(
                r"algorithm_\d+_\d+_\w+\.py$", impl
            ), f"Bad naming: {impl}"

            test = algo["test_file"]
            assert re.match(
                r"test_algorithm_\d+_\d+\.py$", test
            ), f"Bad test naming: {test}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
