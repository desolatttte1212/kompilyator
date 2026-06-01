import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
TEST_DIR = Path(__file__).parent

def run_compiler(src_file):
    """Запускает компилятор и возвращает (stdout, stderr, returncode)"""
    res = subprocess.run(
        [sys.executable, "-m", "src.main", "compile", "--input", str(src_file)],
        capture_output=True, text=True, cwd=str(ROOT_DIR)
    )
    return res.stdout, res.stderr, res.returncode

def generate_valid():
    valid_dir = TEST_DIR / "valid"
    print("\n--- Valid Tests ---")
    for src in sorted(valid_dir.glob("*.src")):
        stdout, stderr, code = run_compiler(src)
        if code == 0:
            # Сохраняем только ASM (stdout), убираем лишние переводы строк
            asm = stdout.strip().replace('\r\n', '\n')
            src.with_suffix(".expected").write_text(asm, encoding="utf-8")
            print(f"  [UPDATED] {src.name}")
        else:
            print(f"  [SKIP] {src.name} (compilation failed)")

def generate_invalid():
    invalid_dir = TEST_DIR / "invalid"
    print("\n--- Invalid Tests ---")
    for src in sorted(invalid_dir.glob("*.src")):
        stdout, stderr, code = run_compiler(src)
        if code != 0:
            # Сохраняем точный текст ошибки из stderr
            err_msg = stderr.strip().replace('\r\n', '\n')
            src.with_suffix(".expected").write_text(err_msg, encoding="utf-8")
            print(f"  [UPDATED] {src.name}")
        else:
            print(f"  [WARN] {src.name} (expected error, but compiled successfully)")

if __name__ == "__main__":
    print("="*50)
    print("Generating Control Flow Expected Files...")
    print("="*50)
    generate_valid()
    generate_invalid()
    print("\n✅ Done. Run tests again to verify.")