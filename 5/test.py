from main import XMLLexer


def main():
    # Создаем экземпляр лексического анализатора
    lexer = XMLLexer()

    # Пример XML документа
    xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
<bookstore>
    <book category="fiction">
        <title lang="en">The Great Gatsby</title>
        <author>F. Scott Fitzgerald</author>
        <year>1925</year>
        <price>15.99</price>
    </book>
    <book category="programming">
    
        <title lang="en">Clean Code</title>
        <author>Robert C. Martin</author>
        <year>2008</year>
        <price>42.99</price>
    </book>
</bookstore>'''

    print("Анализ XML документа...")
    print("-" * 60)

    # Токенизация
    tokens = lexer.tokenize(xml_data)

    # Вывод результатов
    print(f"Найдено токенов: {len(tokens)}")
    print("\nПервые 15 токенов:")
    for i, token in enumerate(tokens[:15]):
        print(f"{i + 1:3}. {token['type']:20} = '{token['value']}'")

    # Статистика
    print("\nСтатистика по типам токенов:")
    stats = {}
    for token in tokens:
        stats[token['type']] = stats.get(token['type'], 0) + 1

    for token_type, count in sorted(stats.items()):
        print(f"  {token_type:20}: {count:3}")

    # Проверка ошибок
    errors = lexer.get_errors()
    if errors:
        print(f"\nОбнаружено ошибок: {len(errors)}")
        for error in errors:
            print(f"  ⚠ {error}")
    else:
        print("\n Ошибок не обнаружено")


def analyze_file(filename):
    """Анализ XML файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        lexer = XMLLexer()
        tokens = lexer.tokenize(xml_content)

        print(f"Файл: {filename}")
        print(f"Токенов: {len(tokens)}")
        print(f"Ошибок: {len(lexer.get_errors())}")

        return tokens, lexer.get_errors()

    except FileNotFoundError:
        print(f"Файл {filename} не найден")
        return [], []


if __name__ == "__main__":
    main()

    # Для анализа файла раскомментируйте:
    # analyze_file("example.xml")