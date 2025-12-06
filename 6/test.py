import unittest
import tempfile
import os
from pda import PushdownAutomaton, load_pda_from_config


class TestPushdownAutomaton(unittest.TestCase):

    def setUp(self):
        """Настройка перед каждым тестом"""
        self.pda = PushdownAutomaton()

    def create_temp_csv(self, content: str) -> str:
        """Создание временного CSV файла"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            return f.name

    def create_temp_config(self, content: str) -> str:
        """Создание временного конфигурационного файла"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            return f.name

    def tearDown(self):
        """Очистка после каждого теста"""
        pass

    def test_load_valid_csv(self):
        """Тест загрузки корректного CSV файла"""
        csv_content = """current_state,input_symbol,stack_top,new_state,stack_push
q0,a,Z,q0,AZ
q0,a,A,q0,AA
q0,b,A,q1,ε
q1,b,A,q1,ε
q1,ε,Z,q2,Z"""

        csv_file = self.create_temp_csv(csv_content)

        try:
            self.pda.load_from_csv(csv_file)

            # Проверка состояний
            self.assertEqual(self.pda.states, {'q0', 'q1', 'q2'})

            # Проверка входного алфавита
            self.assertEqual(self.pda.input_alphabet, {'a', 'b'})

            # Проверка стекового алфавита
            self.assertEqual(self.pda.stack_alphabet, {'Z', 'A'})

            # Проверка количества переходов
            total_transitions = sum(len(v) for v in self.pda.transitions.values())
            self.assertEqual(total_transitions, 5)

        finally:
            os.unlink(csv_file)

    def test_a_power_n_b_power_n_language(self):
        """Тест автомата для языка {a^n b^n | n >= 0}"""
        csv_content = """current_state,input_symbol,stack_top,new_state,stack_push
q0,a,Z,q0,AZ
q0,a,A,q0,AA
q0,b,A,q1,ε
q1,b,A,q1,ε
q1,ε,Z,q2,Z"""

        csv_file = self.create_temp_csv(csv_content)

        try:
            self.pda.load_from_csv(csv_file)
            self.pda.set_start_configuration('q0', 'Z')
            self.pda.set_accepting_states(['q2'])
            self.pda.set_acceptance_mode(by_final_state=True, by_empty_stack=False)

            # Проверка корректности конфигурации
            errors = self.pda.validate_configuration()
            self.assertEqual(len(errors), 0)

            # Тестовые цепочки
            test_cases = [
                ("", True),  # ε (n=0)
                ("ab", True),  # n=1
                ("aabb", True),  # n=2
                ("aaabbb", True),  # n=3
                ("a", False),  # неполная цепочка
                ("abb", False),  # несоответствие количества
                ("aab", False),  # неполная цепочка
                ("ba", False),  # неверный порядок
                ("abc", False),  # посторонний символ
            ]

            for chain, expected in test_cases:
                accept, _ = self.pda.simulate(chain)
                self.assertEqual(accept, expected,
                                 f"Цепочка '{chain}': ожидалось {expected}, получено {accept}")

        finally:
            os.unlink(csv_file)

    def test_palindrome_language(self):
        """Тест автомата для языка палиндромов над {a,b}"""
        csv_content = """current_state,input_symbol,stack_top,new_state,stack_push
q0,a,Z,q0,AZ
q0,b,Z,q0,BZ
q0,a,A,q0,AA
q0,b,A,q0,BA
q0,a,B,q0,AB
q0,b,B,q0,BB
q0,ε,A,q1,A
q0,ε,B,q1,B
q0,ε,Z,q1,Z
q1,a,A,q1,ε
q1,b,B,q1,ε
q1,ε,Z,q2,ε"""

        csv_file = self.create_temp_csv(csv_content)

        try:
            self.pda.load_from_csv(csv_file)
            self.pda.set_start_configuration('q0', 'Z')
            self.pda.set_accepting_states(['q2'])
            self.pda.set_acceptance_mode(by_final_state=True, by_empty_stack=True)

            errors = self.pda.validate_configuration()
            self.assertEqual(len(errors), 0)

            # Тестовые цепочки-палиндромы
            test_cases = [
                ("", True),  # ε
                ("a", True),  # один символ
                ("b", True),
                ("aa", True),
                ("bb", True),
                ("aba", True),
                ("bab", True),
                ("abba", True),
                ("baab", True),
                ("ab", False),  # не палиндром
                ("aab", False),
                ("ababa", True),  # палиндром нечетной длины
                ("abc", False),  # посторонний символ
            ]

            for chain, expected in test_cases:
                accept, _ = self.pda.simulate(chain, max_steps=5000)
                self.assertEqual(accept, expected,
                                 f"Палиндром '{chain}': ожидалось {expected}, получено {accept}")

        finally:
            os.unlink(csv_file)

    def test_accept_by_empty_stack(self):
        """Тест допуска по пустому стеку"""
        csv_content = """current_state,input_symbol,stack_top,new_state,stack_push
q0,a,Z,q0,AZ
q0,a,A,q0,AA
q0,b,A,q1,ε
q1,b,A,q1,ε
q1,ε,Z,q1,ε"""

        csv_file = self.create_temp_csv(csv_content)

        try:
            self.pda.load_from_csv(csv_file)
            self.pda.set_start_configuration('q0', 'Z')
            self.pda.set_accepting_states([])  # Нет допускающих состояний
            self.pda.set_acceptance_mode(by_final_state=False, by_empty_stack=True)

            errors = self.pda.validate_configuration()
            self.assertEqual(len(errors), 0)

            test_cases = [
                ("ab", True),
                ("aabb", True),
                ("aaabbb", True),
                ("a", False),
                ("abb", False),
            ]

            for chain, expected in test_cases:
                accept, _ = self.pda.simulate(chain)
                self.assertEqual(accept, expected)

        finally:
            os.unlink(csv_file)

    def test_epsilon_transitions(self):
        """Тест эпсилон-переходов"""
        csv_content = """current_state,input_symbol,stack_top,new_state,stack_push
q0,ε,Z,q0,A
q0,ε,A,q0,AA
q0,a,A,q1,ε
q1,a,A,q1,ε
q1,ε,Z,q2,Z"""

        csv_file = self.create_temp_csv(csv_content)

        try:
            self.pda.load_from_csv(csv_file)
            self.pda.set_start_configuration('q0', 'Z')
            self.pda.set_accepting_states(['q2'])
            self.pda.set_acceptance_mode(by_final_state=True, by_empty_stack=False)

            # Автомат допускает цепочки вида a^n, где n >= 0
            test_cases = [
                ("", True),  # ε
                ("a", True),  # a
                ("aa", True),  # aa
                ("aaa", True),  # aaa
                ("b", False),  # посторонний символ
            ]

            for chain, expected in test_cases:
                accept, _ = self.pda.simulate(chain)
                self.assertEqual(accept, expected)

        finally:
            os.unlink(csv_file)

    def test_multiple_transitions(self):
        """Тест недетерминированного автомата с несколькими переходами"""
        csv_content = """current_state,input_symbol,stack_top,new_state,stack_push
q0,a,Z,q0,AZ
q0,a,Z,q0,BZ
q0,b,A,q1,ε
q0,b,B,q1,ε
q1,ε,Z,q2,Z"""

        csv_file = self.create_temp_csv(csv_content)

        try:
            self.pda.load_from_csv(csv_file)
            self.pda.set_start_configuration('q0', 'Z')
            self.pda.set_accepting_states(['q2'])
            self.pda.set_acceptance_mode(by_final_state=True, by_empty_stack=False)

            # Автомат допускает цепочки вида ab
            test_cases = [
                ("ab", True),
                ("aab", False),
                ("abb", False),
            ]

            for chain, expected in test_cases:
                accept, _ = self.pda.simulate(chain)
                self.assertEqual(accept, expected)

        finally:
            os.unlink(csv_file)

    def test_validation_errors(self):
        """Тест проверки ошибок конфигурации"""
        csv_content = """current_state,input_symbol,stack_top,new_state,stack_push
q0,a,Z,q0,AZ"""

        csv_file = self.create_temp_csv(csv_content)

        try:
            self.pda.load_from_csv(csv_file)

            # Не задано начальное состояние и символ стека
            errors = self.pda.validate_configuration()
            self.assertIn("Не задано начальное состояние", errors)
            self.assertIn("Не задан начальный символ стека", errors)

            # Задаем несуществующее состояние
            self.pda.set_start_configuration('q99', 'Z')
            errors = self.pda.validate_configuration()
            self.assertIn("не найден в множестве состояний", errors[0])

            # Режим допуска по конечному состоянию, но нет допускающих состояний
            self.pda.set_start_configuration('q0', 'Z')
            self.pda.set_accepting_states([])
            self.pda.set_acceptance_mode(by_final_state=True, by_empty_stack=False)
            errors = self.pda.validate_configuration()
            self.assertIn("нет допускающих состояний", errors[0])

        finally:
            os.unlink(csv_file)

    def test_load_from_config(self):
        """Тест загрузки из конфигурационного файла"""
        csv_content = """current_state,input_symbol,stack_top,new_state,stack_push
q0,a,Z,q0,AZ
q0,a,A,q0,AA
q0,b,A,q1,ε
q1,b,A,q1,ε
q1,ε,Z,q2,Z"""

        config_content = """csv_file={csv_file}
start_state=q0
start_stack_symbol=Z
accepting_states=q2
acceptance_mode=final_state"""

        # Создаем временные файлы
        csv_file = self.create_temp_csv(csv_content)
        config_content = config_content.format(csv_file=csv_file)
        config_file = self.create_temp_config(config_content)

        try:
            pda = load_pda_from_config(config_file)

            # Проверка загруженной конфигурации
            self.assertEqual(pda.start_state, 'q0')
            self.assertEqual(pda.start_stack_symbol, 'Z')
            self.assertEqual(pda.accepting_states, {'q2'})
            self.assertTrue(pda.accept_by_final_state)
            self.assertFalse(pda.accept_by_empty_stack)

            # Проверка работы автомата
            accept, _ = pda.simulate("aabb")
            self.assertTrue(accept)

            accept, _ = pda.simulate("aabbb")
            self.assertFalse(accept)

        finally:
            os.unlink(csv_file)
            os.unlink(config_file)

    def test_max_steps_limit(self):
        """Тест ограничения максимального количества шагов"""
        # Создаем автомат, который может зациклиться
        csv_content = """current_state,input_symbol,stack_top,new_state,stack_push
q0,ε,Z,q0,AZ
q0,ε,A,q0,AA"""

        csv_file = self.create_temp_csv(csv_content)

        try:
            self.pda.load_from_csv(csv_file)
            self.pda.set_start_configuration('q0', 'Z')
            self.pda.set_accepting_states(['q0'])
            self.pda.set_acceptance_mode(by_final_state=True, by_empty_stack=False)

            # Этот автомат будет бесконечно добавлять символы в стек
            accept, history = self.pda.simulate("", max_steps=10)

            # Должен остановиться по достижению max_steps
            self.assertFalse(accept)
            self.assertIn("Превышено максимальное количество шагов", history[0])

        finally:
            os.unlink(csv_file)


