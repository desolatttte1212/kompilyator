import subprocess
import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
VALID_TESTS_DIR = ROOT_DIR / "tests" / "lexer" / "valid"
INVALID_TESTS_DIR = ROOT_DIR / "tests" / "lexer" / "invalid"


def run_lexer(input_file: Path) -> str:
    cmd = [
        sys.executable, "-m", "src.lexer.main",
        "lex", "--input", str(input_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))

    if result.stderr:
        print(f"STDERR for {input_file.name}:\n{result.stderr}")

    return result.stdout.strip()


def load_expected(expected_file: Path) -> str:
    if not expected_file.exists():
        raise FileNotFoundError(f"Expected file not found: {expected_file}")

    encodings = ['utf-8-sig', 'utf-8', 'utf-16', 'cp1251']

    for encoding in encodings:
        try:
            return expected_file.read_text(encoding=encoding).strip()
        except UnicodeDecodeError:
            continue

    raise ValueError(f"Не удалось прочитать файл {expected_file} ни в одной из известных кодировок")


def run_tests(test_dir: Path, test_type: str):
    print(f"\n--- Running {test_type} Tests ---")
    passed = 0
    failed = 0

    src_files = list(test_dir.glob("*.src"))

    if not src_files:
        print(f"No .src files found in {test_dir}")
        return 0, 0

    for src_file in src_files:
        expected_file = src_file.with_suffix(".expected")

        if not expected_file.exists():
            print(f"[SKIP] {src_file.name} (no .expected file)")
            continue

        try:
            actual_output = run_lexer(src_file)
            expected_output = load_expected(expected_file)

            if actual_output == expected_output:
                print(f"[PASS] {src_file.name}")
                passed += 1
            else:
                print(f"[FAIL] {src_file.name}")
                print(f"  Expected:\n{expected_output[:200]}...")  # Первые 200 символов
                print(f"  Actual:\n{actual_output[:200]}...")
                failed += 1
        except Exception as e:
            print(f"[ERROR] {src_file.name}: {e}")
            failed += 1

    return passed, failed


if __name__ == "__main__":
    total_passed = 0
    total_failed = 0

    p, f = run_tests(VALID_TESTS_DIR, "Valid")
    total_passed += p
    total_failed += f

    p, f = run_tests(INVALID_TESTS_DIR, "Invalid")
    total_passed += p
    total_failed += f


    print(f"\n--- Results ---")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")

    sys.exit(0 if total_failed == 0 else 1)