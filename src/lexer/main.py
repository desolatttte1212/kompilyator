import sys
import argparse
from .scanner import Scanner


def main():
    parser = argparse.ArgumentParser(description="MiniCompiler Lexer")
    parser.add_argument("command", choices=["lex"], help="Command to run")
    parser.add_argument("--input", required=True, help="Input source file")
    parser.add_argument("--output", help="Output tokens file (default: stdout)")

    args = parser.parse_args()

    if args.command == "lex":
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                source = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.input}' not found.")
            sys.exit(1)

        scanner = Scanner(source)
        tokens = scanner.scan_tokens()

        output_lines = [str(token) for token in tokens]
        result = "\n".join(output_lines)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result + "\n")
        else:
            print(result)


if __name__ == "__main__":
    main()