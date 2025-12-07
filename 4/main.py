import re
import csv
import os
import random
from collections import defaultdict, deque
from typing import Set, Dict, List, Optional, Tuple, Any


class State:
    """Класс для представления состояния автомата"""
    counter = 0

    def __init__(self, is_final: bool = False):
        self.id = State.counter
        State.counter += 1
        self.transitions = defaultdict(set)  # символ -> множество состояний
        self.epsilon_transitions = set()  # ε-переходы
        self.is_final = is_final

    def add_transition(self, symbol: str, state):
        """Добавить переход по символу"""
        self.transitions[symbol].add(state)

    def add_epsilon(self, state):
        """Добавить ε-переход"""
        self.epsilon_transitions.add(state)

    def __repr__(self):
        return f"State({self.id}, final={self.is_final})"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, State) and self.id == other.id


class NFA:
    """Класс для представления недетерминированного конечного автомата"""

    def __init__(self, start: State = None, end: State = None):
        self.start = start
        self.end = end

    def epsilon_closure(self, states: Set[State]) -> Set[State]:
        """Вычисление ε-замыкания множества состояний"""
        closure = set(states)
        stack = list(states)

        while stack:
            state = stack.pop()
            for next_state in state.epsilon_transitions:
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)

        return closure

    def process_input(self, input_string: str) -> bool:
        """Обработка входной строки НКА"""
        current_states = self.epsilon_closure({self.start})

        for symbol in input_string:
            next_states = set()
            for state in current_states:
                if symbol in state.transitions:
                    next_states.update(state.transitions[symbol])

            if not next_states:
                return False

            current_states = self.epsilon_closure(next_states)

        return any(state.is_final for state in current_states)


class DFA:
    """Класс для представления детерминированного конечного автомата"""

    def __init__(self, states: Set[int], alphabet: Set[str],
                 transitions: Dict[int, Dict[str, int]],
                 start_state: int, accept_states: Set[int]):
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start_state = start_state
        self.accept_states = accept_states

    def process_input(self, input_string: str) -> bool:
        """Обработка входной строки ДКА"""
        current_state = self.start_state

        for symbol in input_string:
            if symbol not in self.alphabet:
                raise ValueError(f"Символ '{symbol}' не найден в алфавите")

            if current_state in self.transitions and symbol in self.transitions[current_state]:
                current_state = self.transitions[current_state][symbol]
            else:
                # Если нет перехода по символу, строка не принимается
                return False

        return current_state in self.accept_states

    def process_input_with_trace(self, input_string: str) -> Tuple[bool, List[int]]:
        """Обработка входной строки ДКА с возвратом пути"""
        path = []
        current_state = self.start_state
        path.append(current_state)

        for symbol in input_string:
            if symbol not in self.alphabet:
                raise ValueError(f"Символ '{symbol}' не найден в алфавите")

            if current_state in self.transitions and symbol in self.transitions[current_state]:
                current_state = self.transitions[current_state][symbol]
                path.append(current_state)
            else:
                return False, path

        return current_state in self.accept_states, path


