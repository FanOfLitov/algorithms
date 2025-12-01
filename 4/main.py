import re
from collections import defaultdict, deque
from typing import Set, Dict, List, Optional, Tuple


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
                return False

            if current_state in self.transitions and symbol in self.transitions[current_state]:
                current_state = self.transitions[current_state][symbol]
            else:
                return False

        return current_state in self.accept_states


class RegexInterpreter:
    """Интерпретатор регулярных выражений"""

    def __init__(self):
        self.operators = {'|', '*', '(', ')', '.', '+'}
        self.precedence = {'|': 1, '.': 2, '*': 3, '+': 3}

    def add_concat_operator(self, regex: str) -> str:
        """Добавление оператора конкатенации (.) в явном виде"""
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
                current_is_operand = char not in self.operators or char in {'*', '+', ')'}
                next_is_operand = next_char not in self.operators or next_char == '('

                if current_is_operand and next_is_operand:
                    result.append('.')

        return ''.join(result)

    def to_postfix(self, regex: str) -> str:
        """Преобразование регулярного выражения в обратную польскую запись"""
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
                stack.pop()  # Удаляем '('
            else:
                while (stack and stack[-1] != '(' and
                       self.precedence.get(stack[-1], 0) >= self.precedence.get(char, 0)):
                    output.append(stack.pop())
                stack.append(char)

            i += 1

        while stack:
            output.append(stack.pop())

        return ''.join(output)

    def build_nfa_from_postfix(self, postfix: str) -> NFA:
        """Построение НКА из обратной польской записи (алгоритм Томпсона)"""
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
                nfa2 = stack.pop()
                nfa1 = stack.pop()

                nfa1.end.is_final = False
                nfa1.end.add_epsilon(nfa2.start)

                stack.append(NFA(nfa1.start, nfa2.end))

            elif token == '*':  # Звезда Клини
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
                nfa = stack.pop()

                start = State()
                end = State(is_final=True)

                start.add_epsilon(nfa.start)
                nfa.end.is_final = False
                nfa.end.add_epsilon(nfa.start)
                nfa.end.add_epsilon(end)

                stack.append(NFA(start, end))

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
                    alphabet.add(symbol)

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

        # Шаг 4: Создание объекта ДКА
        dfa = DFA(
            states=set(range(len(dfa_states))),
            alphabet=alphabet,
            transitions=dfa_transitions,
            start_state=0,
            accept_states=accept_states
        )

        return dfa


class KMP:
    """Реализация алгоритма Кнута-Морриса-Пратта для поиска подстроки"""

    @staticmethod
    def build_lps(pattern: str) -> List[int]:
        """Построение таблицы длин префиксов-суффиксов (LPS)"""
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
        postfix = interpreter.to_postfix(pattern)
        nfa = interpreter.build_nfa_from_postfix(postfix)
        dfa = interpreter.nfa_to_dfa(nfa)

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
        import random
        return ''.join(random.choice(alphabet) for _ in range(length))

    @staticmethod
    def test_regex(regex: str, test_string: str, use_dfa: bool = True) -> Tuple[bool, List[int]]:
        """Тестирование регулярного выражения на строке"""
        try:
            # Используем встроенный модуль re для сравнения
            python_matches = []
            for match in re.finditer(regex, test_string):
                python_matches.append(match.start())

            # Используем наш интерпретатор
            interpreter = RegexInterpreter()
            postfix = interpreter.to_postfix(regex)
            nfa = interpreter.build_nfa_from_postfix(postfix)

            if use_dfa:
                dfa = interpreter.nfa_to_dfa(nfa)

                # Поиск всех вхождений
                our_matches = []
                for i in range(len(test_string)):
                    for j in range(i + 1, len(test_string) + 1):
                        if dfa.process_input(test_string[i:j]):
                            our_matches.append(i)
                            break
            else:
                # Используем НКА
                our_matches = []
                for i in range(len(test_string)):
                    for j in range(i + 1, len(test_string) + 1):
                        if nfa.process_input(test_string[i:j]):
                            our_matches.append(i)
                            break

            return python_matches == our_matches, our_matches

        except Exception as e:
            return False, []

    @staticmethod
    def compare_kmp_dfa(pattern: str, text: str) -> Tuple[List[int], List[int], bool]:
        """Сравнение результатов KMP и ДКА"""
        kmp_matches = KMP.search(text, pattern)

        interpreter = RegexInterpreter()
        postfix = interpreter.to_postfix(pattern)
        nfa = interpreter.build_nfa_from_postfix(postfix)
        dfa = interpreter.nfa_to_dfa(nfa)

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


