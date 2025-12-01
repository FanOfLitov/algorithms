import unittest
import tempfile
import csv
import os
from main import DFA


class TestDFA(unittest.TestCase):
    """Тесты для программы моделирования ДКА"""

    def setUp(self):
        """Создание тестовых CSV файлов перед каждым тестом"""
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
            ("ab", True),  # q0->q1->q2
            ("abab", True),  # q0->q1->q2->q1->q2
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
            ("", False),  # Пустая строка
            ("a", False),  # q0->q1
            ("b", False),  # q0->q0
            ("ba", False),  # q0->q0->q1
            ("aba", False),  # q0->q1->q2->q1
            ("bab", False),  # q0->q0->q1->q2
            ("aa", False),  # q0->q1->q1
            ("bb", False),  # q0->q0->q0
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
            "abc",  # содержит 'c'
            "123",  # цифры
            "a b",  # пробел
            "a+b",  # символ '+'
        ]

        for input_str in test_cases:
            with self.subTest(input_str=input_str):
                is_accepted, state_sequence = self.dfa.validate_string(input_str)
                self.assertFalse(is_accepted, f"Цепочка с недопустимым символом '{input_str}' должна отвергаться")
                # Проверяем, что автомат остановился на первом состоянии
                self.assertEqual(len(state_sequence), 1,
                                 f"Для цепочки с недопустимым символом должна быть только начальное состояние")

    def test_dfa_complex_sequences(self):
        """Тест сложных последовательностей"""
        test_cases = [
            ("ab" * 10, True),  # 20 символов, должна допускаться
            ("ab" * 10 + "a", False),  # 21 символ, не должна допускаться
            ("b" * 100, False),  # 100 символов 'b', не должна допускаться
            ("ab" * 50, True),  # 100 символов, должна допускаться
        ]

        for input_str, expected in test_cases:
            with self.subTest(input_str=f"len={len(input_str)}"):
                is_accepted, _ = self.dfa.validate_string(input_str)
                self.assertEqual(is_accepted, expected,
                                 f"Цепочка длины {len(input_str)} должна {'допускаться' if expected else 'не допускаться'}")


class TestCustomDFA(unittest.TestCase):
    """Тесты для пользовательских ДКА"""

    def test_dfa_with_custom_alphabet(self):
        """Тест ДКА с пользовательским алфавитом"""
        # Создаем ДКА с алфавитом {0, 1}
        csv_content = """,0,1,Final
q0,q1,q0,0
q1,q1,q2,0
q2,q1,q0,1"""

        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        temp_file.write(csv_content)
        temp_file.close()

        try:
            dfa = DFA(temp_file.name)

            # Тестируем
            test_cases = [
                ("01", True),  # q0->q1->q2
                ("0101", True),  # q0->q1->q2->q1->q2
                ("0", False),  # q0->q1
                ("1", False),  # q0->q0
                ("00", False),  # q0->q1->q1
            ]

            for input_str, expected in test_cases:
                with self.subTest(input_str=input_str):
                    is_accepted, _ = dfa.validate_string(input_str)
                    self.assertEqual(is_accepted, expected)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def test_dfa_single_state(self):
        """Тест ДКА с одним состоянием"""
        # ДКА, который всегда находится в q0 и допускает только пустую строку
        csv_content = """,a,b,Final
q0,q0,q0,1"""

        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        temp_file.write(csv_content)
        temp_file.close()

        try:
            dfa = DFA(temp_file.name)

            # Тестируем
            test_cases = [
                ("", True),  # Пустая строка
                ("a", True),  # Любой символ
                ("b", True),  # Любой символ
                ("abab", True),  # Любая цепочка
            ]

            for input_str, expected in test_cases:
                with self.subTest(input_str=input_str):
                    is_accepted, _ = dfa.validate_string(input_str)
                    self.assertEqual(is_accepted, expected)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def test_dfa_no_final_states(self):
        """Тест ДКА без конечных состояний"""
        # ДКА без конечных состояний (никогда ничего не допускает)
        csv_content = """,a,b,Final
q0,q1,q0,0
q1,q0,q1,0"""

        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
        temp_file.write(csv_content)
        temp_file.close()

        try:
            dfa = DFA(temp_file.name)

            # Тестируем
            test_cases = [
                ("", False),  # Пустая строка
                ("a", False),  # Любой символ
                ("b", False),  # Любой символ
                ("abab", False),  # Любая цепочка
            ]

            for input_str, expected in test_cases:
                with self.subTest(input_str=input_str):
                    is_accepted, _ = dfa.validate_string(input_str)
                    self.assertEqual(is_accepted, expected)
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)