class RegexInterpreter:
    """Интерпретатор регулярных выражений"""

    def __init__(self):
        self.operators = {'|', '*', '(', ')', '.', '+'}
        self.precedence = {'|': 1, '.': 2, '*': 3, '+': 3}

    def add_concat_operator(self, regex: str) -> str:
        """Добавление оператора конкатенации (.) в явном виде"""
        if not regex:
            return regex

        result = []
        for i, char in enumerate(regex):
            result.append(char)

            if i + 1 < len(regex):
                next_char = regex[i + 1]

                # Вставляем . между:
                # 1) символом и символом
                # 2) символом и (
                # 3) ) и символом
                # 4) ) и (
                # 5) * и символом
                # 6) * и (
                # 7) + и символом
                # 8) + и (
                current_is_operand = char not in self.operators or char in {'*', '+', ')'}
                next_is_operand = next_char not in self.operators or next_char == '('

                if current_is_operand and next_is_operand:
                    result.append('.')

        return ''.join(result)

    def to_postfix(self, regex: str) -> str:
        """Преобразование регулярного выражения в обратную польскую запись"""
        if not regex:
            return ''

        # Добавляем оператор конкатенации
        regex = self.add_concat_operator(regex)

        output = []
        stack = []

        i = 0
        while i < len(regex):
            char = regex[i]

            if char == '\\':  # Обработка экранирования
                if i + 1 < len(regex):
                    output.append(regex[i:i + 2])
                    i += 2
                continue

            if char not in self.operators:
                output.append(char)
            elif char == '(':
                stack.append(char)
            elif char == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if stack and stack[-1] == '(':
                    stack.pop()  # Удаляем '('
                else:
                    raise ValueError("Несогласованные скобки в регулярном выражении")
            else:
                while (stack and stack[-1] != '(' and
                       self.precedence.get(stack[-1], 0) >= self.precedence.get(char, 0)):
                    output.append(stack.pop())
                stack.append(char)

            i += 1

        # Обработка оставшихся операторов в стеке
        while stack:
            if stack[-1] == '(':
                raise ValueError("Несогласованные скобки в регулярном выражении")
            output.append(stack.pop())

        return ''.join(output)

    def build_nfa_from_postfix(self, postfix: str) -> NFA:
        """Построение НКА из обратной польской записи (алгоритм Томпсона)"""
        if not postfix:
            # Пустое выражение принимает только пустую строку
            start = State()
            end = State(is_final=True)
            start.add_epsilon(end)
            return NFA(start, end)

        stack = []

        for token in postfix:
            if len(token) == 2 and token[0] == '\\':  # Экранированный символ
                char = token[1]
                start = State()
                end = State(is_final=True)
                start.add_transition(char, end)
                stack.append(NFA(start, end))

            elif token not in self.operators:  # Обычный символ
                start = State()
                end = State(is_final=True)
                start.add_transition(token, end)
                stack.append(NFA(start, end))

            elif token == '|':  # Объединение
                if len(stack) < 2:
                    raise ValueError("Недостаточно операндов для оператора |")
                nfa2 = stack.pop()
                nfa1 = stack.pop()

                start = State()
                end = State(is_final=True)

                start.add_epsilon(nfa1.start)
                start.add_epsilon(nfa2.start)

                nfa1.end.is_final = False
                nfa2.end.is_final = False
                nfa1.end.add_epsilon(end)
                nfa2.end.add_epsilon(end)

                stack.append(NFA(start, end))

            elif token == '.':  # Конкатенация
                if len(stack) < 2:
                    raise ValueError("Недостаточно операндов для оператора .")
                nfa2 = stack.pop()
                nfa1 = stack.pop()

                nfa1.end.is_final = False
                nfa1.end.add_epsilon(nfa2.start)

                stack.append(NFA(nfa1.start, nfa2.end))

            elif token == '*':  # Звезда Клини
                if len(stack) < 1:
                    raise ValueError("Недостаточно операндов для оператора *")
                nfa = stack.pop()

                start = State()
                end = State(is_final=True)

                start.add_epsilon(nfa.start)
                start.add_epsilon(end)

                nfa.end.is_final = False
                nfa.end.add_epsilon(nfa.start)
                nfa.end.add_epsilon(end)

                stack.append(NFA(start, end))

            elif token == '+':  # Плюс (один или более)
                if len(stack) < 1:
                    raise ValueError("Недостаточно операндов для оператора +")
                nfa = stack.pop()

                start = State()
                end = State(is_final=True)

                start.add_epsilon(nfa.start)
                nfa.end.is_final = False
                nfa.end.add_epsilon(nfa.start)
                nfa.end.add_epsilon(end)

                stack.append(NFA(start, end))

        if len(stack) != 1:
            raise ValueError("Ошибка в построении НКА")

        return stack.pop()

    def nfa_to_dfa(self, nfa: NFA) -> DFA:
        """Преобразование НКА в ДКА (алгоритм подмножеств)"""
        # Шаг 1: Инициализация
        dfa_states = []
        dfa_transitions = {}
        state_map = {}  # Множество состояний НКА -> ID состояния ДКА

        start_set = frozenset(nfa.epsilon_closure({nfa.start}))
        queue = deque([start_set])
        state_map[start_set] = 0
        dfa_states.append(start_set)

        accept_states = set()

        # Шаг 2: Определение алфавита
        alphabet = set()
        for state_set in dfa_states:
            for state in state_set:
                for symbol in state.transitions:
                    if symbol:  # Игнорируем пустые символы
                        alphabet.add(symbol)

        # Если алфавит пустой, добавляем хотя бы один символ для корректной работы
        if not alphabet:
            alphabet.add('a')  # Заглушка

        # Шаг 3: Построение таблицы переходов ДКА
        while queue:
            current_set = queue.popleft()
            current_id = state_map[current_set]

            # Проверяем, является ли состояние допускающим
            if any(state.is_final for state in current_set):
                accept_states.add(current_id)

            # Обрабатываем переходы по каждому символу
            for symbol in alphabet:
                next_states = set()

                for state in current_set:
                    if symbol in state.transitions:
                        next_states.update(state.transitions[symbol])

                if next_states:
                    epsilon_closure = nfa.epsilon_closure(next_states)
                    next_set = frozenset(epsilon_closure)

                    if next_set not in state_map:
                        state_map[next_set] = len(dfa_states)
                        dfa_states.append(next_set)
                        queue.append(next_set)

                    if current_id not in dfa_transitions:
                        dfa_transitions[current_id] = {}
                    dfa_transitions[current_id][symbol] = state_map[next_set]
                else:
                    # Нет перехода по символу - можно добавить переход в ловушку,
                    # но для простоты оставляем без перехода
                    pass

        # Шаг 4: Создание объекта ДКА
        dfa = DFA(
            states=set(range(len(dfa_states))),
            alphabet=alphabet,
            transitions=dfa_transitions,
            start_state=0,
            accept_states=accept_states
        )

        return dfa

    def regex_to_dfa(self, regex: str) -> DFA:
        """Полный конвейер: регулярное выражение -> ДКА"""
        postfix = self.to_postfix(regex)
        nfa = self.build_nfa_from_postfix(postfix)
        return self.nfa_to_dfa(nfa)


