import ply.lex as lex
import re
from typing import List, Dict, Tuple, Any
import json
import os


class XMLLexer:
    """Лексический анализатор для подмножества XML"""

    # Определение токенов
    tokens = (
        'TAG_OPEN',  # <
        'TAG_CLOSE',  # >
        'SLASH',  # /
        'EQUALS',  # =
        'IDENTIFIER',  # Имя тега или атрибута
        'STRING',  # Строковое значение в кавычках
        'TEXT',  # Текстовое содержимое
        'COMMENT',  # <!-- комментарий -->
        'CDATA',  # <![CDATA[ ... ]]>
        'PROCESSING_INSTR',  # <? ... ?>
        'DOCTYPE',  # <!DOCTYPE ... >
        'ENTITY_REF',  # &entity;
        'CHAR_REF',  # &#xHH; или &#DDD;
    )

    # Состояния для обработки специальных конструкций
    states = (
        ('comment', 'exclusive'),
        ('cdata', 'exclusive'),
        ('pi', 'exclusive'),
        ('doctype', 'exclusive'),
    )

    # Игнорируемые символы в основном состоянии
    t_ignore = ' \t\r'

    # ---- Правила для основного состояния (INITIAL) ----

    # Простые токены
    t_TAG_OPEN = r'<'
    t_TAG_CLOSE = r'>'
    t_SLASH = r'/'
    t_EQUALS = r'='

    # Идентификаторы (имена тегов и атрибутов)
    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_\-:\.]*'
        return t

    # Строковые значения
    def t_STRING(self, t):
        r'"[^"]*"|\'[^\']*\''  # Упрощенное выражение для строк
        t.value = t.value[1:-1]  # Убираем кавычки
        return t

    # Текстовое содержимое
    def t_TEXT(self, t):
        r'[^<&\r\n]+'  # Не включает <, &, переносы строк
        if t.value.strip():  # Пропускаем текст, состоящий только из пробелов
            return t
        else:
            # Пропускаем пробельный текст
            pass

    # Комментарии
    def t_COMMENT(self, t):
        r'<!--.*?-->'
        t.value = t.value[4:-3]  # Убираем <!-- и -->
        return t

    # CDATA секции
    def t_CDATA(self, t):
        r'<!\[CDATA\[.*?\]\]>'
        t.value = t.value[9:-3]  # Убираем <![CDATA[ и ]]>
        return t

    # Инструкции обработки
    def t_PROCESSING_INSTR(self, t):
        r'<\?.*?\?>'
        t.value = t.value[2:-2]  # Убираем <? и ?>
        return t

    # DOCTYPE
    def t_DOCTYPE(self, t):
        r'<!DOCTYPE.*?>'
        t.value = t.value[9:-1]  # Убираем <!DOCTYPE и >
        return t

    # Ссылки на сущности
    def t_ENTITY_REF(self, t):
        r'&[a-zA-Z][a-zA-Z0-9]*;'
        return t

    # Символьные ссылки (исправлено!)
    def t_CHAR_REF(self, t):
        r'&#[0-9]+;|&#x[0-9a-fA-F]+;'
        return t

    # Отслеживание номеров строк
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # Обработка ошибок в основном состоянии
    def t_error(self, t):
        # Пропускаем недопустимый символ
        t.lexer.skip(1)

    # ---- Правила для состояния комментариев ----

    # Игнорируем пробелы в комментариях
    t_comment_ignore = ' \t\r'

    def t_comment_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # Конец комментария
    def t_comment_end(self, t):
        r'-->'
        t.lexer.begin('INITIAL')
        t.type = 'COMMENT'
        t.value = t.lexer.comment_content
        return t

    # Содержимое комментария
    def t_comment_content(self, t):
        r'[^-]+'
        if hasattr(t.lexer, 'comment_content'):
            t.lexer.comment_content += t.value
        else:
            t.lexer.comment_content = t.value

    # Тире в комментарии (часть содержимого или маркер конца)
    def t_comment_dash(self, t):
        r'-'
        if hasattr(t.lexer, 'comment_content'):
            t.lexer.comment_content += t.value

    # Ошибки в комментариях
    def t_comment_error(self, t):
        # Пропускаем недопустимый символ
        t.lexer.skip(1)

    # ---- Правила для состояния CDATA ----

    t_cdata_ignore = ' \t\r'

    def t_cdata_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # Конец CDATA
    def t_cdata_end(self, t):
        r'\]\]>'
        t.lexer.begin('INITIAL')
        t.type = 'CDATA'
        t.value = t.lexer.cdata_content
        return t

    # Содержимое CDATA
    def t_cdata_content(self, t):
        r'[^\]]+'
        if hasattr(t.lexer, 'cdata_content'):
            t.lexer.cdata_content += t.value
        else:
            t.lexer.cdata_content = t.value

    # Скобка в CDATA
    def t_cdata_bracket(self, t):
        r'\]'
        if hasattr(t.lexer, 'cdata_content'):
            t.lexer.cdata_content += t.value

    # Ошибки в CDATA
    def t_cdata_error(self, t):
        t.lexer.skip(1)

    # ---- Инициализация и вспомогательные методы ----

    def __init__(self, debug: bool = False):
        """Инициализация лексического анализатора"""
        self.lexer = None
        self.errors: List[str] = []
        self.tokens_log: List[Dict[str, Any]] = []

        try:
            self.lexer = lex.lex(module=self, debug=debug)
            self.lexer.lineno = 1
        except Exception as e:
            self.errors.append(f"Ошибка инициализации лексера: {e}")
            raise

    def reset(self):
        """Сброс состояния лексера"""
        if self.lexer:
            self.lexer.lineno = 1
            self.lexer.input('')
        self.errors = []
        self.tokens_log = []

    def tokenize(self, data: str) -> List[Dict[str, Any]]:
        """Токенизация входных данных"""
        if not self.lexer:
            raise RuntimeError("Лексер не инициализирован")

        self.reset()
        self.lexer.input(data)
        tokens = []

        while True:
            tok = self.lexer.token()
            if not tok:
                break
            token_info = {
                'type': tok.type,
                'value': tok.value,
                'lineno': tok.lineno,
                'lexpos': tok.lexpos,
            }
            tokens.append(token_info)
            self.tokens_log.append(token_info)

        return tokens

    def get_errors(self) -> List[str]:
        """Получить список ошибок"""
        return self.errors

    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику по токенам"""
        stats = {
            'total_tokens': len(self.tokens_log),
            'token_types': {},
            'errors': len(self.errors),
            'lines_processed': self.lexer.lineno - 1 if self.lexer and self.lexer.lineno > 1 else 0
        }

        for token in self.tokens_log:
            token_type = token['type']
            if token_type not in stats['token_types']:
                stats['token_types'][token_type] = 0
            stats['token_types'][token_type] += 1

        return stats

    def analyze_xml_structure(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ структуры XML на основе токенов"""
        structure = {
            'tags': [],
            'attributes': [],
            'text_nodes': [],
            'comments': [],
            'cdata_sections': [],
            'processing_instructions': [],
            'doctype': None,
            'entity_refs': [],
            'char_refs': []
        }

        tag_stack = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token['type'] == 'TAG_OPEN':
                if i + 1 < len(tokens) and tokens[i + 1]['type'] == 'SLASH':
                    # Закрывающий тег
                    if tag_stack and i + 2 < len(tokens):
                        tag_name = tokens[i + 2]['value'] if tokens[i + 2]['type'] == 'IDENTIFIER' else 'unknown'
                        structure['tags'].append({
                            'type': 'closing',
                            'name': tag_name,
                            'lineno': token['lineno'],
                        })
                        if tag_stack and tag_stack[-1] == tag_name:
                            tag_stack.pop()
                else:
                    # Открывающий тег
                    tag_info = {
                        'type': 'opening',
                        'name': '',
                        'attributes': [],
                        'self_closing': False,
                        'lineno': token['lineno'],
                    }

                    # Ищем имя тега и атрибуты
                    j = i + 1
                    while j < len(tokens) and tokens[j]['type'] != 'TAG_CLOSE':
                        if tokens[j]['type'] == 'IDENTIFIER' and not tag_info['name']:
                            tag_info['name'] = tokens[j]['value']
                        elif tokens[j]['type'] == 'SLASH' and j + 1 < len(tokens) and tokens[j + 1][
                            'type'] == 'TAG_CLOSE':
                            tag_info['self_closing'] = True
                        elif tokens[j]['type'] == 'IDENTIFIER' and tokens[j]['value'] != tag_info['name']:
                            # Атрибут
                            attr_info = {'name': tokens[j]['value'], 'value': None}
                            if j + 2 < len(tokens) and tokens[j + 1]['type'] == 'EQUALS' and tokens[j + 2][
                                'type'] == 'STRING':
                                attr_info['value'] = tokens[j + 2]['value']
                                structure['attributes'].append({
                                    'tag': tag_info['name'],
                                    **attr_info,
                                    'lineno': tokens[j]['lineno']
                                })
                            tag_info['attributes'].append(attr_info)
                        j += 1

                    structure['tags'].append(tag_info)
                    if not tag_info['self_closing'] and tag_info['name']:
                        tag_stack.append(tag_info['name'])

            elif token['type'] == 'TEXT' and token['value'].strip():
                structure['text_nodes'].append({
                    'content': token['value'],
                    'lineno': token['lineno'],
                    'parent_tag': tag_stack[-1] if tag_stack else None
                })

            elif token['type'] == 'COMMENT':
                structure['comments'].append({
                    'content': token['value'],
                    'lineno': token['lineno']
                })

            elif token['type'] == 'CDATA':
                structure['cdata_sections'].append({
                    'content': token['value'],
                    'lineno': token['lineno']
                })

            elif token['type'] == 'PROCESSING_INSTR':
                structure['processing_instructions'].append({
                    'content': token['value'],
                    'lineno': token['lineno']
                })

            elif token['type'] == 'DOCTYPE':
                structure['doctype'] = {
                    'content': token['value'],
                    'lineno': token['lineno']
                }

            elif token['type'] == 'ENTITY_REF':
                structure['entity_refs'].append({
                    'content': token['value'],
                    'lineno': token['lineno']
                })

            elif token['type'] == 'CHAR_REF':
                structure['char_refs'].append({
                    'content': token['value'],
                    'lineno': token['lineno']
                })

            i += 1

        structure['nesting_depth'] = len(tag_stack)
        structure['well_formed'] = len(tag_stack) == 0
        structure['unclosed_tags'] = tag_stack.copy()

        return structure

    def export_tokens(self, filename: str, format: str = 'json'):
        """Экспорт токенов в файл"""
        if format == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.tokens_log, f, indent=2, ensure_ascii=False)
        elif format == 'csv':
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['type', 'value', 'lineno', 'lexpos'])
                writer.writeheader()
                writer.writerows(self.tokens_log)
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")


