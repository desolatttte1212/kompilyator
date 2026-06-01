# MiniCompiler Makefile
# Для Linux/macOS/WSL. (Windows: используйте .ps1/.bat скрипты напрямую)

PYTHON ?= python3
MYCC   ?= ./mycc
NASM   ?= nasm
GCC    ?= gcc

BUILD_DIR  ?= build
DEMO_SRC   := examples/demo_final.src
DEMO_ASM   := $(BUILD_DIR)/demo.asm
DEMO_OBJ   := $(BUILD_DIR)/demo.o
DEMO_EXE   := $(BUILD_DIR)/demo

.PHONY: all test demo compile-demo run-demo clean help install

# Цель по умолчанию
all: help

# 🧪 Запуск всех тестов
test:
	@echo "🧪 Running full test suite..."
	$(PYTHON) run_all_tests.py

# 🚀 Запуск полного демо-скрипта
demo:
	@echo " Running interactive demo..."
	chmod +x demo_full.sh
	./demo_full.sh

#  Пошаговая сборка демо
compile-demo: $(DEMO_EXE)
	@echo "✅ Demo executable ready: $(DEMO_EXE)"

$(BUILD_DIR):
	mkdir -p $@

$(DEMO_ASM): $(DEMO_SRC) | $(BUILD_DIR)
	$(MYCC) compile --input $< --output $@ --verbose

$(DEMO_OBJ): $(DEMO_ASM)
	$(NASM) -f elf64 $< -o $@

$(DEMO_EXE): $(DEMO_OBJ)
	$(GCC) $< -o $@

# ▶️ Запуск собранного демо
run-demo: $(DEMO_EXE)
	@echo "▶️  Executing demo..."
	./$(DEMO_EXE)
	@echo "Exit code: $$?"

# 🧹 Очистка артефактов и кэшей
clean:
	@echo "🧹 Cleaning build artifacts & caches..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf $(BUILD_DIR) build_tmp build_demo 2>/dev/null || true
	find . -name "*.asm" -o -name "*.obj" -o -name "*.o" -o -name "*.exe" | xargs rm -f 2>/dev/null || true
	@echo "✨ Clean complete."

# ❓ Справка
help:
	@echo "MiniCompiler (Sprint 8) - Makefile"
	@echo "=================================="
	@echo "make test          Run all test suites (Lexer → Codegen)"
	@echo "make demo          Run full demo script (tests + compile + run)"
	@echo "make compile-demo  Build demo executable step-by-step"
	@echo "make run-demo      Build & run demo executable"
	@echo "make clean         Remove generated files & Python caches"
	@echo "make help          Show this message"
	@echo ""
	@echo "Direct usage: $(MYCC) --help"

# 📦 Подсказка по установке
install:
	@echo "To install globally:"
	@echo "  sudo cp mycc /usr/local/bin/ && sudo chmod +x /usr/local/bin/mycc"