class KMP:
    """Реализация алгоритма Кнута-Морриса-Пратта для поиска подстроки"""

    @staticmethod
    def build_lps(pattern: str) -> List[int]:
        """Построение таблицы длин префиксов-суффиксов (LPS)"""
        if not pattern:
            return []

        lps = [0] * len(pattern)
        length = 0  # Длина текущего префикса-суффикса
        i = 1

        while i < len(pattern):
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            else:
                if length != 0:
                    length = lps[length - 1]
                else:
                    lps[i] = 0
                    i += 1

        return lps

    @staticmethod
    def search(text: str, pattern: str) -> List[int]:
        """Поиск всех вхождений pattern в text"""
        if not pattern:
            return []

        lps = KMP.build_lps(pattern)
        result = []

        i = 0  # Индекс в text
        j = 0  # Индекс в pattern

        while i < len(text):
            if pattern[j] == text[i]:
                i += 1
                j += 1

            if j == len(pattern):
                result.append(i - j)
                j = lps[j - 1]
            elif i < len(text) and pattern[j] != text[i]:
                if j != 0:
                    j = lps[j - 1]
                else:
                    i += 1

        return result

    @staticmethod
    def search_with_dfa(text: str, pattern: str) -> List[int]:
        """Поиск с использованием ДКА, построенного из pattern"""
        # Создаем интерпретатор и строим ДКА для pattern
        interpreter = RegexInterpreter()

        # Экранируем специальные символы в pattern для использования как литерала
        escaped_pattern = ''.join(f'\\{c}' if c in interpreter.operators else c for c in pattern)
        dfa = interpreter.regex_to_dfa(escaped_pattern)

        result = []

        # Для каждой позиции в тексте проверяем, принимает ли ДКА суффикс
        for i in range(len(text)):
            current_state = dfa.start_state
            j = i

            while j < len(text):
                symbol = text[j]
                if symbol in dfa.alphabet and current_state in dfa.transitions:
                    if symbol in dfa.transitions[current_state]:
                        current_state = dfa.transitions[current_state][symbol]
                        if current_state in dfa.accept_states:
                            result.append(i)
                            break
                    else:
                        break
                else:
                    break
                j += 1

        return result


