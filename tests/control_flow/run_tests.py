import sys
import subprocess
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
TEST_DIR = Path(__file__).parent

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def normalize(text):
    """Убирает различия в переносах строк и лишних пробелах"""
    return text.replace('\r\n', '\n').strip()

def normalize_error(text):
    """Фильтрует шум, приводит к нижнему регистру и нормализует пути"""
    text = text.lower().replace('\\', '/').replace('\r\n', '\n')
    # Оставляем только строки, содержащие ключевые слова ошибок
    lines = [line.strip() for line in text.split('\n') if 'error:' in line or 'failed:' in line]
    return '\n'.join(lines)

def run_valid_test(src_file, update_mode=False):
    name = src_file.stem
    asm_file = src_file.with_suffix('.asm')
    expected_file = src_file.with_suffix('.expected')

    # 1. Компиляция
    res_compile = subprocess.run([
        sys.executable, "-m", "src.main",
        "compile", "--input", str(src_file), "--output", str(asm_file)
    ], capture_output=True, text=True, cwd=str(ROOT_DIR))

    if res_compile.returncode != 0:
        if update_mode:
            print(f"  {RED}[SKIP]{RESET} {name}.src (compilation failed during update)")
        else:
            print(f"{RED}[FAIL]{RESET} {name}.src (compilation error)")
        return False

    # 2. Проверка синтаксиса NASM
    res_nasm = subprocess.run([
        "nasm", "-f", "win64", str(asm_file), "-o", "NUL"
    ], capture_output=True, text=True, cwd=str(ROOT_DIR))

    if res_nasm.returncode != 0:
        if update_mode:
            print(f"  {RED}[SKIP]{RESET} {name}.src (nasm syntax error during update)")
        else:
            print(f"{RED}[FAIL]{RESET} {name}.src (nasm syntax error)")
        if asm_file.exists(): asm_file.unlink()
        return False

    actual_asm = normalize(asm_file.read_text(encoding='utf-8'))
    if asm_file.exists(): asm_file.unlink()

    if update_mode:
        expected_file.write_text(actual_asm + '\n', encoding='utf-8')
        print(f"  {GREEN}[UPDATED]{RESET} {name}.src")
        return True

    if not expected_file.exists():
        print(f"{YELLOW}[SKIP]{RESET} {name}.src (no .expected file)")
        return False

    expected_asm = normalize(expected_file.read_text(encoding='utf-8'))

    if actual_asm == expected_asm:
        print(f"{GREEN}[PASS]{RESET} {name}.src")
        return True
    else:
        print(f"{RED}[FAIL]{RESET} {name}.src (ASM mismatch)")
        return False

def run_invalid_test(src_file, update_mode=False):
    name = src_file.stem
    expected_file = src_file.with_suffix('.expected')

    res_compile = subprocess.run([
        sys.executable, "-m", "src.main",
        "compile", "--input", str(src_file)
    ], capture_output=True, text=True, cwd=str(ROOT_DIR))

    actual_error = normalize_error(res_compile.stderr + res_compile.stdout)

    if update_mode:
        # При обновлении сохраняем сырой вывод, как было раньше
        expected_file.write_text(normalize(res_compile.stderr) + '\n', encoding='utf-8')
        print(f"  {GREEN}[UPDATED]{RESET} {name}.src")
        return True

    if not expected_file.exists():
        print(f"{YELLOW}[SKIP]{RESET} {name}.src (no .expected file)")
        return False

    expected_error = normalize_error(expected_file.read_text(encoding='utf-8'))

    if res_compile.returncode == 0:
        print(f"{RED}[FAIL]{RESET} {name}.src (expected error, but compilation succeeded)")
        return False

    # Гибкая проверка: ищем совпадение ключевых фраз
    if expected_error in actual_error or any(phrase in actual_error for phrase in expected_error.split('\n') if phrase):
        print(f"{GREEN}[PASS]{RESET} {name}.src (error detected)")
        return True
    else:
        print(f"{RED}[FAIL]{RESET} {name}.src (wrong error message)")
        return False

def main():
    parser = argparse.ArgumentParser(description="Control Flow Tests")
    parser.add_argument('--update', action='store_true', help='Regenerate .expected files with current output')
    args = parser.parse_args()

    print("=" * 60)
    print("MiniCompiler Control Flow Tests (Sprint 6)")
    print("=" * 60)
    print(f"Mode: {'UPDATING EXPECTED FILES' if args.update else 'TESTING'}\n")

    passed = failed = 0

    valid_dir = TEST_DIR / "valid"
    if valid_dir.exists():
        src_files = sorted(valid_dir.glob("*.src"))
        print(f"--- Running {len(src_files)} Valid Tests ---")
        for f in src_files:
            if run_valid_test(f, args.update): passed += 1
            else: failed += 1
        print()

    invalid_dir = TEST_DIR / "invalid"
    if invalid_dir.exists():
        src_files = sorted(invalid_dir.glob("*.src"))
        print(f"--- Running {len(src_files)} Invalid Tests ---")
        for f in src_files:
            if run_invalid_test(f, args.update): passed += 1
            else: failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed + failed} total")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 60)

    # При обновлении всегда выходим успешно, при тестировании - по результату
    sys.exit(0 if (args.update or failed == 0) else 1)

if __name__ == "__main__":
    main()