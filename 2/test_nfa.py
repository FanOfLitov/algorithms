import unittest
import tempfile
import os
from main import NFA, read_nfa_from_csv


class TestNFA(unittest.TestCase):
    def setUp(self):
        """Создание тестового НКА"""
        self.states = {'q0', 'q1', 'q2', 'q3'}
        self.alphabet = {'a', 'b', 'ε'}

        transitions = {
            'q0': {'a': {'q1'}, 'b': {'q2'}, 'ε': set()},
            'q1': {'a': set(), 'b': {'q3'}, 'ε': set()},
            'q2': {'a': {'q3'}, 'b': set(), 'ε': set()},
            'q3': {'a': {'q3'}, 'b': {'q3'}, 'ε': set()}
        }

        self.start_state = 'q0'
        self.accept_states = {'q3'}
        self.nfa = NFA(self.states, self.alphabet, transitions,
                       self.start_state, self.accept_states)

    def test_epsilon_closure(self):
        """Тест ε-замыкания"""
        # Без эпсилон-переходов
        self.assertEqual(self.nfa.epsilon_closure({'q0'}), {'q0'})
        self.assertEqual(self.nfa.epsilon_closure({'q1', 'q2'}), {'q1', 'q2'})

        # Создадим НКА с эпсилон-переходами
        transitions_with_eps = {
            'q0': {'a': {'q1'}, 'ε': {'q1'}},
            'q1': {'b': {'q2'}, 'ε': {'q3'}},
            'q2': {'ε': set()},
            'q3': {'ε': {'q2'}}
        }
        nfa_eps = NFA({'q0', 'q1', 'q2', 'q3'}, {'a', 'b', 'ε'},
                      transitions_with_eps, 'q0', {'q2'})

        self.assertEqual(nfa_eps.epsilon_closure({'q0'}), {'q0', 'q1', 'q3', 'q2'})
        self.assertEqual(nfa_eps.epsilon_closure({'q1'}), {'q1', 'q3', 'q2'})

    def test_process_input_accept(self):
        """Тест принятия цепочек"""
        # Цепочка "ab" - q0->q1 по a, q1->q3 по b
        self.assertTrue(self.nfa.process_input("ab"))

        # Цепочка "ba" - q0->q2 по b, q2->q3 по a
        self.assertTrue(self.nfa.process_input("ba"))

        # Цепочка "abaab" - проверяем сложную цепочку
        # q0->q1 (a), q1->q3 (b), q3->q3 (a), q3->q3 (a), q3->q3 (b)
        self.assertTrue(self.nfa.process_input("abaab"))

    def test_process_input_reject(self):
        """Тест отклонения цепочек"""
        # Пустая цепочка
        self.assertFalse(self.nfa.process_input(""))

        # Цепочка "a" - q0->q1 по a, но q1 не допускающее
        self.assertFalse(self.nfa.process_input("a"))

        # Цепочка "b" - q0->q2 по b, но q2 не допускающее
        self.assertFalse(self.nfa.process_input("b"))

        # Цепочка "aaa" - q0->q1 по a, дальше нет переходов по a из q1
        self.assertFalse(self.nfa.process_input("aaa"))

        # Цепочка "bb" - q0->q2 по b, дальше нет переходов по b из q2
        self.assertFalse(self.nfa.process_input("bb"))

        # Неверный символ
        with self.assertRaises(ValueError):
            self.nfa.process_input("acb")

    def test_nfa_with_epsilon_transitions(self):
        """Тест НКА с эпсилон-переходами"""
        states = {'q0', 'q1', 'q2', 'q3'}
        alphabet = {'a', 'b', 'ε'}

        transitions = {
            'q0': {'a': {'q0'}, 'ε': {'q1'}},
            'q1': {'b': {'q1'}, 'ε': {'q2'}},
            'q2': {'a': {'q2'}, 'b': {'q3'}, 'ε': set()},
            'q3': {'a': {'q3'}, 'b': {'q3'}, 'ε': set()}
        }

        nfa_eps = NFA(states, alphabet, transitions, 'q0', {'q3'})

        # Эпсилон-замыкание q0
        self.assertEqual(nfa_eps.epsilon_closure({'q0'}), {'q0', 'q1', 'q2'})

        # Проверка цепочек
        self.assertTrue(nfa_eps.process_input("ab"))  # ab: q0->q1->q2->q3
        self.assertTrue(nfa_eps.process_input("b"))  # b: q0->q1->q2->q3 по ε, затем b
        self.assertFalse(nfa_eps.process_input("a"))  # a: q0 остается в q0, не достигает q3

    def test_csv_reading(self):
        """Тест чтения НКА из CSV-файла"""
        # Создаем временный CSV файл с правильной кодировкой
        csv_content = """,a,b,ε
q0,q1,q2,,
q1,,q3,
q2,q3,,,
q3,q3,q3,*"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            nfa = read_nfa_from_csv(temp_file)

            # Проверка структуры НКА
            self.assertEqual(nfa.states, {'q0', 'q1', 'q2', 'q3'})
            self.assertEqual(set(nfa.alphabet), {'a', 'b', 'ε'})
            self.assertEqual(nfa.start_state, 'q0')
            self.assertEqual(nfa.accept_states, {'q3'})

            # Проверка переходов
            self.assertEqual(nfa.transitions['q0']['a'], {'q1'})
            self.assertEqual(nfa.transitions['q0']['b'], {'q2'})
            self.assertEqual(nfa.transitions['q1']['b'], {'q3'})
            self.assertEqual(nfa.transitions['q2']['a'], {'q3'})
            self.assertEqual(nfa.transitions['q3']['a'], {'q3'})
            self.assertEqual(nfa.transitions['q3']['b'], {'q3'})

            # Проверка обработки цепочек
            self.assertTrue(nfa.process_input("ab"))
            self.assertTrue(nfa.process_input("ba"))
            self.assertFalse(nfa.process_input("a"))
            self.assertFalse(nfa.process_input("aaa"))

        finally:
            os.unlink(temp_file)

    def test_empty_transitions(self):
        """Тест пустых переходов"""
        states = {'q0', 'q1'}
        alphabet = {'a', 'b', 'ε'}

        transitions = {
            'q0': {'a': {'q1'}, 'b': set(), 'ε': set()},
            'q1': {'a': set(), 'b': set(), 'ε': set()}
        }

        nfa = NFA(states, alphabet, transitions, 'q0', {'q1'})

        # Цепочка "a" принимается
        self.assertTrue(nfa.process_input("a"))

        # Цепочка "b" отклоняется (нет перехода)
        self.assertFalse(nfa.process_input("b"))

        # Цепочка "aa" отклоняется (после первого символа в q1, нет перехода по a)
        self.assertFalse(nfa.process_input("aa"))

    def test_multiple_transitions(self):
        """Тест множественных переходов"""
        states = {'q0', 'q1', 'q2'}
        alphabet = {'a', 'b', 'ε'}

        transitions = {
            'q0': {'a': {'q1', 'q2'}, 'b': set(), 'ε': set()},
            'q1': {'a': {'q1'}, 'b': {'q2'}, 'ε': set()},
            'q2': {'a': set(), 'b': {'q2'}, 'ε': set()}
        }

        nfa = NFA(states, alphabet, transitions, 'q0', {'q2'})

        # Цепочка "a" - может перейти в q1 или q2, если в q2 - принимается
        # Нужно проверить оба пути
        self.assertTrue(nfa.process_input("a"))

        # Цепочка "ab" - q0->q1 по a, q1->q2 по b
        self.assertTrue(nfa.process_input("ab"))

        # Цепочка "abb" - q0->q1 по a, q1->q2 по b, q2->q2 по b
        self.assertTrue(nfa.process_input("abb"))


if __name__ == '__main__':
    unittest.main(verbosity=2)