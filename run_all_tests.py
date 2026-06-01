import sys
import subprocess
import time
from pathlib import Path

#  Цвета для консоли
C = {
    "GREEN": "\033[92m", "RED": "\033[91m", "YELLOW": "\033[93m",
    "BLUE": "\033[94m", "CYAN": "\033[96m", "BOLD": "\033[1m", "RESET": "\033[0m"
}

PROJECT_ROOT = Path(__file__).resolve().parent

# 📋 Список тестовых модулей (Название, Путь к скрипту)
TEST_SUITES = [
    ("🔤 Lexer",           "tests/lexer/test_runner.py"),
    ("🌳 Parser",          "tests/parser/run_test.py"),
    ("🔍 Semantic",        "tests/semantic/run_tests.py"),
    ("📦 IR Generation",   "tests/ir/test_all.py"),
    ("🔀 Control Flow",    "tests/control_flow/run_tests.py"),
    ("⚙️ Codegen",         "tests/codegen/run_tests.py"),
]

def run_suite(name, script_rel_path):
    script_path = PROJECT_ROOT / script_rel_path
    if not script_path.exists():
        print(f"\n{C['YELLOW']}⚠️  Пропуск {name}: файл не найден{C['RESET']}")
        return 0.0, True

    print(f"\n{'='*60}")
    print(f"{C['BOLD']}{C['CYAN']}🚀 Запуск: {name}{C['RESET']}")
    print(f"{'='*60}")

    start = time.time()
    try:
        # Запускаем в корне проекта, вывод транслируем в консоль в реальном времени
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            check=False,  # Не прерываем при ошибке, обрабатываем код возврата сами
            text=True
        )
        elapsed = time.time() - start
        success = (proc.returncode == 0)
        return elapsed, success
    except Exception as e:
        print(f"\n{C['RED']}💥 Ошибка запуска {name}: {e}{C['RESET']}")
        return 0.0, False

def main():
    print(f"\n{C['BOLD']}{C['BLUE']}")
    print("══════════════════════════════════════════════════╗")
    print("║  🧪 MiniCompiler: Full Test Suite Runner       ║")
    print("╚══════════════════════════════════════════════════╝")
    print(f"{C['RESET']}")

    results = []
    all_passed = True

    for name, path in TEST_SUITES:
        elapsed, success = run_suite(name, path)
        results.append((name, success, elapsed))
        if not success:
            all_passed = False

    #  Финальный отчёт
    print(f"\n{'='*60}")
    print(f"{C['BOLD']}{C['BLUE']}📊 ИТОГОВЫЙ ОТЧЁТ{C['RESET']}")
    print(f"{'='*60}")

    for name, success, elapsed in results:
        status = f"{C['GREEN']}✅ PASSED{C['RESET']}" if success else f"{C['RED']} FAILED{C['RESET']}"
        print(f"  {name:<25} {status}  ({elapsed:.2f}s)")

    print(f"\n{'='*60}")
    if all_passed:
        print(f"{C['BOLD']}{C['GREEN']}🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО! 🎉{C['RESET']}")
    else:
        print(f"{C['BOLD']}{C['RED']}⚠️  ОБНАРУЖЕНЫ ОШИБКИ В ОДНОМ ИЛИ НЕСКОЛЬКИХ МОДУЛЯХ ⚠️{C['RESET']}")
    print(f"{'='*60}\n")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()