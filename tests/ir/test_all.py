import sys
import os
from pathlib import Path

#  Настройка путей
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.lexer.scanner import Scanner
    from src.parser.parser import Parser
    from src.semantic.analyzer import SemanticAnalyzer
    from src.ir.generator import IRGenerator
    from src.ir.printer import IRPrinter
    from src.ir.operand import OperandFactory, Temporary, Variable, Literal, Label, MemoryLocation
    from src.ir.instructions import InstructionFactory, InstructionType
    from src.ir.basic_block import BasicBlock, BlockType, IRFunction
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# 🎨 Цвета
GREEN, RED, YELLOW, BLUE, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[94m", "\033[0m"


# ==========================================
# ЧАСТЬ 1: UNIT ТЕСТЫ
# ==========================================
def run_unit_tests():
    print(f"\n{BLUE}--- Part 1: Unit Tests (IR Components) ---{RESET}")
    passed = failed = 0

    try:
        temp = OperandFactory.new_temporary()
        var = OperandFactory.variable('x', 'int')
        lit = OperandFactory.literal(42)
        assert isinstance(temp, Temporary) and isinstance(var, Variable) and isinstance(lit, Literal)
        print(f"  {GREEN}[PASS]{RESET} OperandFactory works correctly")
        passed += 1
    except Exception as e:
        print(f"  {RED}[FAIL]{RESET} OperandFactory: {e}")
        failed += 1

    try:
        op = OperandFactory.new_temporary()
        inst = InstructionFactory.add(op, OperandFactory.literal(1), OperandFactory.literal(2))
        assert inst.instruction_type == InstructionType.ADD
        print(f"  {GREEN}[PASS]{RESET} Instructions created correctly")
        passed += 1
    except Exception as e:
        print(f"  {RED}[FAIL]{RESET} Instructions: {e}")
        failed += 1

    try:
        func = IRFunction(name='test', return_type='int', parameters=[])
        block = func.create_block('entry', BlockType.NORMAL)
        assert block is not None and block.label.name == 'entry'
        print(f"  {GREEN}[PASS]{RESET} Blocks and Functions structure OK")
        passed += 1
    except Exception as e:
        print(f"  {RED}[FAIL]{RESET} Blocks/Functions: {e}")
        failed += 1

    print(f"  Result: {passed} passed, {failed} failed\n")
    return failed == 0


# ==========================================
# ЧАСТЬ 2: ЯДРО КОМПИЛЯЦИИ
# ==========================================
def compile_to_ir(source_text):
    try:
        scanner = Scanner(source_text)
        tokens = scanner.scan_tokens()

        parser = Parser(tokens)
        ast = parser.parse()
        if parser.has_errors():
            return None, f"ParseError: {parser.errors[0]}"

        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        if analyzer.has_errors():
            err_msg = str(analyzer.errors[0]) if hasattr(analyzer, 'errors') and analyzer.errors else "Unknown"
            return None, f"SemanticError: {err_msg}"

        sym_table = analyzer.get_symbol_table() if hasattr(analyzer, 'get_symbol_table') else getattr(analyzer,
                                                                                                      'symbol_table',
                                                                                                      {})
        generator = IRGenerator(symbol_table=sym_table)
        ir_program = generator.generate(ast)

        printer = IRPrinter(show_comments=False)
        return printer.print_program(ir_program).strip(), None
    except Exception as e:
        return None, f"Crash: {str(e)}"


# ==========================================
# ГЕНЕРАЦИЯ .EXPECTED ФАЙЛОВ
# ==========================================
def generate_expected_files():
    print(f"\n{YELLOW}--- Generating Expected Files ---{RESET}")
    test_root = PROJECT_ROOT / 'tests' / 'ir'
    categories = [
        ('Generation (Expressions)', test_root / 'generation' / 'expressions'),
        ('Generation (Control Flow)', test_root / 'generation' / 'control_flow'),
        ('Generation (Functions)', test_root / 'generation' / 'functions'),
        ('Generation (Integration)', test_root / 'generation' / 'integration'),
        ('Golden Tests', test_root / 'golden'),
    ]

    count = 0
    for name, path in categories:
        if not path.exists(): continue
        for src_file in sorted(path.glob("*.src")):
            source_code = src_file.read_text(encoding='utf-8')
            ir_output, error = compile_to_ir(source_code)

            if error:
                print(f"  {RED}[SKIP]{RESET} {src_file.name} ({error})")
                continue

            expected_file = src_file.with_suffix('.expected')
            expected_file.write_text(ir_output + '\n', encoding='utf-8')
            print(f"  {GREEN}[UPDATED]{RESET} {expected_file.name}")
            count += 1

    print(f"\n✅ Generated/Updated {count} expected files.\n")


# ==========================================
# ЧАСТЬ 3: INTEGRATION ТЕСТЫ
# ==========================================
def run_file_tests():
    print(f"\n{BLUE}--- Part 2: Integration Tests (File Generation) ---{RESET}")
    test_root = PROJECT_ROOT / 'tests' / 'ir'

    categories = [
        ('Generation (Expressions)', test_root / 'generation' / 'expressions', False),
        ('Generation (Control Flow)', test_root / 'generation' / 'control_flow', False),
        ('Generation (Functions)', test_root / 'generation' / 'functions', False),
        ('Generation (Integration)', test_root / 'generation' / 'integration', False),
        ('Golden Tests', test_root / 'golden', False),
        ('Invalid Tests (Errors Expected)', test_root / 'invalid', True),
    ]

    total_passed = total_failed = total_skipped = 0

    for name, path, expect_errors in categories:
        if not path.exists(): continue
        src_files = sorted(path.glob("*.src"))
        if not src_files: continue

        print(f"\n  {YELLOW}Category: {name}{RESET}")
        for src_file in src_files:
            src_name = src_file.name
            expected_file = src_file.with_suffix('.expected')

            if not expected_file.exists():
                print(f"    {YELLOW}[SKIP]{RESET} {src_name} (no .expected file)")
                total_skipped += 1
                continue

            source_code = src_file.read_text(encoding='utf-8')
            expected_content = expected_file.read_text(encoding='utf-8').strip()
            actual_output, error = compile_to_ir(source_code)

            if expect_errors:
                if error:
                    if expected_content.lower() in error.lower() or error.lower() in expected_content.lower():
                        print(f"    {GREEN}[PASS]{RESET} {src_name} (error detected)")
                        total_passed += 1
                    else:
                        print(f"    {RED}[FAIL]{RESET} {src_name} (wrong error)")
                        total_failed += 1
                else:
                    print(f"    {RED}[FAIL]{RESET} {src_name} (expected error, got IR)")
                    total_failed += 1
            else:
                if error:
                    print(f"    {RED}[FAIL]{RESET} {src_name} ({error[:60]})")
                    total_failed += 1
                else:
                    if actual_output == expected_content:
                        print(f"    {GREEN}[PASS]{RESET} {src_name}")
                        total_passed += 1
                    else:
                        print(f"    {RED}[FAIL]{RESET} {src_name} (output mismatch)")
                        total_failed += 1

    print(f"\n  {BLUE}Summary:{RESET} {total_passed} passed, {total_failed} failed, {total_skipped} skipped")
    return total_failed == 0


# ==========================================
# ГЛАВНЫЙ ЗАПУСК
# ==========================================
if __name__ == "__main__":
    print(f"{'=' * 60}\n MiniCompiler Unified IR Test Runner\n{'=' * 60}")

    if '--generate' in sys.argv:
        generate_expected_files()
        sys.exit(0)

    unit_ok = run_unit_tests()
    integration_ok = run_file_tests()

    print(f"\n{'=' * 60}")
    if unit_ok and integration_ok:
        print(f"{GREEN}✅ ALL TESTS PASSED!{RESET}")
        sys.exit(0)
    else:
        print(f"{RED}❌ SOME TESTS FAILED{RESET}")
        sys.exit(1)