import sys
import os
import argparse
import json
from typing import Optional

# Исправленные относительные импорты
from .lexer.scanner import Scanner
from .lexer.tokens import Token, TokenType
from .parser.parser import Parser
from .parser.visitors import PrettyPrinter, DotVisitor, JsonVisitor
from .semantic.analyzer import SemanticAnalyzer
from .semantic.type_system import Types
from .ir.generator import IRGenerator
from .ir.printer import IRPrinter, CFGDotPrinter, IRJsonPrinter, print_ir, generate_cfg_dot, ir_to_json

# 🆕 Спринт 5: Импорт генератора x86-64 кода
from .codegen.x86_generator import X86Generator


def read_file(filepath: str) -> str:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Source file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def write_output(content: str, output_file: Optional[str]):
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Output written to: {output_file}", file=sys.stderr)
    else:
        print(content)


def cmd_lex(args):
    try:
        source = read_file(args.input)
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        output_lines = []
        for token in tokens:
            output_lines.append(f"{token.type.name}: {token.lexeme} (line {token.line})")

        write_output("\n".join(output_lines), args.output)
        print(f"\n[SUCCESS] Lexical analysis successful! {len(tokens)} tokens.", file=sys.stderr)

    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


def cmd_parse(args):
    try:
        source = read_file(args.input)

        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        if args.verbose:
            print(f"Tokenized {len(tokens)} tokens", file=sys.stderr)

        parser = Parser(tokens)
        ast = parser.parse()

        if parser.has_errors():
            print(f"\n[ERROR] Parsing completed with {len(parser.errors)} error(s):", file=sys.stderr)
            for error in parser.get_errors():
                print(f"  [Line {error.line}:{error.column}] {error.message}", file=sys.stderr)

            if not ast:
                sys.exit(1)

        if args.ast_format == 'text':
            printer = PrettyPrinter()
            output = printer.print(ast)
        elif args.ast_format == 'dot':
            visitor = DotVisitor()
            output = visitor.generate(ast)
        elif args.ast_format == 'json':
            visitor = JsonVisitor()
            output = visitor.to_json(ast)
        else:
            raise ValueError(f"Unknown format: {args.ast_format}")

        write_output(output, args.output)

        if not parser.has_errors():
            print("\n[SUCCESS] Parsing successful!", file=sys.stderr)
            sys.exit(0)
        else:
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_check(args):
    try:
        source = read_file(args.input)
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        if args.verbose:
            print(f"[LEX] Tokenized {len(tokens)} tokens", file=sys.stderr)

        parser = Parser(tokens)
        ast = parser.parse()

        if parser.has_errors():
            print(f"\n[ERROR] Parsing failed with {len(parser.errors)} error(s):", file=sys.stderr)
            for error in parser.get_errors():
                print(f"  [Line {error.line}:{error.column}] {error.message}", file=sys.stderr)
            sys.exit(1)

        if args.verbose:
            print(f"[PARSE] AST built successfully", file=sys.stderr)

        analyzer = SemanticAnalyzer(filename=args.input)
        decorated_ast = analyzer.analyze(ast)

        # Вывод типов или таблицы символов (если запрошено)
        if args.show_types:
            from .semantic.visitors import TypeAnnotatedPrinter
            printer = TypeAnnotatedPrinter()
            write_output(printer.print(decorated_ast), args.output)
        elif args.symbols_only:
            sym_table = analyzer.get_symbol_table()
            output = json.dumps(sym_table.to_dict(), indent=2, ensure_ascii=False) if args.format == 'json' else sym_table.dump()
            write_output(output, args.output)

        # 🔑 КЛЮЧЕВОЙ ФИКС: Явный вывод ошибок в stderr в формате, который ждёт раннер
        if analyzer.has_errors():
            error_list = getattr(analyzer, 'errors', []) or getattr(analyzer, '_errors', [])
            if not error_list:
                # Fallback, если список ошибок пуст, но флаг has_errors=True
                print("semantic error: analysis failed", file=sys.stderr)
            for err in error_list:
                print(f"semantic error: {err}", file=sys.stderr)
            sys.exit(1)
        else:
            print("[SUCCESS] Semantic analysis passed!", file=sys.stderr)
            if args.verbose and not args.show_types and not args.symbols_only:
                sym_table = analyzer.get_symbol_table()
                print(f"\n[INFO] Symbols declared: {len(sym_table.global_scope.symbols)}", file=sys.stderr)
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_symbols(args):
    try:
        source = read_file(args.input)

        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        parser = Parser(tokens)
        ast = parser.parse()

        if parser.has_errors():
            print(f"\n[ERROR] Parsing failed:", file=sys.stderr)
            for error in parser.get_errors():
                print(f"  [Line {error.line}:{error.column}] {error.message}", file=sys.stderr)
            sys.exit(1)

        analyzer = SemanticAnalyzer(filename=args.input)
        analyzer.analyze(ast)

        sym_table = analyzer.get_symbol_table()

        if args.format == 'json':
            output = json.dumps(sym_table.to_dict(), indent=2, ensure_ascii=False)
        elif args.format == 'text':
            output = sym_table.dump()
        else:
            raise ValueError(f"Unknown format: {args.format}")

        write_output(output, args.output)

        if not analyzer.has_errors():
            print(f"[SUCCESS] Symbol table dumped ({len(sym_table.global_scope.symbols)} symbols)", file=sys.stderr)
            sys.exit(0)
        else:
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_ir(args):
    try:
        source = read_file(args.input)

        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        if args.verbose:
            print(f"[LEX] Tokenized {len(tokens)} tokens", file=sys.stderr)

        parser = Parser(tokens)
        ast = parser.parse()

        if parser.has_errors():
            print(f"\n[ERROR] Parsing failed with {len(parser.errors)} error(s):", file=sys.stderr)
            for error in parser.get_errors():
                print(f"  [Line {error.line}:{error.column}] {error.message}", file=sys.stderr)
            sys.exit(1)

        if args.verbose:
            print(f"[PARSE] AST built successfully", file=sys.stderr)

        analyzer = SemanticAnalyzer(filename=args.input)
        decorated_ast = analyzer.analyze(ast)

        if analyzer.has_errors():
            print(f"\n[ERROR] Semantic analysis failed:", file=sys.stderr)
            analyzer.print_report()
            sys.exit(1)

        if args.verbose:
            print(f"[SEMANTIC] Analysis passed", file=sys.stderr)

        generator = IRGenerator(symbol_table=analyzer.get_symbol_table())
        ir_program = generator.generate(decorated_ast)

        if args.verbose:
            print(f"[IR] Generated {len(ir_program.functions)} function(s)", file=sys.stderr)

        if args.format == 'text':
            printer = IRPrinter(show_comments=not args.no_comments)
            output = printer.print_program(ir_program)
        elif args.format == 'dot':
            printer = CFGDotPrinter(show_comments=not args.no_comments)
            output = printer.generate_program(ir_program)
        elif args.format == 'json':
            printer = IRJsonPrinter(indent=2 if args.pretty else None)
            output = printer.to_json(ir_program)
        else:
            raise ValueError(f"Unknown format: {args.format}")

        write_output(output, args.output)

        if args.stats:
            print_stats(ir_program)

        print(f"\n[SUCCESS] IR generation successful!", file=sys.stderr)
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

