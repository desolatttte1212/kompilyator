# kompilyator

Проект компилятора для упрощенного C-подобного языка.
Parsing & AST Generation

## Структура проекта
```bash
mini-compiler/
├── src/
│   ├── lexer/                  # Спринт 1: Лексический анализ
│   │   ├── __init__.py
│   │   ├── scanner.py          # Реализация токенизатора
│   │   └── tokens.py           # Типы токенов и класс Token
│   ├── parser/                 # Спринт 2: Парсинг и AST
│   │   ├── __init__.py
│   │   ├── parser.py           # Рекурсивный спуск парсер
│   │   ├── ast_nodes.py        # Определения узлов AST
│   │   ├── visitors.py         # Посетители AST (text, dot, json)
│   │   └── grammar.txt         # Формальная спецификация грамматики
│   ├── utils/
│   │   └── __init__.py
│   └── main.py                 # Точка входа CLI
├── tests/
│   ├── lexer/
│   │   ├── valid/
│   │   ├── invalid/
│   │   └── run_tests.py
│   └── parser/
│       ├── valid/
│       ├── invalid/
│       └── run_tests.py
├── examples/
│   ├── hello.src
│   └── factorial.src
├── docs/
│   └── grammar.md
├── README.md
└── requirements.txt
```

## Установка
```bash
# Перейти в директорию проекта
cd mini-compiler

# Создать виртуальное окружение
python -m venv venv

# Активировать виртуальное окружение (Windows)
venv\Scripts\activate

# Активировать виртуальное окружение (Linux/Mac)
source venv/bin/activate

# Установить зависимости (если есть)
pip install -r requirements.txt
```
## Использование 
Лексический анализ (Спринт 1)
```bash
# Запустить лексер на исходном файле
python -m src.main lex --input examples/hello.src

# Сохранить токены в файл
python -m src.main lex --input examples/hello.src --output tokens.txt

# Режим подробного вывода
python -m src.main lex --input examples/hello.src --verbose
```
Парсинг и генерация AST (Спринт 2)
```bash
# Разобрать и вывести AST в текстовом формате
python -m src.main parse --input examples/hello.src --ast-format text

# Сгенерировать Graphviz DOT файл для визуализации
python -m src.main parse --input examples/hello.src --ast-format dot --output ast.dot

# Сгенерировать JSON вывод (для тестирования и автоматизации)
python -m src.main parse --input examples/hello.src --ast-format json --output ast.json

# Режим подробного вывода (показать количество токенов и информацию о парсинге)
python -m src.main parse --input examples/hello.src --verbose

# Комбинировать опции
python -m src.main parse --input examples/hello.src --ast-format dot --output ast.dot --verbose
```
Визуализация AST с помощью Graphviz
```bash
# Сгенерировать DOT файл
python -m src.main parse --input examples/hello.src --ast-format dot --output ast.dot

# Конвертировать DOT в PNG (требуется установленный Graphviz)
dot -Tpng ast.dot -o ast.png
