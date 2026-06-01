import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.generator import IRGenerator
from src.ir.printer import IRPrinter


def generate_ir(source_code):
    scanner = Scanner(source_code)
    tokens = scanner.scan_tokens()

    parser = Parser(tokens)
    ast = parser.parse()

    if parser.has_errors():
        return None, f"parser error: {parser.errors[0].message if hasattr(parser.errors[0], 'message') else str(parser.errors[0])}"

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    if analyzer.has_errors():
        # ✅ Безопасное получение списка ошибок
        err_list = analyzer.get_errors() if hasattr(analyzer, 'get_errors') else getattr(analyzer.errors, 'errors', [])
        if err_list:
            return None, str(err_list[0])
        return None, "semantic error: unknown"

    generator = IRGenerator()
    ir_program = generator.generate(ast)

    printer = IRPrinter(show_comments=False)
    return printer.print_program(ir_program), None


def main():
    print("🔄 Генерация .expected файлов...")

    dirs = [
        ROOT_DIR / 'tests' / 'ir' / 'generation' / 'expressions',
        ROOT_DIR / 'tests' / 'ir' / 'generation' / 'control_flow',
        ROOT_DIR / 'tests' / 'ir' / 'generation' / 'functions',
        ROOT_DIR / 'tests' / 'ir' / 'golden',
        ROOT_DIR / 'tests' / 'ir' / 'invalid',
    ]

    count = 0
    for dir_path in dirs:
        if not dir_path.exists(): continue

        for src_file in dir_path.glob('*.src'):
            try:
                source = src_file.read_text(encoding='utf-8')
                result, error = generate_ir(source)

                expected_file = src_file.with_suffix('.expected')

                if error:
                    expected_file.write_text(error.strip(), encoding='utf-8')
                    print(f"✅ Создан (error): {expected_file.relative_to(ROOT_DIR)}")
                else:
                    expected_file.write_text(result.strip(), encoding='utf-8')
                    print(f"✅ Создан: {expected_file.relative_to(ROOT_DIR)}")

                count += 1
            except Exception as e:
                print(f"❌ Ошибка в {src_file.name}: {e}")
                import traceback
                traceback.print_exc()

    print(f"\n✨ Готово! Сгенерировано {count} файлов.")


if __name__ == "__main__":
    main()