class TestPDAPerformance(unittest.TestCase):
    """Тесты производительности"""

    def test_large_input(self):
        """Тест с большой входной цепочкой"""
        csv_content = """current_state,input_symbol,stack_top,new_state,stack_push
q0,a,Z,q0,AZ
q0,a,A,q0,AA
q0,b,A,q1,ε
q1,b,A,q1,ε
q1,ε,Z,q2,Z"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            csv_file = f.name

        try:
            pda = PushdownAutomaton()
            pda.load_from_csv(csv_file)
            pda.set_start_configuration('q0', 'Z')
            pda.set_accepting_states(['q2'])
            pda.set_acceptance_mode(by_final_state=True, by_empty_stack=False)

            # Большая корректная цепочка (n=100)
            chain = 'a' * 100 + 'b' * 100

            import time
            start_time = time.time()
            accept, _ = pda.simulate(chain, max_steps=100000)
            end_time = time.time()

            # Проверяем, что цепочка допускается
            self.assertTrue(accept)

            # Проверяем, что обработка заняла разумное время (менее 5 секунд)
            self.assertLess(end_time - start_time, 5.0)
            print(f"\nБольшая цепочка обработана за {end_time - start_time:.2f} секунд")

        finally:
            os.unlink(csv_file)


def run_all_tests():
    """Запуск всех тестов"""
    # Создаем test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Добавляем тесты
    suite.addTests(loader.loadTestsFromTestCase(TestPushdownAutomaton))
    suite.addTests(loader.loadTestsFromTestCase(TestPDAPerformance))

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    print("ЗАПУСК ТЕСТОВ МАГАЗИННОГО АВТОМАТА")
    print("=" * 60)

    # Запуск тестов
    success = run_all_tests()

    if success:
        print("\n✅ Все тесты пройдены успешно!")
    else:
        print("\n❌ Некоторые тесты не пройдены.")