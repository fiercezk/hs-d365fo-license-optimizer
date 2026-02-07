#!/usr/bin/env python3
"""Algorithm Completeness Checker.

Validates that an algorithm implementation meets all 5 completeness criteria:
  1. Implementation file exists
  2. Tests pass
  3. Mypy type checking passes
  4. Ruff linting passes
  5. Algorithm is registered in __init__.py

Usage:
    python scripts/check_algorithm_completeness.py 1.4
    python scripts/check_algorithm_completeness.py 2.2

Exit codes:
    0: All checks passed
    1: One or more checks failed
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Final

# Project root is parent of scripts/ directory
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent


def check_implementation_exists(algo_num: str) -> bool:
    """Check if implementation file exists.

    Args:
        algo_num: Algorithm number in format "X.Y"

    Returns:
        True if implementation exists, False otherwise
    """
    algo_pattern = f"algorithm_{algo_num.replace('.', '_')}_*.py"
    algo_dir = PROJECT_ROOT / "src" / "algorithms"

    matches = list(algo_dir.glob(algo_pattern))

    if not matches:
        print(f"  ✗ Implementation file not found (expected: {algo_pattern})")
        return False

    print(f"  ✓ Implementation exists: {matches[0].name}")
    return True


def check_tests_pass(algo_num: str) -> bool:
    """Check if tests pass.

    Args:
        algo_num: Algorithm number in format "X.Y"

    Returns:
        True if tests pass, False otherwise
    """
    test_file = f"test_algorithm_{algo_num.replace('.', '_')}.py"
    test_path = PROJECT_ROOT / "tests" / test_file

    if not test_path.exists():
        print(f"  ✗ Test file not found: {test_file}")
        return False

    # Check for virtual environment
    venv_python = PROJECT_ROOT / ".venv" / "bin" / "python3"
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    try:
        result = subprocess.run(
            [python_cmd, "-m", "pytest", str(test_path), "-v"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            # Extract test count from pytest output
            for line in result.stdout.split("\n"):
                if "passed" in line:
                    print(f"  ✓ Tests pass: {line.strip()}")
                    break
            else:
                print("  ✓ Tests pass")
            return True
        else:
            print(f"  ✗ Tests failed (exit code: {result.returncode})")
            # Show last few lines of output for debugging
            error_lines = result.stdout.split("\n")[-10:]
            for line in error_lines:
                if line.strip():
                    print(f"    {line}")
            return False

    except Exception as e:
        print(f"  ✗ Error running tests: {e}")
        return False


def check_mypy_clean(algo_num: str) -> bool:
    """Check if mypy type checking passes.

    Args:
        algo_num: Algorithm number in format "X.Y"

    Returns:
        True if mypy passes, False otherwise
    """
    algo_pattern = f"algorithm_{algo_num.replace('.', '_')}_*.py"
    algo_dir = PROJECT_ROOT / "src" / "algorithms"

    matches = list(algo_dir.glob(algo_pattern))

    if not matches:
        print("  ✗ Implementation not found for mypy check")
        return False

    # Check for virtual environment
    venv_python = PROJECT_ROOT / ".venv" / "bin" / "python3"
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    try:
        result = subprocess.run(
            [python_cmd, "-m", "mypy", str(matches[0])],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print("  ✓ Mypy clean (no type errors)")
            return True
        else:
            print("  ✗ Mypy found type errors:")
            for line in result.stdout.split("\n"):
                if line.strip():
                    print(f"    {line}")
            return False

    except Exception as e:
        print(f"  ✗ Error running mypy: {e}")
        return False


def check_ruff_clean(algo_num: str) -> bool:
    """Check if ruff linting passes.

    Args:
        algo_num: Algorithm number in format "X.Y"

    Returns:
        True if ruff passes, False otherwise
    """
    algo_pattern = f"algorithm_{algo_num.replace('.', '_')}_*.py"
    test_pattern = f"test_algorithm_{algo_num.replace('.', '_')}.py"

    algo_dir = PROJECT_ROOT / "src" / "algorithms"
    test_dir = PROJECT_ROOT / "tests"

    algo_matches = list(algo_dir.glob(algo_pattern))
    test_matches = list(test_dir.glob(test_pattern))

    if not algo_matches:
        print("  ✗ Implementation not found for ruff check")
        return False

    files_to_check = [str(m) for m in algo_matches + test_matches]

    # Check for virtual environment
    venv_python = PROJECT_ROOT / ".venv" / "bin" / "python3"
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    try:
        result = subprocess.run(
            [python_cmd, "-m", "ruff", "check"] + files_to_check,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print("  ✓ Ruff clean (all checks passed)")
            return True
        else:
            print("  ✗ Ruff found linting issues:")
            for line in result.stdout.split("\n"):
                if line.strip():
                    print(f"    {line}")
            return False

    except Exception as e:
        print(f"  ✗ Error running ruff: {e}")
        return False


def check_init_registration(algo_num: str) -> bool:
    """Check if algorithm is registered in __init__.py.

    Args:
        algo_num: Algorithm number in format "X.Y"

    Returns:
        True if registered, False otherwise
    """
    init_file = PROJECT_ROOT / "src" / "algorithms" / "__init__.py"

    if not init_file.exists():
        print("  ✗ __init__.py not found")
        return False

    try:
        content = init_file.read_text()

        # Look for algorithm import statement
        algo_module = f"algorithm_{algo_num.replace('.', '_')}_"

        if algo_module in content:
            print("  ✓ Registered in __init__.py")
            return True
        else:
            print(f"  ✗ Not found in __init__.py (expected module name: {algo_module}*)")
            return False

    except Exception as e:
        print(f"  ✗ Error reading __init__.py: {e}")
        return False


def main() -> int:
    """Run all completeness checks.

    Returns:
        Exit code: 0 if all pass, 1 if any fail
    """
    parser = argparse.ArgumentParser(
        description="Check algorithm implementation completeness"
    )
    parser.add_argument(
        "algorithm",
        help='Algorithm number in format "X.Y" (e.g., "1.4", "2.2")',
    )
    args = parser.parse_args()

    algo_num = args.algorithm

    print(f"\n{'='*60}")
    print(f"Algorithm {algo_num} Completeness Check")
    print(f"{'='*60}\n")

    # Run all 5 checks
    checks = [
        ("1. Implementation exists", lambda: check_implementation_exists(algo_num)),
        ("2. Tests pass", lambda: check_tests_pass(algo_num)),
        ("3. Mypy clean", lambda: check_mypy_clean(algo_num)),
        ("4. Ruff clean", lambda: check_ruff_clean(algo_num)),
        ("5. __init__.py registration", lambda: check_init_registration(algo_num)),
    ]

    results = []
    for check_name, check_func in checks:
        print(f"{check_name}:")
        result = check_func()
        results.append(result)
        print()

    # Summary
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✓ ALL CHECKS PASSED ({passed}/{total})")
        print(f"{'='*60}\n")
        return 0
    else:
        print(f"✗ FAILED: {passed}/{total} checks passed")
        print(f"{'='*60}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
