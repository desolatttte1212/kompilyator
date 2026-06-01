import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
TEST_DIR = Path(__file__).parent

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def normalize(text):
    return text.replace('\r\n', '\n').strip()

def normalize_error(text):
    """Фильтрует шум, приводит к нижнему регистру и нормализует пути"""
    text = text.lower().replace('\\', '/').replace('\r\n', '\n')
    lines = [line.strip() for line in text.split('\n') if 'error:' in line or 'failed:' in line]
    return '\n'.join(lines)

def run_valid_test(src_file):
    name = src_file.stem
    asm_file = src_file.with_suffix('.asm')
    expected_file = src_file.with_suffix('.expected')

    if not expected_file.exists():
        print(f"{YELLOW}[SKIP]{RESET} {name} (no .expected file)")
        return None

    # 1. Компиляция
    cmd_compile = [
        sys.executable, "-m", "src.main",
        "compile",
        "--input", str(src_file),
        "--output", str(asm_file)
    ]

    res_compile = subprocess.run(cmd_compile, capture_output=True, text=True, cwd=str(ROOT_DIR))

    if res_compile.returncode != 0:
        print(f"{RED}[FAIL]{RESET} {name} (Compilation Error)")
        print(f"       {res_compile.stderr.strip().splitlines()[-1]}")
        return False

    # 2. Проверка синтаксиса NASM
    res_nasm = subprocess.run(
        ["nasm", "-f", "win64", str(asm_file), "-o", "NUL"],
        capture_output=True, text=True, cwd=str(ROOT_DIR)
    )

    if res_nasm.returncode != 0:
        print(f"{RED}[FAIL]{RESET} {name} (NASM Syntax Error)")
        print(f"       {res_nasm.stderr.strip().splitlines()[0]}")
        if asm_file.exists(): asm_file.unlink()
        return False

    # 3. Сравнение с Expected
    actual_asm = normalize(asm_file.read_text(encoding='utf-8'))
    expected_asm = normalize(expected_file.read_text(encoding='utf-8'))

    if asm_file.exists():
        asm_file.unlink()

    if actual_asm == expected_asm:
        print(f"{GREEN}[PASS]{RESET} {name}")
        return True
    else:
        print(f"{RED}[FAIL]{RESET} {name} (ASM Mismatch)")
        print(f"       Expected lines: {len(expected_asm.splitlines())}")
        print(f"       Actual lines:   {len(actual_asm.splitlines())}")
        return False

def run_invalid_test(src_file):
    name = src_file.stem
    expected_file = src_file.with_suffix('.expected')

    if not expected_file.exists():
        print(f"{YELLOW}[SKIP]{RESET} {name} (no .expected file)")
        return None

    expected_error = normalize_error(expected_file.read_text(encoding='utf-8'))

    cmd_compile = [
        sys.executable, "-m", "src.main",
        "compile",
        "--input", str(src_file)
    ]

    res_compile = subprocess.run(cmd_compile, capture_output=True, text=True, cwd=str(ROOT_DIR))

    if res_compile.returncode == 0:
        print(f"{RED}[FAIL]{RESET} {name} (Expected error, but succeeded)")
        return False

    actual_error = normalize_error(res_compile.stderr + res_compile.stdout)

    # Гибкая проверка по ключевым фразам
    if expected_error in actual_error or any(phrase in actual_error for phrase in expected_error.split('\n') if phrase):
        print(f"{GREEN}[PASS]{RESET} {name} (Error detected)")
        return True
    else:
        print(f"{RED}[FAIL]{RESET} {name} (Wrong error message)")
        print(f"       Expected: '{expected_error[:50]}...'")
        print(f"       Got:      '{actual_error[:50]}...'")
        return False

def main():
    print("=" * 60)
    print("MiniCompiler Codegen Tests (Sprint 5)")
    print("=" * 60)

    passed = failed = skipped = 0

    # --- Valid Tests ---
    valid_dir = TEST_DIR / "valid"
    if valid_dir.exists():
        print(f"\n--- Running {len(list(valid_dir.glob('*.src')))} Valid Tests ---\n")
        for f in sorted(valid_dir.glob("*.src")):
            res = run_valid_test(f)
            if res:
                passed += 1
            elif res is False:
                failed += 1
            else:
                skipped += 1
    else:
        print(f"\n{YELLOW}[WARN]{RESET} Directory 'valid' not found.")

    # --- Invalid Tests ---
    invalid_dir = TEST_DIR / "invalid"
    if invalid_dir.exists():
        print(f"\n--- Running {len(list(invalid_dir.glob('*.src')))} Invalid Tests ---\n")
        for f in sorted(invalid_dir.glob("*.src")):
            res = run_invalid_test(f)
            if res:
                passed += 1
            elif res is False:
                failed += 1
            else:
                skipped += 1
    else:
        print(f"\n{YELLOW}[WARN]{RESET} Directory 'invalid' not found.")

    # --- Summary ---
    print("\n" + "=" * 60)
    print(f"Results: {passed + failed + skipped} total")
    print(f"Passed:  {GREEN}{passed}{RESET}")
    print(f"Failed:  {RED}{failed}{RESET}")
    print(f"Skipped: {YELLOW}{skipped}{RESET}")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()