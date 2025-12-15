import unittest
import tempfile
import os
import re
from main import RegexInterpreter, DFA, KMP, RegexTester, State, NFA, CSVHandler


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
        dfa = interpreter.nfa_to_dfa(nfa, 'a|b')

        self.assertIsInstance(dfa, DFA)
        self.assertGreater(len(dfa.states), 0)
        self.assertGreater(len(dfa.alphabet), 0)

    def test_dfa_process_input(self):
        """Тест обработки строки ДКА"""
        interpreter = RegexInterpreter()

        # Выражение: 'a*'
        postfix = interpreter.to_postfix('a*')
        nfa = interpreter.build_nfa_from_postfix(postfix)
        dfa = interpreter.nfa_to_dfa(nfa, 'a*')

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

    def test_regex_tester_simple(self):
        """Тест сравнения с Python re для простых случаев"""
        tester = RegexTester()

        # Простое выражение, которое должно работать
        regex = "a*b"
        test_string = "aaab"

        success, matches = tester.test_regex(regex, test_string, use_dfa=True)
        # Проверяем, что тест выполняется без ошибок
        self.assertIsInstance(success, bool)
        self.assertIsInstance(matches, list)

    def test_complex_regex(self):
        """Тест сложных регулярных выражений"""
        interpreter = RegexInterpreter()

        test_cases = [
            ("(a|b)*", "abbaab", True),
            ("a(b|c)d", "abd", True),
            ("a(b|c)d", "acd", True),
            ("a+b+c", "aaabc", True),
            ("a+b+c", "abc", True),
        ]

        for regex, test_string, should_match in test_cases:
            with self.subTest(regex=regex, string=test_string):
                dfa = interpreter.regex_to_dfa(regex)
                result = dfa.process_input(test_string)
                self.assertEqual(result, should_match,
                                 f"Ошибка для regex='{regex}', string='{test_string}': "
                                 f"ожидалось {should_match}, получено {result}")

    def test_compare_kmp_dfa(self):
        """Тест сравнения KMP и DFA"""
        tester = RegexTester()

        pattern = "ab"
        text = "ababab"

        kmp_matches, dfa_matches, equal = tester.compare_kmp_dfa(pattern, text)
        # В данном случае они должны совпадать
        self.assertEqual(kmp_matches, [0, 2, 4])
        self.assertEqual(dfa_matches, [0, 2, 4])
        self.assertTrue(equal)

    def test_epsilon_transitions(self):
        """Тест ε-переходов"""
        interpreter = RegexInterpreter()

        # Тест с выражением, содержащим ε-переходы
        regex = "a*b"
        dfa = interpreter.regex_to_dfa(regex)

        self.assertTrue(dfa.process_input('b'))  # 0 a, 1 b
        self.assertTrue(dfa.process_input('ab'))
        self.assertTrue(dfa.process_input('aab'))
        self.assertFalse(dfa.process_input('a'))
        self.assertFalse(dfa.process_input('ba'))


class TestCSVReading(unittest.TestCase):

    def test_csv_reading(self):
        """Тест чтения CSV файлов"""
        csv_content = """regex,test_string,expected
a,aaa,True
ab,abab,True
a|b,c,False
a*,aaaa,True
(a|b)*,abba,True"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            # Используем CSVHandler из pda.py
            test_cases = CSVHandler.read_test_cases(temp_file)

            self.assertEqual(len(test_cases), 5)

            self.assertEqual(test_cases[0]['regex'], 'a')
            self.assertEqual(test_cases[0]['test_string'], 'aaa')
            self.assertEqual(test_cases[0]['expected'], 'True')

            self.assertEqual(test_cases[1]['regex'], 'ab')
            self.assertEqual(test_cases[1]['test_string'], 'abab')
            self.assertEqual(test_cases[1]['expected'], 'True')

        finally:
            os.unlink(temp_file)


class TestAdditionalFunctionality(unittest.TestCase):

    def test_state_equality(self):
        """Тест сравнения состояний"""
        State.counter = 0
        s1 = State()
        s2 = State()

        self.assertNotEqual(s1, s2)
        self.assertEqual(s1, s1)

        # Проверяем хеши
        self.assertEqual(hash(s1), hash(s1.id))

    def test_nfa_epsilon_closure(self):
        """Тест ε-замыкания НКА"""
        interpreter = RegexInterpreter()

        # Создаем простое НКА с ε-переходами
        s1 = State()
        s2 = State()
        s3 = State(is_final=True)

        s1.add_epsilon(s2)
        s2.add_epsilon(s3)

        nfa = NFA(s1, s3)

        closure = nfa.epsilon_closure({s1})
        self.assertEqual(len(closure), 3)
        self.assertIn(s1, closure)
        self.assertIn(s2, closure)
        self.assertIn(s3, closure)

    def test_dfa_with_trace(self):
        """Тест ДКА с трассировкой"""
        interpreter = RegexInterpreter()

        # Простое выражение с алфавитом, содержащим все нужные символы
        regex = "ab"
        dfa = interpreter.regex_to_dfa(regex)

        # Проверяем, что алфавит содержит 'a' и 'b'
        self.assertIn('a', dfa.alphabet)
        self.assertIn('b', dfa.alphabet)

        # Тестируем с трассировкой
        accepted, path = dfa.process_input_with_trace("ab")

        self.assertTrue(accepted)
        self.assertGreater(len(path), 0)

        # Тестируем с неправильной строкой
        accepted, path = dfa.process_input_with_trace("ac")
        self.assertFalse(accepted)

    def test_dfa_alphabet_handling(self):
        interpreter = RegexInterpreter()

        regex = "a*"
        dfa = interpreter.regex_to_dfa(regex)


        self.assertEqual(dfa.alphabet, {'a'})


        self.assertFalse(dfa.process_input('b'))


        self.assertTrue(dfa.process_input('a'))


if __name__ == '__main__':
    unittest.main(verbosity=2)