#!/usr/bin/env python3
"""Script to check for syntax errors in Python files."""

from pathlib import Path
import ast
import sys


def check_file(file_path: Path) -> int:
    """
    Check a file for syntax errors.

    Args:
        file_path: Path to the file to check

    Returns:
        Number of errors found
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check syntax
        ast.parse(content, filename=str(file_path))
        return 0
    except SyntaxError as e:
        print(
            f"Syntax error in {file_path} at line {e.lineno}, column {e.offset}: {e.msg}"
        )
        if e.text:
            print(f"  {e.text.strip()}")
            if e.offset:
                print(f"  {' ' * (e.offset - 1)}^")
        return 1
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
        return 1


def main() -> int:
    """
    Check all Python files in the repository for syntax errors.

    Returns:
        Exit code (0 for success, 1 for errors)
    """
    files_to_check = list(Path("src").glob("**/*.py"))
    files_to_check.extend(
        [
            Path("fix_syntax_errors.py"),
            Path("fix_imports.py"),
            Path("fix_github_actions.py"),
            Path("fix_ruff_errors.py"),
            Path("finalize_fixes.py"),
        ]
    )

    error_count = 0
    for file_path in files_to_check:
        if file_path.exists():
            file_errors = check_file(file_path)
            if file_errors == 0:
                print(f"✅ {file_path}")
            else:
                error_count += file_errors

    print(f"\nChecked {len(files_to_check)} files, found {error_count} syntax errors.")
    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