def run_comprehensive_test():
    """Запуск комплексного тестирования"""
    print("\n" + "=" * 80)
    print("КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ДКА")
    print("=" * 80)

    # Создаем тестовый файл
    csv_content = """,a,b,Final
q0,q1,q0,0
q1,q1,q2,0
q2,q1,q0,1"""

    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
    temp_file.write(csv_content)
    temp_file.close()

    try:
        dfa = DFA(temp_file.name)

        # Генерируем тестовые строки
        test_strings = []
        expected_results = []

        # Допускающие цепочки (должны заканчиваться в q2)
        accepting_strings = [
            "ab",  # q0->q1->q2
            "abab",  # q0->q1->q2->q1->q2
            "ababab",  # q0->q1->q2->q1->q2->q1->q2
            "abababab",  # и т.д.
        ]

        for s in accepting_strings:
            test_strings.append(s)
            expected_results.append(True)

        # Отвергающие цепочки
        rejecting_strings = [
            "",  # пустая строка
            "a",  # q0->q1
            "b",  # q0->q0
            "aa",  # q0->q1->q1
            "bb",  # q0->q0->q0
            "aba",  # q0->q1->q2->q1
            "bab",  # q0->q0->q1->q2
            "ba",  # q0->q0->q1
            "abb",  # q0->q1->q2->q0
        ]

        for s in rejecting_strings:
            test_strings.append(s)
            expected_results.append(False)

        # Длинные цепочки для производительности
        for i in range(5, 10):
            s = "ab" * i
            test_strings.append(s)
            expected_results.append(True if i % 2 == 1 else False)  # "ab"*нечетное - допускается

        # Выполняем тесты
        passed = 0
        failed = 0

        print(f"\nВсего тестов: {len(test_strings)}")
        print("-" * 80)

        for i, (test_str, expected) in enumerate(zip(test_strings, expected_results), 1):
            is_accepted, state_sequence = dfa.validate_string(test_str)

            if is_accepted == expected:
                status = "✓"
                passed += 1
            else:
                status = "✗"
                failed += 1

            result_str = "допускается" if is_accepted else "не допускается"
            expected_str = "должна допускаться" if expected else "не должна допускаться"

            print(
                f"{status} Тест {i:3d}: '{test_str}' (len={len(test_str):2d}) -> {result_str:15s} [ожидалось: {expected_str}]")

            if is_accepted != expected:
                print(f"    Состояния: {' → '.join(state_sequence)}")

        print("-" * 80)
        print(f"ИТОГО: {passed} пройдено, {failed} не пройдено")
        print(f"Успешность: {passed / len(test_strings) * 100:.1f}%")

        if failed == 0:
            print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print(f"\n❌ НЕ ПРОЙДЕНО ТЕСТОВ: {failed}")

    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


if __name__ == '__main__':
    # Запуск комплексного тестирования
    run_comprehensive_test()

    # Запуск unit-тестов
    print("\n" + "=" * 80)
    print("ЗАПУСК UNIT-ТЕСТОВ")
    print("=" * 80)

    # Создаем тестовый набор
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDFA)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCustomDFA))

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Выводим итоги
    print("\n" + "=" * 80)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 80)
    print(f"Всего тестов: {result.testsRun}")
    print(f"Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Неудач: {len(result.failures)}")
    print(f"Ошибок: {len(result.errors)}")

    if result.failures:
        print("\nНЕУДАЧНЫЕ ТЕСТЫ:")
        for test, traceback in result.failures:
            print(f"\n{test}:")
            print(traceback)

    if result.errors:
        print("\nОШИБКИ:")
        for test, traceback in result.errors:
            print(f"\n{test}:")
            print(traceback)