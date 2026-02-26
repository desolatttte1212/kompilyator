# kompilyator

Проект компилятора для упрощенного C-подобного языка.
**Текущий спринт:** Sprint 1 - Лексический анализ (Tokenization).

## Структура проекта
- `src/lexer`: Реализация сканера и токенов.
- `tests/lexer`: Набор тестов (valid/invalid).
- `docs/language_spec.md`: Спецификация языка (EBNF).

## Быстрый старт

### Установка
```bash
python -m venv .venv
source .venv/bin/activate  # или .venv\Scripts\Activate.ps1
pip install -e .
