#!/bin/bash
# demo_full.sh - Final Defense Demo for Linux/Ubuntu
# Mirrors demo_full.ps1 functionality exactly

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# ANSI Colors
B="\033[36m"; G="\033[32m"; R="\033[31m"; Y="\033[33m"; GR="\033[90m"; RESET="\033[0m"

echo -e "\n${B}========================================================${RESET}"
echo -e "${B}   MiniCompiler: Final Defense Demo${RESET}"
echo -e "${B}========================================================${RESET}\n"

# =========================================================
# PART 1: FULL TEST SUITE
# =========================================================
echo -e "${GR}[1/3] Running Full Test Suite (Lexer -> Codegen)...${RESET}"
echo -e "${GR}--------------------------------------------------------${RESET}"

python3 run_all_tests.py
TEST_CODE=$?

echo -e "${GR}--------------------------------------------------------${RESET}"
echo -e "\n--- TEST SUITE SUMMARY ---"
if [ $TEST_CODE -eq 0 ]; then
    echo -e "  ${G}✅ ALL 6 MODULES PASSED${RESET}"
    echo -e "  ${GR}Lexer | Parser | Semantic | IR | ControlFlow | Codegen${RESET}"
else
    echo -e "  ${Y}⚠️  SOME MODULES REPORTED ISSUES${RESET}"
    echo -e "  ${GR}(Proceeding to live compilation demo...)${RESET}"
fi
echo ""

# =========================================================
# PART 2: LIVE COMPILATION
# =========================================================
echo -e "${GR}[2/3] Live Compilation: examples/demo_final.src${RESET}"
TEMP_DIR="$SCRIPT_DIR/build_demo"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

ASM="$TEMP_DIR/demo.asm"
OBJ="$TEMP_DIR/demo.o"
EXE="$TEMP_DIR/demo"

# Activate venv if present
if [ -d "venv" ]; then
    source venv/bin/activate > /dev/null 2>&1
fi

# Compile
COMP_OUTPUT=$(python3 -m src.main compile --input examples/demo_final.src --output "$ASM" --verbose 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${R}ERROR: Compilation failed!${RESET}"
    exit 1
fi

echo -e "\n--- Compilation Pipeline ---"
echo "$COMP_OUTPUT" | grep -E "\[LEX\]|\[PARSE\]|\[SEMANTIC\]|\[IR\]|\[SUCCESS\]" | sed 's/^/  /'

# NASM (Linux format: elf64)
echo -n "  [NASM] Assembling... "
if nasm -f elf64 "$ASM" -o "$OBJ" > /dev/null 2>&1; then
    echo -e "${G}OK${RESET}"
else
    echo -e "${R}FAILED${RESET}"
    exit 1
fi

# GCC
echo -n "  [GCC]  Linking...     "
if gcc -o "$EXE" "$OBJ" > /dev/null 2>&1; then
    echo -e "${G}OK${RESET}"
else
    echo -e "${R}FAILED${RESET}"
    exit 1
fi

#  DISPLAY GENERATED ASSEMBLY
echo -e "\n--- Generated Assembly Code ---"
if [ -f "$ASM" ]; then
    sed 's/^/  /' "$ASM"
else
    echo -e "${Y}  (Assembly file not found)${RESET}"
fi
echo ""

# =========================================================
# PART 3: EXECUTION & FINAL
# =========================================================
echo -e "${GR}[3/3] Executing Program...${RESET}"
chmod +x "$EXE"
"$EXE" > /dev/null 2>&1
EXIT_CODE=$?

echo -e "\n--- FINAL RESULT ---"
echo "  Program Exit Code: $EXIT_CODE"
if [ "$EXIT_CODE" -eq 180 ]; then
    echo -e "  Status: ${G}SUCCESS (Expected: 180)${RESET}"
else
    echo -e "  Status: ${R}UNEXPECTED (Expected: 180)${RESET}"
fi

# Cleanup
rm -rf "$TEMP_DIR"
echo -e "\n${G} Demo Complete. Ready for defense.${RESET}\n"

# Exit 0 only if both tests and demo passed
if [ "$EXIT_CODE" -eq 180 ] && [ "$TEST_CODE" -eq 0 ]; then
    exit 0
else
    exit 1
fi