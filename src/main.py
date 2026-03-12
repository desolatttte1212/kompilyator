import sys
import os
import argparse
import json
from typing import Optional

from .lexer.scanner import Scanner
from .lexer.tokens import Token, TokenType
from .parser.parser import Parser
from .parser.visitors import PrettyPrinter, DotVisitor, JsonVisitor


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
    parse_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show verbose parsing information'
    )
    parse_parser.set_defaults(func=cmd_parse)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == '__main__':
    main()