import subprocess
import sys
from pathlib import Path

# Корректные пути
SCRIPT_DIR = Path(__file__).parent
VALID_TESTS_DIR = SCRIPT_DIR / "valid"
INVALID_TESTS_DIR = SCRIPT_DIR / "invalid"
ROOT_DIR = SCRIPT_DIR.parent.parent


def run_lexer(input_file: Path) -> str:
    abs_path = str(input_file.resolve())
    cmd = [
        sys.executable, "-m", "src.lexer.main",
        "lex", "--input", abs_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))

    # ✅ Объединяем stdout и stderr для полного сравнения
    output = result.stdout.strip()
    if result.stderr.strip():
        output += "\n" + result.stderr.strip()
    return output


def load_expected(expected_file: Path) -> str:
    if not expected_file.exists():
        return None
    return expected_file.read_text(encoding='utf-8').strip()


def run_tests(test_dir: Path, test_type: str):
    print(f"\n--- Running {test_type} Tests ---")
    passed = failed = skipped = 0
    src_files = sorted(test_dir.glob("*.src"))

    if not src_files:
        print(f"⚠️ No .src files found in {test_dir}")
        return 0, 0, 0

    for src_file in src_files:
        expected_file = src_file.with_suffix(".expected")
        expected_output = load_expected(expected_file)

        if expected_output is None:
            print(f"[SKIP] {src_file.name} (no .expected file)")
            skipped += 1
            continue

        try:
            actual_output = run_lexer(src_file)
            if actual_output == expected_output:
                print(f"[PASS] {src_file.name}")
                passed += 1
            else:
                print(f"[FAIL] {src_file.name}")
                # Показываем полные отличия без обрезки
                print(f"  Expected:\n{expected_output}")
                print(f"  Actual:\n{actual_output}")
                print("-" * 40)
                failed += 1
        except Exception as e:
            print(f"[ERROR] {src_file.name}: {e}")
            failed += 1

    return passed, failed, skipped


if __name__ == "__main__":
    total_p = total_f = total_s = 0
    for test_dir, name in [(VALID_TESTS_DIR, "Valid"), (INVALID_TESTS_DIR, "Invalid")]:
        p, f, s = run_tests(test_dir, name)
        total_p += p;
        total_f += f;
        total_s += s

    print(f"\n--- Results ---")
    print(f"✅ Passed: {total_p}")
    print(f"❌ Failed: {total_f}")
    print(f"⏭️  Skipped: {total_s}")
    print(f"Total:   {total_p + total_f + total_s}")
    sys.exit(0 if total_f == 0 else 1)