def cmd_compile(args):
    try:
        source = read_file(args.input)

        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        if args.verbose:
            print(f"[LEX] Tokenized {len(tokens)} tokens", file=sys.stderr)

        parser = Parser(tokens)
        ast = parser.parse()

        if parser.has_errors():
            print(f"\n[ERROR] Parsing failed with {len(parser.errors)} error(s):", file=sys.stderr)
            for error in parser.get_errors():
                print(f"  [Line {error.line}:{error.column}] {error.message}", file=sys.stderr)
            sys.exit(1)

        if args.verbose:
            print(f"[PARSE] AST built successfully", file=sys.stderr)

        analyzer = SemanticAnalyzer(filename=args.input)
        decorated_ast = analyzer.analyze(ast)

        if analyzer.has_errors():
            print(f"\n[ERROR] Semantic analysis failed:", file=sys.stderr)
            analyzer.print_report()
            sys.exit(1)

        if args.verbose:
            print(f"[SEMANTIC] Analysis passed", file=sys.stderr)

        ir_generator = IRGenerator(symbol_table=analyzer.get_symbol_table())
        ir_program = ir_generator.generate(decorated_ast)
        if getattr(args, 'optimize', False):
            from .ir.optimizer import OptimizationPipeline
            optimizer = OptimizationPipeline(ir_program)
            ir_program = optimizer.run()
            if args.verbose:
                print(f"[OPTIMIZER] {optimizer.get_report()}", file=sys.stderr)

        if args.verbose:
            print(f"[IR] Generated {len(ir_program.functions)} function(s)", file=sys.stderr)

        asm_generator = X86Generator(ir_program)
        asm_code = asm_generator.generate()

        output_file = args.output or (args.input.rsplit('.', 1)[0] + '.asm')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(asm_code)

        print(f"[SUCCESS] Assembly generated: {output_file}", file=sys.stderr)
        if args.verbose:
            print("\n--- Generated Assembly ---", file=sys.stderr)
            print(asm_code, file=sys.stderr)
            print("--------------------------", file=sys.stderr)

        sys.exit(0)

    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Compilation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def print_stats(ir_program):
    total_blocks = 0
    total_instructions = 0
    instruction_counts = {}

    for func_name, func in ir_program.functions.items():
        for block in func.blocks:
            total_blocks += 1
            for instr in block.instructions:
                total_instructions += 1
                instr_type = instr.instruction_type.name
                instruction_counts[instr_type] = instruction_counts.get(instr_type, 0) + 1

    print(f"\n=== IR Statistics ===", file=sys.stderr)
    print(f"Functions: {len(ir_program.functions)}", file=sys.stderr)
    print(f"Basic Blocks: {total_blocks}", file=sys.stderr)
    print(f"Total Instructions: {total_instructions}", file=sys.stderr)
    print(f"\nInstructions by type:", file=sys.stderr)
    for instr_type, count in sorted(instruction_counts.items()):
        print(f"  {instr_type}: {count}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        prog='minicompiler',
        description='MiniCompiler - A simple compiler for educational purposes'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    lex_parser = subparsers.add_parser('lex', help='Run lexical analysis')
    lex_parser.add_argument('--input', '-i', required=True, help='Input source file')
    lex_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    lex_parser.set_defaults(func=cmd_lex)

    parse_parser = subparsers.add_parser('parse', help='Run parsing and generate AST')
    parse_parser.add_argument('--input', '-i', required=True, help='Input source file')
    parse_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parse_parser.add_argument(
        '--ast-format', '-f',
        choices=['text', 'dot', 'json'],
        default='text',
        help='AST output format (default: text)'
    )
    parse_parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose parsing information')
    parse_parser.set_defaults(func=cmd_parse)

    check_parser = subparsers.add_parser('check', help='Run semantic analysis')
    check_parser.add_argument('--input', '-i', required=True, help='Input source file')
    check_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    check_parser.add_argument('--show-types', '-t', action='store_true', help='Show type-annotated AST')
    check_parser.add_argument('--symbols-only', '-s', action='store_true', help='Show only symbol table')
    check_parser.add_argument('--format', choices=['text', 'json'], default='text',
                              help='Output format for symbols (default: text)')
    check_parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose analysis information')
    check_parser.set_defaults(func=cmd_check)

    symbols_parser = subparsers.add_parser('symbols', help='Dump symbol table')
    symbols_parser.add_argument('--input', '-i', required=True, help='Input source file')
    symbols_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    symbols_parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                                help='Output format (default: text)')
    symbols_parser.set_defaults(func=cmd_symbols)

    ir_parser = subparsers.add_parser('ir', help='Generate Intermediate Representation')
    ir_parser.add_argument('--input', '-i', required=True, help='Input source file')
    ir_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    ir_parser.add_argument('--format', '-f', choices=['text', 'dot', 'json'], default='text',
                           help='IR output format (default: text)')
    ir_parser.add_argument('--no-comments', action='store_true', help='Hide comments in output')
    ir_parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    ir_parser.add_argument('--stats', action='store_true', help='Show IR statistics')
    ir_parser.add_argument('--verbose', '-v', action='store_true', help='Show verbose generation information')
    ir_parser.set_defaults(func=cmd_ir)

    compile_parser = subparsers.add_parser('compile', help='Compile source to x86-64 assembly')
    compile_parser.add_argument('--input', '-i', required=True, help='Input source file')
    compile_parser.add_argument('--output', '-o', help='Output assembly file (default: <input>.asm)')
    compile_parser.add_argument('--verbose', '-v', action='store_true', help='Print generated assembly')
    compile_parser.add_argument('--optimize', '-O', action='store_true',
                                help='Enable IR optimizations')  # ✅ Теперь после создания
    compile_parser.set_defaults(func=cmd_compile)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()