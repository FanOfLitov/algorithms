import unittest
import tempfile
import os
from xml_lexer import XMLLexer, validate_xml_syntax, create_xml_example


class TestXMLLexerSimple(unittest.TestCase):
    """Упрощенные тесты XML лексического анализатора"""

    def setUp(self):
        """Настройка перед каждым тестом"""
        self.lexer = XMLLexer(debug=False)

    def test_basic_xml_parsing(self):
        """Тест базового парсинга XML"""
        xml = "<root>text</root>"
        tokens = self.lexer.tokenize(xml)

        self.assertGreater(len(tokens), 0)
        self.assertEqual(len(self.lexer.get_errors()), 0)

    def test_xml_with_attributes(self):
        """Тест XML с атрибутами"""
        xml = '<element attr="value"></element>'
        tokens = self.lexer.tokenize(xml)

        token_types = [t['type'] for t in tokens]
        self.assertIn('IDENTIFIER', token_types)
        self.assertIn('STRING', token_types)
        self.assertEqual(len(self.lexer.get_errors()), 0)

    def test_xml_comment(self):
        """Тест XML комментариев"""
        xml = '<!-- comment -->'
        tokens = self.lexer.tokenize(xml)

        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0]['type'], 'COMMENT')
        self.assertEqual(len(self.lexer.get_errors()), 0)

    def test_self_closing_tag(self):
        """Тест самозакрывающегося тега"""
        xml = '<br/>'
        tokens = self.lexer.tokenize(xml)

        # Должен быть открывающий тег, идентификатор, слэш и закрывающий тег
        self.assertGreaterEqual(len(tokens), 4)
        self.assertEqual(len(self.lexer.get_errors()), 0)

    def test_processing_instruction(self):
        """Тест инструкции обработки"""
        xml = '<?xml version="1.0"?>'
        tokens = self.lexer.tokenize(xml)

        self.assertGreater(len(tokens), 0)
        self.assertEqual(tokens[0]['type'], 'PROCESSING_INSTR')
        self.assertEqual(len(self.lexer.get_errors()), 0)

    def test_char_reference(self):
        """Тест символьных ссылок (исправлено регулярное выражение)"""
        xml = '&#65;'  # Символ 'A'
        tokens = self.lexer.tokenize(xml)

        # Проверяем, что токен CHAR_REF был распознан
        char_refs = [t for t in tokens if t['type'] == 'CHAR_REF']
        self.assertGreater(len(char_refs), 0)
        self.assertEqual(len(self.lexer.get_errors()), 0)

    def test_entity_reference(self):
        """Тест ссылок на сущности"""
        xml = '&amp;' & в
        XML
        tokens = self.lexer.tokenize(xml)

        entity_refs = [t for t in tokens if t['type'] == 'ENTITY_REF']
        self.assertGreater(len(entity_refs), 0)
        self.assertEqual(len(self.lexer.get_errors()), 0)

    def test_complex_xml_structure(self):
        """Тест сложной XML структуры"""
        xml = create_xml_example()
        tokens = self.lexer.tokenize(xml)

        self.assertGreater(len(tokens), 0)
        self.assertEqual(len(self.lexer.get_errors()), 0)

        # Анализ структуры
        structure = self.lexer.analyze_xml_structure(tokens)
        self.assertTrue(structure['well_formed'])

    def test_invalid_xml(self):
        """Тест некорректного XML"""
        xml = '<open>text<not closed>'
        tokens = self.lexer.tokenize(xml)

        structure = self.lexer.analyze_xml_structure(tokens)
        self.assertFalse(structure['well_formed'])

    def test_empty_xml(self):
        """Тест пустого XML"""
        xml = ''
        tokens = self.lexer.tokenize(xml)

        self.assertEqual(len(tokens), 0)
        self.assertEqual(len(self.lexer.get_errors()), 0)

    def test_whitespace_handling(self):
        """Тест обработки пробелов"""
        xml = '  <tag>  text  </tag>  '
        tokens = self.lexer.tokenize(xml)

        # Находим текстовый токен
        text_tokens = [t for t in tokens if t['type'] == 'TEXT']
        self.assertEqual(len(text_tokens), 1)
        self.assertEqual(text_tokens[0]['value'], 'text')
        self.assertEqual(len(self.lexer.get_errors()), 0)

    def test_statistics_collection(self):
        """Тест сбора статистики"""
        xml = '<test>data</test>'
        tokens = self.lexer.tokenize(xml)
        stats = self.lexer.get_statistics()

        self.assertIn('total_tokens', stats)
        self.assertIn('token_types', stats)
        self.assertIn('errors', stats)
        self.assertGreater(stats['total_tokens'], 0)

    def test_export_import(self):
        """Тест экспорта токенов"""
        xml = '<test>data</test>'
        tokens = self.lexer.tokenize(xml)

        # Экспортируем в файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            self.lexer.export_tokens(temp_file, 'json')

            # Проверяем, что файл создан
            self.assertTrue(os.path.exists(temp_file))
            self.assertGreater(os.path.getsize(temp_file), 0)

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestXMLValidation(unittest.TestCase):
    """Тесты валидации XML"""

    def test_valid_xml_validation(self):
        """Тест валидации корректного XML"""
        xml = '''<?xml version="1.0"?>
        <root>
            <child>text</child>
        </root>'''

        result = validate_xml_syntax(xml)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    def test_invalid_xml_validation(self):
        """Тест валидации некорректного XML"""
        xml = '<open>text'
        result = validate_xml_syntax(xml)

        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)


def run_tests():
    """Запуск всех тестов"""
    print("Запуск тестов XML лексического анализатора...")
    print("=" * 60)

    # Создаем тестовый набор
    suite = unittest.TestLoader().loadTestsFromTestCase(TestXMLLexerSimple)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestXMLValidation))

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 60)
    print(f"Всего тестов: {result.testsRun}")
    print(f"Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Провалено: {len(result.failures)}")
    print(f"Ошибок: {len(result.errors)}")

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()

    if success:
        print("\nВсе тесты пройдены успешно!")
    else:
        print("\nЕсть непройденные тесты!")