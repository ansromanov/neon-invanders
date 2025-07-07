#!/usr/bin/env python
"""Run the test suite using pytest."""

import os
import subprocess
import sys


def main():
    """Run pytest with appropriate arguments."""
    # Ensure we're in the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    # Build pytest command
    pytest_args = [
        sys.executable,
        "-m",
        "pytest",
    ]

    # Add any command line arguments passed to this script
    if len(sys.argv) > 1:
        pytest_args.extend(sys.argv[1:])

    # Run pytest
    print("Running tests with pytest...")
    print(f"Command: {' '.join(pytest_args)}")
    print("-" * 70)

    result = subprocess.run(pytest_args, check=False)

    # Exit with the same code as pytest
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
