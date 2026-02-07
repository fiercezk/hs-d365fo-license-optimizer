#!/usr/bin/env python3
"""Algorithm Portfolio Validation Script.

Validates that all algorithms defined in ALGORITHM_MANIFEST.json are:
1. Present as implementation files in src/algorithms/
2. Exported in src/algorithms/__init__.py
3. Have corresponding test files in tests/
4. Have no orphaned (unmanifested) algorithm files

This script is the enforcement layer for portfolio completeness.
It runs locally (pre-push hook) and in CI (GitHub Actions).

Exit codes:
    0 = All checks pass (portfolio complete)
    1 = One or more checks failed (portfolio incomplete)
    2 = Manifest file is missing or malformed

Usage:
    python scripts/validate_algorithms.py
    python scripts/validate_algorithms.py --verbose
    python scripts/validate_algorithms.py --json  # Machine-readable output
"""

import json
import re
import sys
from pathlib import Path
from typing import Any


# Resolve paths relative to this script's location
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
AGENT_DIR = PROJECT_ROOT / "apps" / "agent"
MANIFEST_PATH = AGENT_DIR / "ALGORITHM_MANIFEST.json"
ALGORITHMS_DIR = AGENT_DIR / "src" / "algorithms"
TESTS_DIR = AGENT_DIR / "tests"
INIT_FILE = ALGORITHMS_DIR / "__init__.py"


