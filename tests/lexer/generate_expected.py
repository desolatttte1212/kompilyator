"""
Генератор .expected файлов для тестов лексера.
Запускает лексер на всех .src файлах и сохраняет вывод в .expected файлы.
"""

import subprocess
import sys
from pathlib import Path

# Определение путей
SCRIPT_DIR = Path(__file__).parent
VALID_TESTS_DIR = SCRIPT_DIR / "valid"
INVALID_TESTS_DIR = SCRIPT_DIR / "invalid"
ROOT_DIR = SCRIPT_DIR.parent.parent  # mini-compiler


def run_lexer(input_file: Path) -> str:
    """Запускает лексер и возвращает stdout."""
    abs_path = str(input_file.resolve())
    cmd = [
        sys.executable, "-m", "src.lexer.main",
        "lex", "--input", abs_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
            timeout=10
        )
        # Возвращаем stdout + stderr (для ошибок тоже сохраняем вывод)
        output = result.stdout.strip()
        if result.stderr:
            output += "\n" + result.stderr.strip()
        return output
    except subprocess.TimeoutExpired:
        return "ERROR: Timeout"
    except Exception as e:
        return f"ERROR: {str(e)}"


def generate_for_directory(test_dir: Path, dir_name: str):
    """Генерирует .expected файлы для всех .src в папке."""
    print(f"\n{'=' * 60}")
    print(f"Generating .expected files for: {dir_name}")
    print(f"{'=' * 60}")

    src_files = sorted(test_dir.glob("*.src"))
    if not src_files:
        print(f"⚠️  No .src files found in {test_dir}")
        return 0, 0, 0

    created = 0
    updated = 0
    errors = 0

    for src_file in src_files:
        expected_file = src_file.with_suffix(".expected")

        print(f"\nProcessing: {src_file.name}")
        output = run_lexer(src_file)

        if not output:
            print(f"  ⚠️  WARNING: Empty output from lexer")
            errors += 1
            continue

        # Сохраняем в .expected
        expected_file.write_text(output, encoding='utf-8')

        if expected_file.exists():
            if expected_file.stat().st_size > 0:
                print(f"  ✅ Updated: {expected_file.name}")
                updated += 1
            else:
                print(f"  ✏️  Created: {expected_file.name}")
                created += 1

    return created, updated, errors


def main():
    print("=" * 60)
    print("  LEXER: Expected Files Generator")
    print("=" * 60)

    total_created = 0
    total_updated = 0
    total_errors = 0

    # Генерируем для valid тестов
    c, u, e = generate_for_directory(VALID_TESTS_DIR, "Valid Tests")
    total_created += c
    total_updated += u
    total_errors += e

    # Генерируем для invalid тестов
    c, u, e = generate_for_directory(INVALID_TESTS_DIR, "Invalid Tests")
    total_created += c
    total_updated += u
    total_errors += e

    # Итоговый отчёт
    print(f"\n{'=' * 60}")
    print("  GENERATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"✏️  Created: {total_created}")
    print(f"✅ Updated: {total_updated}")
    print(f"⚠️  Errors:  {total_errors}")
    print(f"{'=' * 60}\n")

    if total_errors > 0:
        print("⚠️  Some files generated with errors. Review them manually.")
        sys.exit(1)
    else:
        print("✅ All .expected files generated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()