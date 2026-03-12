import subprocess
import sys
import os
import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
VALID_TESTS_DIR = ROOT_DIR / "tests" / "parser" / "valid"
INVALID_TESTS_DIR = ROOT_DIR / "tests" / "parser" / "invalid"


def run_parser(input_file: Path, output_format: str = "json") -> tuple:
    cmd = [
        sys.executable, "-m", "src.main",
        "parse",
        "--input", str(input_file),
        "--ast-format", output_format
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))

    return result.stdout.strip(), result.stderr.strip(), result.returncode


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


def compare_json(actual: str, expected: str) -> bool:
    try:
        actual_json = json.loads(actual)
        expected_json = json.loads(expected)
        return actual_json == expected_json
    except json.JSONDecodeError as e:
        print(f"  JSON decode error: {e}")
        return False


def run_tests(test_dir: Path, test_type: str):
    print(f"\n--- Running {test_type} Tests ---")
    passed = 0
    failed = 0

    src_files = sorted(test_dir.glob("*.src"))

    if not src_files:
        print(f"No .src files found in {test_dir}")
        return 0, 0

    for src_file in src_files:
        expected_file = src_file.with_suffix(".expected.json")
        is_invalid_test = "invalid" in src_file.parts

        if not is_invalid_test and not expected_file.exists():
            print(f"[SKIP] {src_file.name} (no .expected.json file)")
            continue

        try:
            actual_output, stderr_output, returncode = run_parser(src_file)

            if is_invalid_test:
                if returncode != 0:
                    error_msg = stderr_output.split('\n')
                    print(f"[PASS] {src_file.name}")
                    for line in error_msg:
                        if '[ERROR]' in line or 'Line' in line:
                            print(f"       {line.strip()}")
                    passed += 1
                else:
                    print(f"[FAIL] {src_file.name}")
                    print(f"       Expected error, but parser succeeded")
                    failed += 1
                continue

            # For valid tests, compare AST output
            if expected_file.exists():
                expected_output = load_expected(expected_file)

                if compare_json(actual_output, expected_output):
                    print(f"[PASS] {src_file.name}")
                    passed += 1
                else:
                    print(f"[FAIL] {src_file.name}")
                    print(f"  Expected:\n{expected_output[:300]}...")
                    print(f"  Actual:\n{actual_output[:300]}...")
                    failed += 1
            else:
                if returncode == 0:
                    print(f"[PASS] {src_file.name} (parsed successfully)")
                    passed += 1
                else:
                    print(f"[FAIL] {src_file.name}")
                    print(f"       Parser failed: {stderr_output[:200]}")
                    failed += 1

        except Exception as e:
            print(f"[ERROR] {src_file.name}: {e}")
            failed += 1

    return passed, failed


def generate_expected_files():
    print("\n--- Generating Expected Files ---")

    src_files = sorted(VALID_TESTS_DIR.glob("*.src"))
    generated = 0

    for src_file in src_files:
        expected_file = src_file.with_suffix(".expected.json")

        try:
            actual_output, stderr_output, returncode = run_parser(src_file)

            if returncode == 0:
                json.loads(actual_output)

                with open(expected_file, 'w', encoding='utf-8') as f:
                    f.write(actual_output)

                print(f"[GENERATED] {expected_file.name}")
                generated += 1
            else:
                print(f"[SKIP] {src_file.name} (parsing failed)")
                print(f"       {stderr_output[:200]}")

        except Exception as e:
            print(f"[ERROR] {src_file.name}: {e}")

    print(f"\nGenerated {generated} expected files")
    return generated


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        generate_expected_files()
        sys.exit(0)

    print("=" * 60)
    print("MiniCompiler Parser Tests")
    print("=" * 60)

    total_passed = 0
    total_failed = 0

    p, f = run_tests(VALID_TESTS_DIR, "Valid")
    total_passed += p
    total_failed += f

    p, f = run_tests(INVALID_TESTS_DIR, "Invalid")
    total_passed += p
    total_failed += f

    print("\n" + "=" * 60)
    print(f"Results: {total_passed + total_failed} total")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print("=" * 60)

    sys.exit(0 if total_failed == 0 else 1)