class ValidationResult:
    """Tracks pass/fail status for a single validation check."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.passed: bool = True
        self.messages: list[str] = []
        self.details: list[str] = []

    def fail(self, message: str) -> None:
        self.passed = False
        self.messages.append(message)

    def info(self, message: str) -> None:
        self.details.append(message)

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"{self.name}: [{status}]"


def load_manifest() -> dict[str, Any] | None:
    """Load and validate the algorithm manifest file."""
    if not MANIFEST_PATH.exists():
        print(f"ERROR: Manifest file not found: {MANIFEST_PATH}")
        print("Create ALGORITHM_MANIFEST.json before running validation.")
        return None

    try:
        with open(MANIFEST_PATH) as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Manifest file is malformed JSON: {e}")
        return None

    # Basic structure validation
    required_keys = ["expected_total", "algorithms"]
    for key in required_keys:
        if key not in manifest:
            print(f"ERROR: Manifest missing required key: '{key}'")
            return None

    return manifest


def check_manifest_integrity(manifest: dict[str, Any]) -> ValidationResult:
    """Check 1: Manifest internal consistency."""
    result = ValidationResult("Manifest Integrity")

    algorithms = manifest["algorithms"]
    expected_total = manifest["expected_total"]
    actual_count = len(algorithms)

    if actual_count != expected_total:
        result.fail(
            f"Manifest declares expected_total={expected_total} "
            f"but contains {actual_count} entries"
        )

    # Check for duplicate IDs
    ids = [a["id"] for a in algorithms]
    seen: set[str] = set()
    duplicates: list[str] = []
    for algo_id in ids:
        if algo_id in seen:
            duplicates.append(algo_id)
        seen.add(algo_id)

    if duplicates:
        result.fail(f"Duplicate algorithm IDs: {', '.join(duplicates)}")

    # Check required fields per algorithm
    required_fields = ["id", "name", "implementation_file", "test_file"]
    for algo in algorithms:
        for field in required_fields:
            if field not in algo:
                result.fail(
                    f"Algorithm {algo.get('id', '?')} missing "
                    f"required field: '{field}'"
                )

    result.info(f"{actual_count} algorithms defined in manifest")
    return result


def check_file_presence(manifest: dict[str, Any]) -> ValidationResult:
    """Check 2: Implementation and test files exist."""
    result = ValidationResult("File Presence")

    algorithms = manifest["algorithms"]
    total = len(algorithms)
    impl_found = 0
    test_found = 0
    missing_impl: list[str] = []
    missing_test: list[str] = []

    for algo in algorithms:
        algo_id = algo["id"]
        impl_file = ALGORITHMS_DIR / algo["implementation_file"]
        test_file = TESTS_DIR / algo["test_file"]

        if impl_file.exists():
            impl_found += 1
        else:
            missing_impl.append(f"{algo_id}: {algo['implementation_file']}")

        if test_file.exists():
            test_found += 1
        else:
            missing_test.append(f"{algo_id}: {algo['test_file']}")

    if missing_impl:
        result.fail(
            f"Implementation files: {impl_found}/{total} present"
        )
        for m in missing_impl:
            result.fail(f"  MISSING IMPL: {m}")

    if missing_test:
        result.fail(f"Test files: {test_found}/{total} present")
        for m in missing_test:
            result.fail(f"  MISSING TEST: {m}")

    if not missing_impl:
        result.info(f"Implementation files: {impl_found}/{total} present")
    if not missing_test:
        result.info(f"Test files: {test_found}/{total} present")

    return result


def check_init_exports(manifest: dict[str, Any]) -> ValidationResult:
    """Check 3: Algorithms are exported in __init__.py."""
    result = ValidationResult("Init Exports")

    if not INIT_FILE.exists():
        result.fail(f"__init__.py not found: {INIT_FILE}")
        return result

    init_content = INIT_FILE.read_text()

    algorithms = manifest["algorithms"]
    total_required = sum(
        1 for a in algorithms if a.get("init_export_required", True)
    )
    exported = 0
    missing_exports: list[str] = []

    for algo in algorithms:
        if not algo.get("init_export_required", True):
            continue

        impl_file = algo["implementation_file"]
        # Strip .py extension to get module name
        module_name = impl_file.replace(".py", "")

        # Check for import pattern: from .module_name import ...
        pattern = rf"from\s+\.{re.escape(module_name)}\s+import"
        if re.search(pattern, init_content):
            exported += 1
        else:
            missing_exports.append(
                f"{algo['id']}: .{module_name} not imported"
            )

    if missing_exports:
        result.fail(f"Init exports: {exported}/{total_required} present")
        for m in missing_exports:
            result.fail(f"  MISSING EXPORT: {m}")
    else:
        result.info(f"Init exports: {exported}/{total_required} present")

    return result


def check_orphan_files(manifest: dict[str, Any]) -> ValidationResult:
    """Check 4: No algorithm files exist without manifest entries."""
    result = ValidationResult("Orphan Detection")

    # Get all algorithm_*.py files from filesystem
    if not ALGORITHMS_DIR.exists():
        result.fail(f"Algorithms directory not found: {ALGORITHMS_DIR}")
        return result

    fs_files = {
        f.name
        for f in ALGORITHMS_DIR.glob("algorithm_*.py")
    }

    # Get all implementation files from manifest
    manifest_files = {a["implementation_file"] for a in manifest["algorithms"]}

    # Find orphans (in filesystem but not in manifest)
    orphans = fs_files - manifest_files

    if orphans:
        result.fail(f"{len(orphans)} unmanifested algorithm file(s)")
        for orphan in sorted(orphans):
            result.fail(f"  ORPHAN: {orphan} (not in manifest)")
    else:
        result.info("0 unmanifested files")

    return result


def check_test_content(manifest: dict[str, Any]) -> ValidationResult:
    """Check 5: Test files contain at least one test function."""
    result = ValidationResult("Test Content")

    algorithms = manifest["algorithms"]
    total = len(algorithms)
    has_tests = 0
    empty_tests: list[str] = []

    for algo in algorithms:
        test_file = TESTS_DIR / algo["test_file"]
        if not test_file.exists():
            # Already reported by check_file_presence
            continue

        content = test_file.read_text()
        # Look for test functions (def test_...)
        test_functions = re.findall(r"def\s+(test_\w+)", content)

        if test_functions:
            has_tests += 1
        else:
            empty_tests.append(
                f"{algo['id']}: {algo['test_file']} has 0 test functions"
            )

    if empty_tests:
        result.fail(f"Test content: {has_tests}/{total} have test functions")
        for m in empty_tests:
            result.fail(f"  EMPTY TEST: {m}")
    else:
        result.info(f"Test content: {has_tests}/{total} have test functions")

    return result


def print_report(
    results: list[ValidationResult],
    manifest: dict[str, Any],
    verbose: bool = False,
) -> bool:
    """Print validation report and return overall pass/fail."""
    total = manifest["expected_total"]
    all_passed = all(r.passed for r in results)

    print()
    print("=" * 60)
    print("  ALGORITHM PORTFOLIO VALIDATION")
    print("=" * 60)
    print(f"  Manifest: {total} algorithms defined")
    print()

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  {r.name:<25} [{status}]")

        if r.passed and verbose:
            for detail in r.details:
                print(f"    {detail}")
        elif not r.passed:
            for msg in r.messages:
                print(f"    {msg}")

    print()
    print("-" * 60)
    if all_passed:
        print("  RESULT: PORTFOLIO COMPLETE")
        print(f"  All {total} algorithms validated successfully.")
    else:
        failed_checks = [r for r in results if not r.passed]
        print(f"  RESULT: PORTFOLIO INCOMPLETE ({len(failed_checks)} check(s) failed)")
        print()
        print("  To fix:")
        print("    1. Check ALGORITHM_MANIFEST.json for expected files")
        print("    2. Ensure missing algorithms are merged to this branch")
        print("    3. Update __init__.py exports if needed")
        print("    4. Re-run: python scripts/validate_algorithms.py")
    print("=" * 60)
    print()

    return all_passed


def print_json_report(
    results: list[ValidationResult],
    manifest: dict[str, Any],
) -> bool:
    """Print machine-readable JSON report."""
    all_passed = all(r.passed for r in results)

    report = {
        "portfolio_complete": all_passed,
        "expected_total": manifest["expected_total"],
        "checks": [
            {
                "name": r.name,
                "passed": r.passed,
                "messages": r.messages if not r.passed else [],
                "details": r.details,
            }
            for r in results
        ],
    }

    print(json.dumps(report, indent=2))
    return all_passed


def main() -> int:
    """Run all validation checks."""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    json_output = "--json" in sys.argv

    # Load manifest
    manifest = load_manifest()
    if manifest is None:
        return 2

    # Run all checks
    results: list[ValidationResult] = [
        check_manifest_integrity(manifest),
        check_file_presence(manifest),
        check_init_exports(manifest),
        check_orphan_files(manifest),
        check_test_content(manifest),
    ]

    # Output report
    if json_output:
        all_passed = print_json_report(results, manifest)
    else:
        all_passed = print_report(results, manifest, verbose)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
