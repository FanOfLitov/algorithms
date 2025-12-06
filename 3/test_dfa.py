"""
Тесты для программы моделирования ДКА
Запуск: python test_dfa.py
       или: py test_dfa.py
"""

import unittest
import tempfile
import os
import sys

# Добавляем текущую директорию в путь Python
sys.path.append('.')

try:
    from main import DFA
except ImportError:
    print("Ошибка: Не удалось импортировать модуль main.py")
    print("Убедитесь, что файл main.py находится в той же директории.")
    sys.exit(1)


class TestDFA(unittest.TestCase):
    """Тесты для программы моделирования ДКА"""

    def setUp(self):
        """Создание тестового ДКА перед каждым тестом"""
        # Тестовый ДКА из исходного задания
        self.dfa_csv_content = """,a,b,Final
q0,q1,q0,0
q1,q1,q2,0
q2,q1,q0,1"""

        # Создаем временный файл с ДКА
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        self.temp_file.write(self.dfa_csv_content)
        self.temp_file.close()

        # Инициализируем DFA объект
        self.dfa = DFA(self.temp_file.name)

    def tearDown(self):
        """Удаление временных файлов после каждого теста"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_dfa_initialization(self):
        """Тест инициализации ДКА"""
        info = self.dfa.get_info()

        self.assertEqual(info['num_states'], 3)
        self.assertEqual(info['alphabet'], ['a', 'b'])
        self.assertEqual(info['start_state'], 'q0')
        self.assertEqual(info['final_states'], ['q2'])
        self.assertEqual(sorted(info['states']), ['q0', 'q1', 'q2'])

    def test_dfa_accepts_correct_strings(self):
        """Тест: ДКА должен допускать правильные цепочки"""
        test_cases = [
            ("ab", True),      # q0->q1->q2
            ("bab", True),     # q0->q0->q1->q2 (ВАЖНО: этот тест был исправлен!)
            ("abab", True),    # q0->q1->q2->q1->q2
            ("ababab", True),  # q0->q1->q2->q1->q2->q1->q2
        ]

        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                is_accepted, _ = self.dfa.validate_string(input_str)
                self.assertEqual(is_accepted, expected,
                               f"Цепочка '{input_str}' должна {'допускаться' if expected else 'не допускаться'}")

    def test_dfa_rejects_incorrect_strings(self):
        """Тест: ДКА должен отвергать неправильные цепочки"""
        test_cases = [
            ("", False),       # Пустая строка
            ("a", False),      # q0->q1
            ("b", False),      # q0->q0
            ("ba", False),     # q0->q0->q1
            ("aba", False),    # q0->q1->q2->q1
            # ("bab", True),   # УДАЛЕНО: эта цепочка теперь допускается!
            ("aa", False),     # q0->q1->q1
            ("bb", False),     # q0->q0->q0
            ("bba", False),    # q0->q0->q0->q1
            ("abb", False),    # q0->q1->q2->q0
        ]

        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                is_accepted, _ = self.dfa.validate_string(input_str)
                self.assertEqual(is_accepted, expected,
                               f"Цепочка '{input_str}' должна {'допускаться' if expected else 'не допускаться'}")

    def test_dfa_state_transitions(self):
        """Тест проверки последовательности состояний"""
        test_cases = [
            ("ab", ['q0', 'q1', 'q2']),
            ("aba", ['q0', 'q1', 'q2', 'q1']),
            ("bab", ['q0', 'q0', 'q1', 'q2']),  # ДОБАВЛЕНО
            ("abab", ['q0', 'q1', 'q2', 'q1', 'q2']),
            ("b", ['q0', 'q0']),
            ("a", ['q0', 'q1']),
        ]

        for input_str, expected_states in test_cases:
            with self.subTest(input_str=input_str):
                _, state_sequence = self.dfa.validate_string(input_str)
                self.assertEqual(state_sequence, expected_states,
                               f"Для цепочки '{input_str}' ожидалась последовательность {expected_states}, получена {state_sequence}")

    def test_dfa_invalid_symbols(self):
        """Тест обработки недопустимых символов"""
        test_cases = [
            ("abc", False),  # содержит 'c' - НОВАЯ ЛОГИКА: цепочка отвергается
            ("123", False),  # цифры
            ("a b", False),  # пробел
            ("a+b", False),  # символ '+'
        ]

        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                is_accepted, state_sequence = self.dfa.validate_string(input_str)
                self.assertFalse(is_accepted, f"Цепочка с недопустимым символом '{input_str}' должна отвергаться")
                # ИСПРАВЛЕНО: больше не проверяем длину последовательности состояний
                # Просто убеждаемся, что цепочка не допускается

    def test_dfa_edge_cases(self):
        """Тест граничных случаев"""
        # Очень длинная цепочка
        long_string = "ab" * 1000
        is_accepted, states = self.dfa.validate_string(long_string)
        # "ab" повторяется четное число раз (2000 символов), должно допускаться
        self.assertTrue(is_accepted)
        self.assertEqual(states[-1], 'q2')

        # Цепочка из одного символа 'b' повторяется много раз
        long_b_string = "b" * 100
        is_accepted, states = self.dfa.validate_string(long_b_string)
        self.assertFalse(is_accepted)  # Все 'b' ведут в q0, который не конечный
        self.assertEqual(states[-1], 'q0')


class TestInteractiveDFA(unittest.TestCase):
    """Тесты для интерактивного использования ДКА"""

    def test_empty_string(self):
        """Тест пустой строки"""
        dfa_csv = """,a,b,Final
