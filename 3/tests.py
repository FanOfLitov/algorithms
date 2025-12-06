import unittest
import tempfile
import os
from main import read_dfa_from_csv, minimize_dfa_table, minimize_dfa_hopcroft, DFA, are_equivalent


class TestDFA(unittest.TestCase):

    def setUp(self):
        """Создание тестового CSV файла"""
        self.csv_content = """state,a,b,accept
q0,q1,q2,
q1,q2,q3,
q2,q2,q2,
q3,q3,q3,*"""

        # Создаем временный файл
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        self.temp_file.write(self.csv_content)
        self.temp_file.close()

    def tearDown(self):
        """Удаление временного файла"""
        os.unlink(self.temp_file.name)

    def test_read_dfa_from_csv(self):
        """Тест чтения ДКА из CSV"""
        dfa = read_dfa_from_csv(self.temp_file.name)

        self.assertIsInstance(dfa, DFA)
        self.assertEqual(len(dfa.states), 5)  # 4 состояния + trap
        self.assertEqual(dfa.alphabet, {'a', 'b'})
        self.assertEqual(dfa.start_state, 'q0')
        self.assertEqual(dfa.accept_states, {'q3'})

    def test_process_input(self):
        """Тест обработки входных строк"""
        dfa = read_dfa_from_csv(self.temp_file.name)

        # Тестовые строки
        test_cases = [
            ("", False),  # пустая строка
            ("a", False),  # q0 -> q1
            ("b", False),  # q0 -> q2
            ("aa", False),  # q0->q1->q2
            ("ab", True),  # q0->q1->q3 (принимается)
            ("aba", True),  # q0->q1->q3->q3
            ("abb", True),  # q0->q1->q3->q3
            ("ba", False),  # q0->q2->q2
            ("bb", False),  # q0->q2->q2
            ("aaa", False),  # q0->q1->q2->q2
        ]

        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                result = dfa.process_input(input_str)
                self.assertEqual(result, expected)

    def test_minimization_table(self):
        """Тест минимизации табличным методом"""
        dfa = read_dfa_from_csv(self.temp_file.name)
        minimized = minimize_dfa_table(dfa)

        # Проверяем, что минимизированный автомат имеет меньше состояний
        self.assertLessEqual(len(minimized.states), len(dfa.states))

        # Проверяем эквивалентность на тестовых строках
        test_strings = ["", "a", "b", "aa", "ab", "ba", "bb", "aba", "bab"]
        for test_str in test_strings:
            original_result = dfa.process_input(test_str)
            minimized_result = minimized.process_input(test_str)
            self.assertEqual(original_result, minimized_result,
                             f"Различие на строке '{test_str}'")

    def test_minimization_hopcroft(self):
        """Тест минимизации алгоритмом Хопкрофта"""
        dfa = read_dfa_from_csv(self.temp_file.name)
        minimized = minimize_dfa_hopcroft(dfa)

        # Проверяем эквивалентность
        test_strings = ["", "a", "b", "aa", "ab", "ba", "bb"]
        for test_str in test_strings:
            original_result = dfa.process_input(test_str)
            minimized_result = minimized.process_input(test_str)
            self.assertEqual(original_result, minimized_result)

    def test_equivalence_check(self):
        """Тест проверки эквивалентности"""
        dfa1 = read_dfa_from_csv(self.temp_file.name)
        dfa2 = minimize_dfa_table(dfa1)

        equivalent, message = are_equivalent(dfa1, dfa2)
        self.assertTrue(equivalent, message)

    def test_invalid_symbol(self):
        """Тест обработки недопустимого символа"""
        dfa = read_dfa_from_csv(self.temp_file.name)

        with self.assertRaises(ValueError):
            dfa.process_input("acb")  # 'c' нет в алфавите

    def test_dfa_creation(self):
        """Тест создания ДКА вручную"""
        states = {'q0', 'q1', 'q2'}
        alphabet = {'0', '1'}
        transitions = {
            'q0': {'0': 'q1', '1': 'q0'},
            'q1': {'0': 'q2', '1': 'q1'},
            'q2': {'0': 'q2', '1': 'q2'}
        }
        start_state = 'q0'
        accept_states = {'q2'}

        dfa = DFA(states, alphabet, transitions, start_state, accept_states)

        self.assertTrue(dfa.process_input("00"))  # q0->q1->q2
        self.assertFalse(dfa.process_input("01"))  # q0->q1->q1
        self.assertTrue(dfa.process_input("000"))  # q0->q1->q2->q2

    def test_empty_string(self):
        """Тест обработки пустой строки"""
        # Создаем отдельный временный файл
        csv_content = """state,a,b,accept
q0,q0,q0,*"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_filename = f.name

        try:
            dfa = read_dfa_from_csv(temp_filename)
            # Пустая строка должна приниматься, так как q0 - допускающее состояние
            self.assertTrue(dfa.process_input(""))
            self.assertFalse(dfa.process_input("a"))
        finally:
            os.unlink(temp_filename)

    def test_only_valid_symbols(self):
        """Тест проверки только допустимых символов"""
        dfa = read_dfa_from_csv(self.temp_file.name)

        # Все символы в строке должны быть из алфавита
        self.assertTrue(all(c in dfa.alphabet for c in "ababba"))

        # Попытка использовать недопустимый символ вызывает исключение
        with self.assertRaises(ValueError):
            dfa.process_input("abc")


if __name__ == '__main__':
    unittest.main(verbosity=2)