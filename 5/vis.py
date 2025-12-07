import json
import os
from xml_lexer import XMLLexer, create_xml_example


class SimpleVisualizer:
    """Простая визуализация работы XML лексического анализатора"""

    def __init__(self):
        pass

    def display_tokens(self, tokens, title="Токены XML", max_display=20):
        """Отображение токенов в виде простой таблицы"""
        print(f"\n{title}")
        print("=" * 80)
        print(f"{'#':>3} {'Тип':<20} {'Значение':<30} {'Строка':>6} {'Позиция':>8}")
        print("-" * 80)

        for i, token in enumerate(tokens[:max_display], 1):
            value = str(token['value'])
            if len(value) > 27:
                value = value[:24] + "..."

            print(f"{i:3d} {token['type']:<20} {value:<30} {token['lineno']:>6} {token['lexpos']:>8}")

        if len(tokens) > max_display:
            print(f"... и еще {len(tokens) - max_display} токенов")

    def display_xml_highlighted(self, xml, max_lines=20):
        """Отображение XML с простой подсветкой"""
        print("\nИсходный XML:")
        print("=" * 80)

        lines = xml.split('\n')
        for i, line in enumerate(lines[:max_lines], 1):
            # Простая подсветка
            line_highlighted = line
            line_highlighted = line_highlighted.replace('<', '\033[91m<\033[0m')  # Красный
            line_highlighted = line_highlighted.replace('>', '\033[91m>\033[0m')  # Красный
            line_highlighted = line_highlighted.replace('</', '\033[91m</\033[0m')  # Красный
            line_highlighted = line_highlighted.replace('<!--', '\033[92m<!--\033[0m')  # Зеленый
            line_highlighted = line_highlighted.replace('-->', '\033[92m-->\033[0m')  # Зеленый
            line_highlighted = line_highlighted.replace('<?', '\033[93m<?\033[0m')  # Желтый
            line_highlighted = line_highlighted.replace('?>', '\033[93m?>\033[0m')  # Желтый

            print(f"{i:3}: {line_highlighted}")

        if len(lines) > max_lines:
            print(f"... и еще {len(lines) - max_lines} строк")

    def display_statistics(self, stats, structure):
        """Отображение статистики"""
        print("\nСтатистика анализа:")
        print("-" * 40)
        print(f"Всего токенов: {stats['total_tokens']}")
        print(f"Ошибок: {stats['errors']}")
        print(f"Строк обработано: {stats['lines_processed']}")
        print(f"Изменений состояний: {stats['states_changes']}")

        print(f"\nТипы токенов:")
        for token_type, count in stats['token_types'].items():
            print(f"  {token_type}: {count}")

        print(f"\nСтруктура XML:")
        print(f"  Тегов: {len(structure['tags'])}")
        print(f"  Атрибутов: {len(structure['attributes'])}")
        print(f"  Текстовых узлов: {len(structure['text_nodes'])}")
        print(f"  Комментариев: {len(structure['comments'])}")
        print(f"  CDATA секций: {len(structure['cdata_sections'])}")
        print(f"  Корректность: {'ДА' if structure['well_formed'] else 'НЕТ'}")

        if not structure['well_formed']:
            print(f"  Незакрытые теги: {', '.join(structure['unclosed_tags'])}")

    def create_text_report(self, xml, tokens, stats, structure, filename="xml_analysis_report.txt"):
        """Создание текстового отчета"""
        report = "=" * 80 + "\n"
        report += "ОТЧЕТ ОБ АНАЛИЗЕ XML\n"
        report += "=" * 80 + "\n\n"

        report += "Статистика:\n"
        report += f"  Всего токенов: {stats['total_tokens']}\n"
        report += f"  Ошибок: {stats['errors']}\n"
        report += f"  Строк обработано: {stats['lines_processed']}\n"
        report += f"  Корректность XML: {'ДА' if structure['well_formed'] else 'НЕТ'}\n\n"

        report += "Типы токенов:\n"
        for token_type, count in stats['token_types'].items():
            report += f"  {token_type}: {count}\n"

        report += "\nСтруктура XML:\n"
        report += f"  Тегов: {len(structure['tags'])}\n"
        report += f"  Атрибутов: {len(structure['attributes'])}\n"
        report += f"  Текстовых узлов: {len(structure['text_nodes'])}\n"
        report += f"  Комментариев: {len(structure['comments'])}\n"

        report += "\nПервые 20 токенов:\n"
        for i, token in enumerate(tokens[:20], 1):
            value = str(token['value'])
            if len(value) > 50:
                value = value[:47] + "..."
            report += f"  {i:3}. {token['type']:20} = '{value}' (строка {token['lineno']})\n"

        # Сохраняем отчет
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"Текстовый отчет сохранен в {filename}")
        return filename