class RegexTester:
    """Класс для тестирования регулярных выражений"""

    @staticmethod
    def generate_test_string(length: int, alphabet: str = "abc") -> str:
        """Генерация тестовой строки заданной длины"""
        if length <= 0:
            return ""
        return ''.join(random.choice(alphabet) for _ in range(length))

    @staticmethod
    def test_regex(regex: str, test_string: str, use_dfa: bool = True) -> Tuple[bool, List[int]]:
        """Тестирование регулярного выражения на строке"""
        try:
            # Используем встроенный модуль re для сравнения
            python_matches = []
            try:
                for match in re.finditer(regex, test_string):
                    python_matches.append(match.start())
            except re.error:
                # Если регулярное выражение некорректно для Python re
                pass

            # Используем наш интерпретатор
            interpreter = RegexInterpreter()

            try:
                dfa = interpreter.regex_to_dfa(regex)
            except Exception as e:
                # Если не удалось построить ДКА, пробуем НКА
                postfix = interpreter.to_postfix(regex)
                nfa = interpreter.build_nfa_from_postfix(postfix)

                if use_dfa:
                    dfa = interpreter.nfa_to_dfa(nfa)
                else:
                    # Используем НКА
                    our_matches = []
                    for i in range(len(test_string)):
                        for j in range(i + 1, len(test_string) + 1):
                            if nfa.process_input(test_string[i:j]):
                                our_matches.append(i)
                                break
                    return False, our_matches

            # Используем ДКА для поиска всех вхождений
            our_matches = []
            for i in range(len(test_string)):
                for j in range(i + 1, len(test_string) + 1):
                    try:
                        if dfa.process_input(test_string[i:j]):
                            our_matches.append(i)
                            break
                    except:
                        break

            return python_matches == our_matches, our_matches

        except Exception as e:
            return False, []

    @staticmethod
    def compare_kmp_dfa(pattern: str, text: str) -> Tuple[List[int], List[int], bool]:
        """Сравнение результатов KMP и ДКА"""
        kmp_matches = KMP.search(text, pattern)

        interpreter = RegexInterpreter()
        # Экранируем специальные символы
        escaped_pattern = ''.join(f'\\{c}' if c in interpreter.operators else c for c in pattern)
        dfa = interpreter.regex_to_dfa(escaped_pattern)

        dfa_matches = []
        for i in range(len(text)):
            current_state = dfa.start_state
            j = i

            while j < len(text):
                symbol = text[j]
                if symbol in dfa.alphabet and current_state in dfa.transitions:
                    if symbol in dfa.transitions[current_state]:
                        current_state = dfa.transitions[current_state][symbol]
                        if current_state in dfa.accept_states:
                            dfa_matches.append(i)
                            break
                    else:
                        break
                else:
                    break
                j += 1

        return kmp_matches, dfa_matches, kmp_matches == dfa_matches


class CSVHandler:
    """Класс для работы с CSV файлами"""

    @staticmethod
    def read_test_cases(filepath: str) -> List[Dict[str, str]]:
        """Чтение тестовых случаев из CSV файла"""
        test_cases = []

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Файл {filepath} не найден")

        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    test_cases.append(dict(row))
        except Exception as e:
            raise ValueError(f"Ошибка чтения CSV файла: {e}")

        return test_cases

    @staticmethod
    def write_results(filepath: str, results: List[Dict[str, Any]]):
        """Запись результатов тестирования в CSV файл"""
        if not results:
            return

        fieldnames = results[0].keys()

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        except Exception as e:
            raise ValueError(f"Ошибка записи CSV файла: {e}")