def main():
    """Основная функция программы"""
    print("Интерпретатор регулярных выражений с генерацией ДКА/НКА")
    print("=" * 60)

    interpreter = RegexInterpreter()
    tester = RegexTester()

    while True:
        print("\n" + "=" * 60)
        print("Меню:")
        print("1. Построить НКА/ДКА по регулярному выражению")
        print("2. Протестировать регулярное выражение")
        print("3. Сравнить KMP и ДКА для поиска подстроки")
        print("4. Сгенерировать тестовую строку")
        print("5. Выход")

        choice = input("\nВыберите действие (1-5): ").strip()

        if choice == '1':
            regex = input("Введите регулярное выражение: ").strip()

            try:
                # Преобразование в обратную польскую запись
                postfix = interpreter.to_postfix(regex)
                print(f"\nОбратная польская запись: {postfix}")

                # Построение НКА
                print("\nПостроение НКА...")
                nfa = interpreter.build_nfa_from_postfix(postfix)
                print(f"НКА построен: начальное состояние {nfa.start.id}, конечное {nfa.end.id}")

                # Преобразование в ДКА
                print("\nПреобразование НКА в ДКА...")
                dfa = interpreter.nfa_to_dfa(nfa)
                print(f"ДКА построен:")
                print(f"  Состояния: {dfa.states}")
                print(f"  Алфавит: {dfa.alphabet}")
                print(f"  Начальное состояние: {dfa.start_state}")
                print(f"  Допускающие состояния: {dfa.accept_states}")
                print(f"  Переходы:")
                for state, trans in dfa.transitions.items():
                    for symbol, target in trans.items():
                        print(f"    {state} --{symbol}--> {target}")

                # Тестирование
                test_string = input("\nВведите строку для тестирования (или Enter для пропуска): ").strip()
                if test_string:
                    nfa_result = nfa.process_input(test_string)
                    dfa_result = dfa.process_input(test_string)
                    print(f"\nРезультаты:")
                    print(f"  НКА: строка {'принята' if nfa_result else 'отвергнута'}")
                    print(f"  ДКА: строка {'принята' if dfa_result else 'отвергнута'}")

            except Exception as e:
                print(f"Ошибка: {e}")

        elif choice == '2':
            regex = input("Введите регулярное выражение: ").strip()
            use_dfa = input("Использовать ДКА (y/n)? ").strip().lower() == 'y'

            # Генерация тестовой строки
            length = int(input("Длина тестовой строки: ").strip())
            test_string = tester.generate_test_string(length)
            print(f"\nТестовая строка: {test_string[:100]}..." if len(test_string) > 100 else test_string)

            # Тестирование
            success, matches = tester.test_regex(regex, test_string, use_dfa)

            if success:
                print(f"\n✓ Результаты совпадают с Python re")
                print(f"  Найдено {len(matches)} совпадений: {matches[:10]}{'...' if len(matches) > 10 else ''}")
            else:
                print(f"\n✗ Результаты не совпадают с Python re")
                print(f"  Наш интерпретатор нашел {len(matches)} совпадений")

        elif choice == '3':
            pattern = input("Введите подстроку для поиска: ").strip()
            length = int(input("Длина тестовой строки: ").strip())

            # Генерация тестовой строки
            test_string = tester.generate_test_string(length)
            print(f"\nТестовая строка: {test_string[:100]}..." if len(test_string) > 100 else test_string)

            # Сравнение KMP и ДКА
            kmp_matches, dfa_matches, equal = tester.compare_kmp_dfa(pattern, test_string)

            print(f"\nРезультаты сравнения:")
            print(f"  KMP найдено: {len(kmp_matches)} совпадений")
            print(f"  ДКА найдено: {len(dfa_matches)} совпадений")

            if equal:
                print(f"✓ Результаты идентичны")
                if kmp_matches:
                    print(f"  Совпадения: {kmp_matches[:10]}{'...' if len(kmp_matches) > 10 else ''}")
            else:
                print(f"✗ Результаты различаются")
                print(f"  KMP: {kmp_matches}")
                print(f"  ДКА: {dfa_matches}")

        elif choice == '4':
            length = int(input("Длина строки: ").strip())
            alphabet = input("Алфавит (по умолчанию abc): ").strip() or "abc"

            test_string = tester.generate_test_string(length, alphabet)
            print(f"\nСгенерированная строка:")
            print(test_string)

        elif choice == '5':
            print("Выход из программы.")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()