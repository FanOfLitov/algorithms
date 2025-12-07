import unittest
import tempfile
import os
import re
from main import RegexInterpreter, DFA, KMP, RegexTester, State, NFA


class TestRegexInterpreter(unittest.TestCase):

    def setUp(self):
        """Сброс счетчика состояний перед каждым тестом"""
        State.counter = 0

    def test_to_postfix_simple(self):
        """Тест преобразования в обратную польскую запись"""
        interpreter = RegexInterpreter()

        test_cases = [
            ("a", "a"),
            ("ab", "ab."),
            ("a|b", "ab|"),
            ("a*", "a*"),
            ("(a|b)c", "ab|c."),
            ("a+b", "a+b."),
        ]

        for regex, expected in test_cases:
            with self.subTest(regex=regex):
                result = interpreter.to_postfix(regex)
                self.assertEqual(result, expected)

    def test_build_nfa_simple(self):
        """Тест построения НКА"""
        interpreter = RegexInterpreter()

        # Простое выражение: 'a'
        postfix = interpreter.to_postfix('a')
        nfa = interpreter.build_nfa_from_postfix(postfix)

        self.assertIsNotNone(nfa.start)
        self.assertIsNotNone(nfa.end)
        self.assertTrue(nfa.end.is_final)

    def test_nfa_process_input(self):
        """Тест обработки строки НКА"""
        interpreter = RegexInterpreter()

        # Выражение: 'ab'
        postfix = interpreter.to_postfix('ab')
        nfa = interpreter.build_nfa_from_postfix(postfix)

        self.assertTrue(nfa.process_input('ab'))
        self.assertFalse(nfa.process_input('a'))
        self.assertFalse(nfa.process_input('b'))
        self.assertFalse(nfa.process_input('abc'))

    def test_nfa_to_dfa_conversion(self):
        """Тест преобразования НКА в ДКА"""
        interpreter = RegexInterpreter()

        # Выражение: 'a|b'
        postfix = interpreter.to_postfix('a|b')
        nfa = interpreter.build_nfa_from_postfix(postfix)
        dfa = interpreter.nfa_to_dfa(nfa)

        self.assertIsInstance(dfa, DFA)
        self.assertGreater(len(dfa.states), 0)
        self.assertGreater(len(dfa.alphabet), 0)

    def test_dfa_process_input(self):
        """Тест обработки строки ДКА"""
        interpreter = RegexInterpreter()

        # Выражение: 'a*'
        postfix = interpreter.to_postfix('a*')
        nfa = interpreter.build_nfa_from_postfix(postfix)
        dfa = interpreter.nfa_to_dfa(nfa)

        # Должно принимать пустую строку и строки из 'a'
        self.assertTrue(dfa.process_input(''))
        self.assertTrue(dfa.process_input('a'))
        self.assertTrue(dfa.process_input('aa'))
        self.assertTrue(dfa.process_input('aaa'))

        # Не должно принимать строки с 'b'
        self.assertFalse(dfa.process_input('b'))
        self.assertFalse(dfa.process_input('ab'))

    def test_kmp_algorithm(self):
        """Тест алгоритма Кнута-Морриса-Пратта"""
        test_cases = [
            ("ababc", "abababcabababc", [2, 9]),
            ("aaa", "aaaaa", [0, 1, 2]),
            ("abc", "def", []),
            ("", "abc", []),
            ("a", "aaaa", [0, 1, 2, 3]),
        ]

        for pattern, text, expected in test_cases:
            with self.subTest(pattern=pattern, text=text):
                result = KMP.search(text, pattern)
                self.assertEqual(result, expected)

    def test_regex_tester(self):
        """Тест сравнения с Python re"""
        tester = RegexTester()

        # Простое выражение
        regex = "a+b"
        test_string = "aaab"

        success, matches = tester.test_regex(regex, test_string, use_dfa=True)
        self.assertTrue(success)

        # Проверяем, что нашли совпадение
        python_matches = [m.start() for m in re.finditer(regex, test_string)]
        self.assertEqual(matches, python_matches)

    def test_complex_regex(self):
        """Тест сложных регулярных выражений"""
        interpreter = RegexInterpreter()
        tester = RegexTester()

        test_cases = [
            ("(a|b)*", "abbaab", True),
            ("a(b|c)d", "acd", False),  # Должно быть abd или acd
            ("a(b|c)d", "abd", True),
            ("a(b|c)d", "acd", True),
            ("a+b+c", "aaabc", True),
            ("a+b+c", "abc", False),
        ]

        for regex, test_string, should_match in test_cases:
            with self.subTest(regex=regex, string=test_string):
                postfix = interpreter.to_postfix(regex)
                nfa = interpreter.build_nfa_from_postfix(postfix)
                dfa = interpreter.nfa_to_dfa(nfa)

                result = dfa.process_input(test_string)
                self.assertEqual(result, should_match)

    def test_compare_kmp_dfa(self):
        """Тест сравнения KMP и ДКА"""
        tester = RegexTester()

        pattern = "ab"
        text = "ababab"

        kmp_matches, dfa_matches, equal = tester.compare_kmp_dfa(pattern, text)
        self.assertTrue(equal)
        self.assertEqual(kmp_matches, [0, 2, 4])
        self.assertEqual(dfa_matches, [0, 2, 4])

    def test_epsilon_transitions(self):
        """Тест ε-переходов"""
        interpreter = RegexInterpreter()

        # Выражение с ε-переходами: (a|ε)b
        postfix = interpreter.to_postfix("(a|)b")
        nfa = interpreter.build_nfa_from_postfix(postfix)

        # Должно принимать 'b' и 'ab'
        self.assertTrue(nfa.process_input('b'))
        self.assertTrue(nfa.process_input('ab'))
        self.assertFalse(nfa.process_input('a'))
        self.assertFalse(nfa.process_input('ba'))


class TestCSVReading(unittest.TestCase):
    """Тесты для чтения из CSV"""

    def test_csv_reading(self):
        """Тест чтения тестовых случаев из CSV"""
        csv_content = """regex,test_string,expected
a,aaa,True
ab,abab,True
a|b,c,False
a*,aaaa,True
(a|b)*,abba,True"""

        # Создаем временный CSV файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            # Читаем CSV
            test_cases = read_test_cases_from_csv(temp_file)

            # Проверяем количество тестов
            self.assertEqual(len(test_cases), 5)

            # Проверяем первый тест
            self.assertEqual(test_cases[0]['regex'], 'a')
            self.assertEqual(test_cases[0]['test_string'], 'aaa')
            self.assertEqual(test_cases[0]['expected'], 'True')

        finally:
            os.unlink(temp_file)


def read_test_cases_from_csv(filepath):
    """Чтение тестовых случаев из CSV файла"""
    test_cases = []

    try:
        import csv
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                test_cases.append(row)
    except ImportError:
        # Если csv не доступен, создаем тестовые данные вручную
        print("CSV модуль не доступен, пропускаем тест CSV")

    return test_cases


if __name__ == '__main__':
    unittest.main(verbosity=2)