class BatchTester:
    """Класс для пакетного тестирования"""

    def __init__(self):
        self.interpreter = RegexInterpreter()
        self.tester = RegexTester()

    def test_from_csv(self, csv_file: str, output_file: str = None) -> Dict[str, Any]:
        """Пакетное тестирование из CSV файла"""
        try:
            test_cases = CSVHandler.read_test_cases(csv_file)
        except Exception as e:
            return {"error": str(e), "total": 0, "passed": 0, "failed": 0}

        results = []
        passed = 0
        failed = 0

        print(f"\nЗагружено {len(test_cases)} тестовых случаев")
        print("-" * 60)

        for i, test_case in enumerate(test_cases, 1):
            regex = test_case.get('regex', '').strip()
            test_string = test_case.get('test_string', '').strip()
            expected = test_case.get('expected', '').strip().lower()

            if not regex:
                print(f"Тест {i}: Пропущен (отсутствует регулярное выражение)")
                continue

            try:
                # Преобразуем ожидаемое значение в булево
                expected_bool = expected in ('true', '1', 'yes', 'да', 't', 'y')

                # Строим ДКА
                dfa = self.interpreter.regex_to_dfa(regex)

                # Тестируем
                result = dfa.process_input(test_string)

                # Проверяем результат
                test_passed = (result == expected_bool)

                if test_passed:
                    status = "✓"
                    passed += 1
                else:
                    status = "✗"
                    failed += 1

                # Сохраняем результат
                result_data = {
                    'test_id': i,
                    'regex': regex,
                    'test_string': test_string,
                    'expected': expected,
                    'actual': str(result),
                    'status': 'PASS' if test_passed else 'FAIL'
                }
                results.append(result_data)

                print(f"Тест {i}: {status} {regex} на '{test_string}' -> ожидалось {expected_bool}, получено {result}")

            except Exception as e:
                failed += 1
                result_data = {
                    'test_id': i,
                    'regex': regex,
                    'test_string': test_string,
                    'expected': expected,
                    'actual': f"ERROR: {str(e)}",
                    'status': 'ERROR'
                }
                results.append(result_data)
                print(f"Тест {i}: ✗ Ошибка: {e}")

        # Записываем результаты, если указан выходной файл
        if output_file and results:
            try:
                CSVHandler.write_results(output_file, results)
                print(f"\nРезультаты сохранены в {output_file}")
            except Exception as e:
                print(f"\nОшибка сохранения результатов: {e}")

        return {
            "total": len(test_cases),
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / len(test_cases)) * 100 if test_cases else 0
        }


def display_dfa_info(dfa: DFA):
    """Отображение информации о ДКА в читаемом формате"""
    print(f"\nИнформация о ДКА:")
    print(f"  Количество состояний: {len(dfa.states)}")
    print(f"  Алфавит: {sorted(dfa.alphabet)}")
    print(f"  Начальное состояние: q{dfa.start_state}")
    print(f"  Допускающие состояния: {sorted(dfa.accept_states)}")

    if dfa.transitions:
        print(f"  Таблица переходов:")
        # Сортируем для красивого вывода
        for state in sorted(dfa.states):
            if state in dfa.transitions:
                trans_str = ', '.join([f"{sym}→q{target}" for sym, target in sorted(dfa.transitions[state].items())])
                if trans_str:
                    print(f"    q{state}: {trans_str}")


def display_nfa_info(nfa: NFA):
    """Отображение информации о НКА"""
    # Собираем все состояния
    all_states = set()
    stack = [nfa.start]

    while stack:
        state = stack.pop()
        if state not in all_states:
            all_states.add(state)
            # Добавляем все состояния из переходов
            for symbol, targets in state.transitions.items():
                for target in targets:
                    if target not in all_states:
                        stack.append(target)
            # Добавляем все состояния из ε-переходов
            for target in state.epsilon_transitions:
                if target not in all_states:
                    stack.append(target)

    print(f"\nИнформация о НКА:")
    print(f"  Количество состояний: {len(all_states)}")
    print(f"  Начальное состояние: q{nfa.start.id}")
    print(f"  Конечное состояние: q{nfa.end.id}")


