# tests/codegen/generate_expected.py
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
TEST_DIR = Path(__file__).parent


def run_compiler(src_file):
    """Запускает компилятор. Возвращает (success: bool, output: str)"""
    cmd = [
        sys.executable, "-m", "src.main",
        "compile",
        "--input", str(src_file)
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT_DIR))

    # Если компиляция успешна, читаем сгенерированный .asm файл
    if res.returncode == 0:
        asm_file = src_file.with_suffix('.asm')
        if asm_file.exists():
            return True, asm_file.read_text(encoding='utf-8').strip()
        return True, ""
    else:
        # Если ошибка, берем stderr
        return False, res.stderr.strip()


def main():
    print("🔄 Генерация .expected файлов...\n")

    # 1. Валидные тесты
    valid_dir = TEST_DIR / "valid"
    if valid_dir.exists():
        for src_file in sorted(valid_dir.glob("*.src")):
            expected_file = src_file.with_suffix('.expected')
            success, output = run_compiler(src_file)
            if success:
                expected_file.write_text(output, encoding='utf-8')
                print(f"✅ valid/{expected_file.name}")
            else:
                print(f"❌ valid/{src_file.name} -> {output}")

    # 2. Негативные тесты
    invalid_dir = TEST_DIR / "invalid"
    if invalid_dir.exists():
        for src_file in sorted(invalid_dir.glob("*.src")):
            expected_file = src_file.with_suffix('.expected')
            success, output = run_compiler(src_file)
            if not success:
                # Ожидаем ошибку, сохраняем её текст
                expected_file.write_text(output, encoding='utf-8')
                print(f"✅ invalid/{expected_file.name}")
            else:
                print(f"❌ invalid/{src_file.name} -> Compilation succeeded (expected error)")

    print("\n✨ Готово! Все .expected файлы созданы.")


if __name__ == "__main__":
    main()