def visualize_xml_analysis():
    """Визуализация анализа XML"""
    print("Визуализация работы XML лексического анализатора")
    print("=" * 60)

    visualizer = SimpleVisualizer()

    # Пример XML
    xml = create_xml_example()

    # Анализ
    lexer = XMLLexer()
    tokens = lexer.tokenize(xml)
    stats = lexer.get_statistics()
    structure = lexer.analyze_xml_structure(tokens)

    # Отображение результатов
    visualizer.display_xml_highlighted(xml)
    visualizer.display_statistics(stats, structure)
    visualizer.display_tokens(tokens)

    # Создание отчета
    report_file = visualizer.create_text_report(xml, tokens, stats, structure)

    # Экспорт токенов в JSON
    export_json = input("\nЭкспортировать токены в JSON? (y/n): ").strip().lower()
    if export_json == 'y':
        lexer.export_tokens("tokens.json", 'json')
        print("Токены экспортированы в tokens.json")

    print(f"\nАнализ завершен. Отчет сохранен в {report_file}")


def visualize_state_transitions(lexer):
    """Визуализация переходов между состояниями"""
    print("\nПереходы между состояниями лексера:")
    print("-" * 60)

    state_history = lexer.get_state_history()

    if not state_history:
        print("Нет переходов между состояниями")
        return

    print(f"{'Переход':<30} {'Позиция':>10}")
    print("-" * 40)

    for transition, position in state_history:
        print(f"{transition:<30} {position:>10}")

    # Статистика по состояниям
    state_counts = {}
    for transition, _ in state_history:
        state = transition.split()[0]
        if state not in state_counts:
            state_counts[state] = 0
        state_counts[state] += 1

    print(f"\nСтатистика по состояниям:")
    for state, count in state_counts.items():
        print(f"  {state}: {count} переходов")


def main():
    """Основная функция"""
    print("XML Лексический анализатор с визуализацией")
    print("=" * 60)

    while True:
        print("\nМеню:")
        print("1. Визуализировать стандартный пример")
        print("2. Загрузить XML из файла")
        print("3. Ввести XML вручную")
        print("4. Показать переходы состояний")
        print("5. Выход")

        choice = input("\nВыберите действие (1-5): ").strip()

        visualizer = SimpleVisualizer()

        if choice == '1':
            xml = create_xml_example()
            analyze_and_visualize(xml, visualizer, "Стандартный пример")

        elif choice == '2':
            filename = input("Введите имя файла: ").strip()
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        xml = f.read()
                    analyze_and_visualize(xml, visualizer, f"Файл: {filename}")
                except Exception as e:
                    print(f"Ошибка чтения файла: {e}")
            else:
                print(f"Файл {filename} не найден")

        elif choice == '3':
            print("\nВведите XML (для завершения введите пустую строку):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            xml = "\n".join(lines)
            if xml.strip():
                analyze_and_visualize(xml, visualizer, "Введенный XML")
            else:
                print("XML не введен")

        elif choice == '4':
            xml = create_xml_example()
            lexer = XMLLexer()
            tokens = lexer.tokenize(xml)
            visualize_state_transitions(lexer)

        elif choice == '5':
            print("Выход из программы")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")


def analyze_and_visualize(xml: str, visualizer: SimpleVisualizer, title: str):
    """Анализ XML и визуализация результатов"""
    print(f"\n{title}")
    print("=" * 60)

    try:
        lexer = XMLLexer()
        tokens = lexer.tokenize(xml)
        stats = lexer.get_statistics()
        structure = lexer.analyze_xml_structure(tokens)

        # Отображение
        visualizer.display_xml_highlighted(xml[:500] + "..." if len(xml) > 500 else xml)
        visualizer.display_statistics(stats, structure)
        visualizer.display_tokens(tokens[:30], "Первые 30 токенов")

        if lexer.get_errors():
            print("\nОшибки:")
            for error in lexer.get_errors():
                print(f"  - {error}")

        # Создание отчета
        report_name = input("\nСоздать текстовый отчет? (y/n): ").strip().lower()
        if report_name == 'y':
            filename = input("Имя файла отчета (по умолчанию report.txt): ").strip()
            if not filename:
                filename = "report.txt"
            visualizer.create_text_report(xml, tokens, stats, structure, filename)

        # Экспорт токенов
        export = input("\nЭкспортировать токены в JSON? (y/n): ").strip().lower()
        if export == 'y':
            filename = input("Имя файла (по умолчанию tokens.json): ").strip()
            if not filename:
                filename = "tokens.json"
            lexer.export_tokens(filename, 'json')
            print(f"Токены экспортированы в {filename}")

    except Exception as e:
        print(f"Ошибка при анализе XML: {e}")


if __name__ == "__main__":
    main()