q0,q1,q0,0
q1,q1,q2,0
q2,q1,q0,1"""

        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        temp_file.write(dfa_csv)
        temp_file.close()

        try:
            dfa = DFA(temp_file.name)
            is_accepted, states = dfa.validate_string("")
            self.assertFalse(is_accepted)
            self.assertEqual(states, ['q0'])
        finally:
            os.unlink(temp_file.name)

    def test_only_valid_symbols(self):
        """Тест только допустимых символов"""
        dfa_csv = """,a,b,Final
q0,q1,q0,0
q1,q1,q2,0
q2,q1,q0,1"""

        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        temp_file.write(dfa_csv)
        temp_file.close()

        try:
            dfa = DFA(temp_file.name)
            # Тест различных комбинаций
            test_cases = [
                ("ab", True),
                ("abab", True),
                ("abababab", True),
                ("ababababab", True),
                ("a", False),
                ("aa", False),
                ("aaa", False),
                ("b", False),
                ("bb", False),
                ("bbb", False),
            ]

            for input_str, expected in test_cases:
                with self.subTest(input_str=input_str):
                    is_accepted, _ = dfa.validate_string(input_str)
                    self.assertEqual(is_accepted, expected)
        finally:
            os.unlink(temp_file.name)


class TestDFAFromFile(unittest.TestCase):
    """Тесты ДКА загруженного из файла"""

    def test_load_from_actual_file(self):
        """Тест загрузки ДКА из реального файла"""
        # Создаем временный файл с ДКА
        dfa_csv = """,a,b,Final
q0,q1,q0,0
q1,q1,q2,0
q2,q1,q0,1"""

        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        temp_file.write(dfa_csv)
        temp_file.close()

        try:
            # Загружаем ДКА
            dfa = DFA(temp_file.name)

            # Проверяем информацию о ДКА
            info = dfa.get_info()
            self.assertEqual(info['alphabet'], ['a', 'b'])
            self.assertEqual(info['start_state'], 'q0')
            self.assertEqual(info['final_states'], ['q2'])

            # Проверяем несколько цепочек
            test_cases = [
                ("ab", True),
                ("bab", True),
                ("abab", True),
                ("aba", False),
                ("", False),
                ("a", False),
            ]

            for input_str, expected in test_cases:
                with self.subTest(input_str=input_str):
                    is_accepted, _ = dfa.validate_string(input_str)
                    self.assertEqual(is_accepted, expected)
        finally:
            os.unlink(temp_file.name)


def run_all_tests():
    """Запуск всех тестов с красивым выводом"""
    print("\n" + "="*80)
    print("ТЕСТИРОВАНИЕ ПРОГРАММЫ ДКА")
    print("="*80)

    # Загружаем тесты
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDFA)
    suite.addTests(loader.loadTestsFromTestCase(TestInteractiveDFA))
    suite.addTests(loader.loadTestsFromTestCase(TestDFAFromFile))

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Выводим итоги
    print("\n" + "="*80)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*80)
    print(f"Всего тестов: {result.testsRun}")

    if result.failures or result.errors:
        failed_count = len(result.failures) + len(result.errors)
        print(f"Не пройдено: {failed_count}")

        if result.failures:
            print(f"\nНеудачные тесты ({len(result.failures)}):")
            for test, traceback in result.failures:
                test_name = test.id().split('.')[-1]
                print(f"  - {test_name}")

        if result.errors:
            print(f"\nОшибки в тестах ({len(result.errors)}):")
            for test, traceback in result.errors:
                test_name = test.id().split('.')[-1]
                print(f"  - {test_name}")

        print("\n" + "="*80)
        print(")bad( ТЕСТЫ НЕ ПРОЙДЕНЫ")
        # Показываем детали только для первого неудачного теста
        if result.failures:
            print(f"\nДетали первой ошибки:")
            test, traceback = result.failures[0]
            print(traceback)
    else:
        print(")good( ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")

    print("="*80)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    # Возвращаем код выхода для CI/CD
    sys.exit(0 if success else 1)