def main():
    """Основная функция программы"""
    print("=" * 70)
    print("ИНТЕРПРЕТАТОР РЕГУЛЯРНЫХ ВЫРАЖЕНИЙ С ГЕНЕРАЦИЕЙ ДКА/НКА")
    print("=" * 70)

    interpreter = RegexInterpreter()
    tester = RegexTester()
    batch_tester = BatchTester()

    while True:
        print("\n" + "=" * 70)
        print("МЕНЮ:")
        print("1. Построить НКА/ДКА по регулярному выражению")
        print("2. Протестировать регулярное выражение на строке")
        print("3. Сравнить KMP и ДКА для поиска подстроки")
        print("4. Сгенерировать тестовую строку")
        print("5. Пакетное тестирование из CSV файла")
        print("6. Примеры регулярных выражений")
        print("7. Выход")

        choice = input("\nВыберите действие (1-7): ").strip()

        if choice == '1':
            print("\n" + "-" * 40)
            regex = input("Введите регулярное выражение: ").strip()

            if not regex:
                print("Ошибка: регулярное выражение не может быть пустым")
                continue

            try:
                # Шаг 1: Преобразование в обратную польскую запись
                print("\n1. Преобразование в обратную польскую запись...")
                postfix = interpreter.to_postfix(regex)
                print(f"   Обратная польская запись: {postfix}")

                # Шаг 2: Построение НКА
                print("\n2. Построение НКА (алгоритм Томпсона)...")
                nfa = interpreter.build_nfa_from_postfix(postfix)
                display_nfa_info(nfa)

                # Шаг 3: Преобразование в ДКА
                print("\n3. Преобразование НКА в ДКА (алгоритм подмножеств)...")
                dfa = interpreter.nfa_to_dfa(nfa)
                display_dfa_info(dfa)

                # Дополнительно: тестирование строки
                print("\n" + "-" * 40)
                test_input = input("Введите строку для тестирования (или Enter для пропуска): ").strip()
                if test_input:
                    try:
                        nfa_result = nfa.process_input(test_input)
                        dfa_result = dfa.process_input(test_input)
                        print(f"\nРезультаты тестирования строки '{test_input}':")
                        print(f"  НКА: {'ПРИНЯТА' if nfa_result else 'ОТВЕРГНУТА'}")
                        print(f"  ДКА: {'ПРИНЯТА' if dfa_result else 'ОТВЕРГНУТА'}")

                        if nfa_result != dfa_result:
                            print("  ⚠️ Внимание: результаты НКА и ДКА различаются!")
                    except ValueError as e:
                        print(f"Ошибка при тестировании: {e}")

            except Exception as e:
                print(f"\n❌ Ошибка: {e}")
                import traceback
                traceback.print_exc()

        elif choice == '2':
            print("\n" + "-" * 40)
            regex = input("Введите регулярное выражение: ").strip()

            if not regex:
                print("Ошибка: регулярное выражение не может быть пустым")
                continue

            test_string = input("Введите тестовую строку: ").strip()
            use_dfa = input("Использовать ДКА для тестирования? (y/n): ").strip().lower() == 'y'

            try:
                success, matches = tester.test_regex(regex, test_string, use_dfa)

                if success:
                    print(f"\n✅ Результаты совпадают с Python re")
                else:
                    print(f"\n❌ Результаты НЕ совпадают с Python re")

                print(f"Наш интерпретатор нашел {len(matches)} совпадений")
                if matches:
                    print(f"Позиции совпадений: {matches}")

            except Exception as e:
                print(f"\n❌ Ошибка: {e}")

        elif choice == '3':
            print("\n" + "-" * 40)
            pattern = input("Введите подстроку для поиска: ").strip()

            if not pattern:
                print("Ошибка: шаблон не может быть пустым")
                continue

            length = input("Длина тестовой строки (по умолчанию 50): ").strip()
            length = int(length) if length.isdigit() else 50

            # Генерация тестовой строки
            alphabet = input("Алфавит для генерации (по умолчанию abc): ").strip() or "abc"
            test_string = tester.generate_test_string(length, alphabet)

            print(f"\nСгенерированная строка ({length} символов):")
            if length > 100:
                print(f"  {test_string[:50]}...{test_string[-50:]}")
            else:
                print(f"  {test_string}")

            try:
                kmp_matches, dfa_matches, equal = tester.compare_kmp_dfa(pattern, test_string)

                print(f"\nРезультаты сравнения:")
                print(f"  Алгоритм KMP:    {len(kmp_matches)} совпадений")
                print(f"  ДКА-поиск:       {len(dfa_matches)} совпадений")

                if equal:
                    print(f"  ✅ Результаты идентичны")
                    if kmp_matches:
                        print(f"  Позиции: {kmp_matches[:10]}{'...' if len(kmp_matches) > 10 else ''}")
                else:
                    print(f"  ❌ Результаты различаются")

                    # Показываем различия
                    only_kmp = set(kmp_matches) - set(dfa_matches)
                    only_dfa = set(dfa_matches) - set(kmp_matches)

                    if only_kmp:
                        print(f"  Только KMP нашел: {sorted(only_kmp)[:5]}{'...' if len(only_kmp) > 5 else ''}")
                    if only_dfa:
                        print(f"  Только ДКА нашел: {sorted(only_dfa)[:5]}{'...' if len(only_dfa) > 5 else ''}")

            except Exception as e:
                print(f"\n❌ Ошибка: {e}")

        elif choice == '4':
            print("\n" + "-" * 40)
            length = input("Длина строки: ").strip()

            if not length.isdigit():
                print("Ошибка: длина должна быть числом")
                continue

            length = int(length)
            if length <= 0:
                print("Ошибка: длина должна быть положительным числом")
                continue

            alphabet = input("Алфавит (по умолчанию abc): ").strip() or "abc"

            test_string = tester.generate_test_string(length, alphabet)

            print(f"\n✅ Сгенерированная строка:")
            print(f"Длина: {len(test_string)} символов")
            print(f"Алфавит: {set(alphabet)}")
            print(f"\n{test_string}")

            # Сохранить в файл?
            save = input("\nСохранить в файл? (y/n): ").strip().lower()
            if save == 'y':
                filename = input("Имя файла (по умолчанию test_string.txt): ").strip() or "test_string.txt"
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(test_string)
                    print(f"✅ Строка сохранена в {filename}")
                except Exception as e:
                    print(f"❌ Ошибка сохранения: {e}")

        elif choice == '5':
            print("\n" + "-" * 40)
            csv_file = input("Введите путь к CSV файлу с тестами: ").strip()

            if not os.path.exists(csv_file):
                print(f"❌ Файл {csv_file} не найден")
                continue

            output_file = input("Введите путь для сохранения результатов (или Enter для пропуска): ").strip()

            print("\nЗапуск пакетного тестирования...")
            results = batch_tester.test_from_csv(csv_file, output_file if output_file else None)

            if "error" in results:
                print(f"❌ Ошибка: {results['error']}")
            else:
                print("\n" + "=" * 60)
                print("ИТОГИ ПАКЕТНОГО ТЕСТИРОВАНИЯ:")
                print(f"  Всего тестов: {results['total']}")
                print(f"  Пройдено: {results['passed']}")
                print(f"  Не пройдено: {results['failed']}")
                print(f"  Успешность: {results['success_rate']:.1f}%")

                if results['success_rate'] == 100:
                    print("  🎉 Отличный результат!")
                elif results['success_rate'] >= 80:
                    print("  👍 Хороший результат!")
                elif results['success_rate'] >= 60:
                    print("  ⚠️  Есть над чем поработать")
                else:
                    print("  ❌ Требуется серьезная доработка")

        elif choice == '6':
            print("\n" + "=" * 60)
            print("ПРИМЕРЫ РЕГУЛЯРНЫХ ВЫРАЖЕНИЙ:")
            print("=" * 60)

            examples = [
                ("a", "Буква 'a'"),
                ("ab", "Конкатенация 'ab'"),
                ("a|b", "Объединение: 'a' или 'b'"),
                ("a*", "Звезда Клини: 0 или более 'a'"),
                ("a+", "Плюс: 1 или более 'a'"),
                ("(a|b)*", "Любая комбинация из 'a' и 'b'"),
                ("a(b|c)d", "'a', затем 'b' или 'c', затем 'd'"),
                ("(ab)+", "Один или более раз 'ab'"),
                ("a*b*", "Ноль или более 'a', затем ноль или более 'b'"),
                ("(a|ε)b", "'a' или пусто, затем 'b'"),
            ]

            for i, (regex, desc) in enumerate(examples, 1):
                print(f"{i:2}. {regex:15} - {desc}")

            print("\nПример CSV файла для тестирования:")
            print("""
regex,test_string,expected
a,a,True
a,b,False
ab,ab,True
ab,abc,False
a|b,a,True
a|b,b,True
a|b,c,False
a*,aaa,True
a*,b,False
(a|b)*,abba,True
            """)

        elif choice == '7':
            print("\n" + "=" * 60)
            print("Спасибо за использование программы!")
            print("=" * 60)
            break

        else:
            print("\n❌ Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрограмма завершена пользователем.")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()