def create_xml_example() -> str:
    """Создание примера XML для тестирования"""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE bookstore SYSTEM "books.dtd">
<!-- Это комментарий -->
<bookstore>
    <book category="cooking">
        <title lang="en">Everyday Italian</title>
        <author>Giada De Laurentiis</author>
        <year>2005</year>
        <price>30.00</price>
        <description><![CDATA[Это <не> тег внутри CDATA]]></description>
    </book>
    <book category="children">
        <title lang="en">Harry Potter</title>
        <author>J.K. Rowling</author>
        <year>2005</year>
        <price>29.99</price>
    </book>
    <book category="web" cover="paperback">
        <title lang="en">Learning XML</title>
        <author>Erik T. Ray</author>
        <year>2003</year>
        <price>39.95</price>
    </book>
    <empty-element/>
</bookstore>'''


def simple_demo():
    """Простая демонстрация работы лексического анализатора"""
    print("XML Лексический анализатор - Демонстрация")
    print("=" * 60)

    # Простой XML для тестирования
    test_xml = '''<?xml version="1.0"?>
<root>
    <element attr="value">Text content</element>
    <!-- Comment -->
    <empty/>
</root>'''

    print("Тестовый XML:")
    print(test_xml)
    print("-" * 60)

    try:
        # Создаем лексер
        lexer = XMLLexer()

        # Токенизация
        tokens = lexer.tokenize(test_xml)

        print(f"\nУспешно распознано токенов: {len(tokens)}")

        # Выводим токены
        print("\nТокены:")
        for i, token in enumerate(tokens, 1):
            value = str(token['value'])
            if len(value) > 30:
                value = value[:27] + "..."
            print(f"  {i:3}. {token['type']:20} = '{value}' (строка {token['lineno']})")

        # Анализ структуры
        structure = lexer.analyze_xml_structure(tokens)

        print(f"\nСтруктура XML:")
        print(f"  Теги: {len(structure['tags'])}")
        print(f"  Атрибуты: {len(structure['attributes'])}")
        print(f"  Текстовые узлы: {len(structure['text_nodes'])}")
        print(f"  Комментарии: {len(structure['comments'])}")
        print(f"  Корректность: {'ДА' if structure['well_formed'] else 'НЕТ'}")

        if not structure['well_formed']:
            print(f"  Незакрытые теги: {structure['unclosed_tags']}")

        # Статистика
        stats = lexer.get_statistics()
        print(f"\nСтатистика:")
        print(f"  Всего токенов: {stats['total_tokens']}")
        print(f"  Типы токенов:")
        for token_type, count in stats['token_types'].items():
            print(f"    {token_type}: {count}")

        return True

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complex_example():
    """Тест сложного примера XML"""
    print("\n" + "=" * 60)
    print("Тест сложного XML")
    print("=" * 60)

    xml = create_xml_example()

    try:
        lexer = XMLLexer()
        tokens = lexer.tokenize(xml)

        print(f"Успешно распознано токенов: {len(tokens)}")

        # Быстрый анализ
        structure = lexer.analyze_xml_structure(tokens)

        print(f"\nСтруктура:")
        print(f"  Теги: {len(structure['tags'])}")
        print(f"  Атрибуты: {len(structure['attributes'])}")
        print(f"  Комментарии: {len(structure['comments'])}")
        print(f"  CDATA: {len(structure['cdata_sections'])}")
        print(f"  DOCTYPE: {'есть' if structure['doctype'] else 'нет'}")
        print(f"  Корректность: {'ДА' if structure['well_formed'] else 'НЕТ'}")

        # Показываем несколько интересных токенов
        print("\nНекоторые интересные токены:")
        interesting_types = ['PROCESSING_INSTR', 'DOCTYPE', 'COMMENT', 'CDATA', 'ENTITY_REF', 'CHAR_REF']
        count = 0
        for token in tokens:
            if token['type'] in interesting_types and count < 5:
                print(f"  {token['type']:20} = '{token['value']}'")
                count += 1

        return True

    except Exception as e:
        print(f"Ошибка: {e}")
        return False


def interactive_mode():
    """Интерактивный режим работы"""
    print("\n" + "=" * 60)
    print("Интерактивный режим")
    print("=" * 60)

    while True:
        print("\nВыберите действие:")
        print("1. Протестировать простой пример")
        print("2. Протестировать сложный пример")
        print("3. Ввести XML вручную")
        print("4. Загрузить XML из файла")
        print("5. Выход")

        choice = input("\nВаш выбор (1-5): ").strip()

        if choice == '1':
            simple_demo()

        elif choice == '2':
            test_complex_example()

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
                analyze_custom_xml(xml, "Введенный XML")
            else:
                print("XML не введен")

        elif choice == '4':
            filename = input("Введите имя файла: ").strip()
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        xml = f.read()
                    analyze_custom_xml(xml, f"Файл: {filename}")
                except Exception as e:
                    print(f"Ошибка чтения файла: {e}")
            else:
                print(f"Файл {filename} не найден")

        elif choice == '5':
            print("Выход из программы")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")


def analyze_custom_xml(xml: str, title: str):
    """Анализ пользовательского XML"""
    print(f"\n{title}")
    print("-" * 60)

    try:
        lexer = XMLLexer()
        tokens = lexer.tokenize(xml)

        print(f"Всего токенов: {len(tokens)}")

        if len(tokens) > 0:
            # Выводим первые 10 токенов
            print("\nПервые 10 токенов:")
            for i, token in enumerate(tokens[:10], 1):
                value = str(token['value'])
                if len(value) > 30:
                    value = value[:27] + "..."
                print(f"  {i:3}. {token['type']:20} = '{value}'")

            # Анализ структуры
            structure = lexer.analyze_xml_structure(tokens)

            print(f"\nСтруктура XML:")
            print(f"  Теги: {len(structure['tags'])}")
            print(f"  Атрибуты: {len(structure['attributes'])}")
            print(f"  Текстовые узлы: {len(structure['text_nodes'])}")
            print(f"  Комментарии: {len(structure['comments'])}")
            print(f"  Корректность: {'ДА' if structure['well_formed'] else 'НЕТ'}")

            if not structure['well_formed']:
                print(f"  Незакрытые теги: {structure['unclosed_tags']}")

            # Экспорт
            export = input("\nЭкспортировать токены в файл? (y/n): ").strip().lower()
            if export == 'y':
                filename = input("Имя файла (без расширения): ").strip()
                if filename:
                    lexer.export_tokens(f"{filename}.json", 'json')
                    print(f"Токены экспортированы в {filename}.json")
        else:
            print("Не распознано ни одного токена")

    except Exception as e:
        print(f"Ошибка при анализе XML: {e}")


if __name__ == "__main__":
    print("XML Лексический анализатор на PLY")
    print("=" * 60)

    # Запуск простой демонстрации
    if simple_demo():
        # После успешной демонстрации предлагаем интерактивный режим
        run_interactive = input("\nЗапустить интерактивный режим? (y/n): ").strip().lower()
        if run_interactive == 'y':
            interactive_mode()
        else:
            print("\nЗавершение работы программы")
    else:
        print("\nПрограмма завершена с ошибками")