import csv
from collections import defaultdict, deque


class DFA:
    """
    Класс для представления детерминированного конечного автомата
    """

    def __init__(self, states, alphabet, transitions, start_state, accept_states):
        """
        Инициализация ДКА

        Параметры:
        - states: множество состояний
        - alphabet: алфавит (символы входной строки)
        - transitions: словарь переходов
        - start_state: начальное состояние
        - accept_states: множество допускающих состояний
        """
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions
        self.start_state = start_state
        self.accept_states = set(accept_states)

    def process_input(self, input_string):
        """
        Обработка входной строки ДКА

        Возвращает True, если строка принимается автоматом,
        и False в противном случае
        """
        current_state = self.start_state

        for symbol in input_string:
            if symbol not in self.alphabet:
                raise ValueError(f"Символ '{symbol}' не найден в алфавите")

            if symbol in self.transitions[current_state]:
                current_state = self.transitions[current_state][symbol]
            else:
                # Если нет перехода по символу, строка не принимается
                return False

        return current_state in self.accept_states


def read_dfa_from_csv(filepath):
    """
    Чтение описания ДКА из CSV-файла

    Формат CSV:
    - Первая строка: заголовки (первая ячейка пустая, затем символы алфавита)
    - Последующие строки: для каждого состояния указываются переходы
    - Последний столбец: '*' для допускающих состояний
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        data = list(reader)

    # Извлекаем алфавит из первой строки (пропускаем первую пустую ячейку)
    alphabet = data[0][1:-1]  # Последний столбец - метка допускающего состояния

    # Инициализируем структуры для хранения данных об автомате
    states = set()
    transitions = {}
    start_state = None
    accept_states = set()

    # Обрабатываем каждую строку (состояние)
    for i, row in enumerate(data[1:]):
        state_name = row[0].strip()
        states.add(state_name)

        # Первое состояние считаем начальным
        if i == 0:
            start_state = state_name

        # Проверяем, является ли состояние допускающим (последний столбец содержит '*')
        if row[-1] == '*':
            accept_states.add(state_name)

        # Создаем словарь переходов для текущего состояния
        state_transitions = {}
        for j, symbol in enumerate(alphabet):
            if j + 1 < len(row):  # Проверяем, что в строке достаточно столбцов
                target_state = row[j + 1].strip()
                if target_state:  # Если есть переход
                    state_transitions[symbol] = target_state

        transitions[state_name] = state_transitions

    # Проверяем полноту переходов
    for state in states:
        for symbol in alphabet:
            if symbol not in transitions[state]:
                # Если нет перехода, добавляем переход в "ловушку"
                trap_state = "trap"
                if trap_state not in states:
                    states.add(trap_state)
                    transitions[trap_state] = {}
                    for sym in alphabet:
                        transitions[trap_state][sym] = trap_state
                transitions[state][symbol] = trap_state

    return DFA(states, alphabet, transitions, start_state, accept_states)


def minimize_dfa_table(dfa):
    """
    Минимизация ДКА с использованием алгоритма таблицы различий (алгоритм Хопкрофта)

    Алгоритм:
    1. Строим начальное разбиение на два класса: допускающие и недопускающие состояния
    2. Итерационно уточняем разбиение, пока оно не стабилизируется
    3. Строим новый ДКА на основе полученных классов эквивалентности
    """
    # Шаг 1: Начальное разбиение
    partition = [dfa.accept_states.copy(), dfa.states - dfa.accept_states]

    # Удаляем пустые множества
    partition = [group for group in partition if group]

    # Шаг 2: Итерационное уточнение разбиения
    changed = True
    while changed:
        changed = False
        new_partition = []

        for group in partition:
            if len(group) <= 1:
                new_partition.append(group)
                continue

            # Разделяем группу на подгруппы по эквивалентности
            subgroup_dict = {}

            for state in group:
                # Для каждого состояния вычисляем "сигнатуру" -
                # к каким группам ведут переходы по каждому символу
                signature = []
                for symbol in sorted(dfa.alphabet):
                    next_state = dfa.transitions[state].get(symbol, state)
                    # Находим индекс группы, содержащей next_state
                    for i, p in enumerate(partition):
                        if next_state in p:
                            signature.append(i)
                            break
                signature = tuple(signature)

                # Группируем состояния по одинаковым сигнатурам
                if signature not in subgroup_dict:
                    subgroup_dict[signature] = set()
                subgroup_dict[signature].add(state)

            # Добавляем новые подгруппы в разбиение
            for subgroup in subgroup_dict.values():
                new_partition.append(subgroup)

            # Если создали больше одной подгруппы, значит разбиение изменилось
            if len(subgroup_dict) > 1:
                changed = True

        partition = new_partition

    # Шаг 3: Построение нового ДКА на основе классов эквивалентности
    # Создаем отображение из состояния в его класс эквивалентности
    state_to_class = {}
    for i, group in enumerate(partition):
        for state in group:
            state_to_class[state] = i

    # Создаем новые состояния, переходы и т.д.
    new_states = set([f"C{i}" for i in range(len(partition))])
    new_alphabet = dfa.alphabet
    new_transitions = {}
    new_start_state = f"C{state_to_class[dfa.start_state]}"
    new_accept_states = set()

    # Находим допускающие классы
    for i, group in enumerate(partition):
        class_name = f"C{i}"
        new_transitions[class_name] = {}

        # Если в классе есть допускающее состояние, то весь класс допускающий
        if any(state in dfa.accept_states for state in group):
            new_accept_states.add(class_name)

        # Выбираем представителя класса для построения переходов
        representative = next(iter(group))

        # Строим переходы для нового состояния
        for symbol in dfa.alphabet:
            if symbol in dfa.transitions[representative]:
                next_state = dfa.transitions[representative][symbol]
                next_class = state_to_class[next_state]
                new_transitions[class_name][symbol] = f"C{next_class}"

    return DFA(new_states, new_alphabet, new_transitions, new_start_state, new_accept_states)


def minimize_dfa_hopcroft(dfa):
    """
    Минимизация ДКА с использованием алгоритма Хопкрофта (более эффективная версия)

    Алгоритм:
    // 1. Начальное разбиение: P = {F, Q \ F}
    2. Инициализируем очередь обработки всеми блоками из P
    3. Пока очередь не пуста, извлекаем блок, разбиваем другие блоки
    4. Возвращаем минимальный ДКА
    """
    # Шаг 1: Начальное разбиение
    P = [dfa.accept_states.copy(), dfa.states - dfa.accept_states]
    P = [block for block in P if block]  # Удаляем пустые блоки

    # Шаг 2: Инициализация очереди
    W = deque()
    for block in P:
        W.append(block)

    # Шаг 3: Основной цикл алгоритма
    while W:
        A = W.popleft()

        for symbol in dfa.alphabet:
            # Находим множество состояний, которые переходят в A по symbol
            X = set()
            for state in dfa.states:
                if dfa.transitions[state].get(symbol, state) in A:
                    X.add(state)

            # Обновляем разбиение
            new_P = []
            for Y in P:
                intersection = Y & X
                difference = Y - X

                if intersection and difference:
                    # Разбиваем Y на два блока
                    new_P.append(intersection)
                    new_P.append(difference)

                    # Обновляем очередь
                    if Y in W:
                        W.remove(Y)
                        W.append(intersection)
                        W.append(difference)
                    else:
                        if len(intersection) <= len(difference):
                            W.append(intersection)
                        else:
                            W.append(difference)
                else:
                    # Не разбиваем Y
                    new_P.append(Y)

            P = new_P

    # Шаг 4: Построение нового ДКА
    # Создаем отображение из состояния в его блок
    state_to_block = {}
    for i, block in enumerate(P):
        for state in block:
            state_to_block[state] = i

    # Создаем новый ДКА
    new_states = set([f"B{i}" for i in range(len(P))])
    new_alphabet = dfa.alphabet
    new_transitions = {}
    new_start_state = f"B{state_to_block[dfa.start_state]}"
    new_accept_states = set()

    for i, block in enumerate(P):
        block_name = f"B{i}"
        new_transitions[block_name] = {}

        # Проверяем, является ли блок допускающим
        if any(state in dfa.accept_states for state in block):
            new_accept_states.add(block_name)

        # Выбираем представителя для построения переходов
        representative = next(iter(block))

        for symbol in dfa.alphabet:
            if symbol in dfa.transitions[representative]:
                next_state = dfa.transitions[representative][symbol]
                next_block = state_to_block[next_state]
                new_transitions[block_name][symbol] = f"B{next_block}"

    return DFA(new_states, new_alphabet, new_transitions, new_start_state, new_accept_states)


def are_equivalent(dfa1, dfa2, test_strings=None, max_depth=10):
    """
    Проверка эквивалентности двух ДКА

    Алгоритм:
    1. Проверяем, что алфавиты совпадают
    2. Используем алгоритм проверки через обход BFS
    3. Если находим строку, которая принимается одним автоматом, но не другим,
       то автоматы не эквивалентны
    """
    # Проверяем совпадение алфавитов
    if dfa1.alphabet != dfa2.alphabet:
        return False, "Алфавиты не совпадают"

    # Если предоставлены тестовые строки, проверяем их
    if test_strings:
        for test_str in test_strings:
            result1 = dfa1.process_input(test_str)
            result2 = dfa2.process_input(test_str)
            if result1 != result2:
                return False, f"Различаются на строке '{test_str}': DFA1={result1}, DFA2={result2}"

    # Алгоритм BFS для поиска различий
    visited = set()
    queue = deque()

    # Начинаем с пары начальных состояний
    start_pair = (dfa1.start_state, dfa2.start_state)
    visited.add(start_pair)
    queue.append((start_pair, ""))  # (пара состояний, строка, приведшая к ним)

    while queue:
        (state1, state2), path = queue.popleft()

        # Проверяем, есть ли различие в допускании
        is_accept1 = state1 in dfa1.accept_states
        is_accept2 = state2 in dfa2.accept_states

        if is_accept1 != is_accept2:
            return False, f"Различаются на строке '{path}': DFA1={is_accept1}, DFA2={is_accept2}"

        # Добавляем соседние пары состояний
        for symbol in sorted(dfa1.alphabet):
            next1 = dfa1.transitions[state1].get(symbol, state1)
            next2 = dfa2.transitions[state2].get(symbol, state2)
            next_pair = (next1, next2)

            if next_pair not in visited:
                visited.add(next_pair)
                # Ограничиваем длину строк для предотвращения бесконечного цикла
                if len(path) < max_depth:
                    queue.append((next_pair, path + symbol))

    return True, "Автоматы эквивалентны"


def write_dfa_to_csv(dfa, filepath):
    """
    Запись ДКА в CSV-файл
    """
    with open(filepath, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Заголовок
        header = ['state'] + sorted(dfa.alphabet) + ['accept']
        writer.writerow(header)

        # Записываем каждое состояние
        for state in sorted(dfa.states):
            row = [state]
            for symbol in sorted(dfa.alphabet):
                row.append(dfa.transitions[state].get(symbol, ''))

            # Добавляем метку допускающего состояния
            if state in dfa.accept_states:
                row.append('*')
            else:
                row.append('')

            writer.writerow(row)


def main():
    """
    Основная функция программы
    """
    print("Программа минимизации ДКА и проверки эквивалентности")
    print("=" * 60)

    try:
        # Чтение исходного ДКА
        csv_file = input("Введите путь к CSV-файлу с описанием ДКА: ")
        original_dfa = read_dfa_from_csv(csv_file)

        print(f"\nИсходный ДКА загружен:")
        print(f"  Состояния: {', '.join(sorted(original_dfa.states))}")
        print(f"  Алфавит: {', '.join(sorted(original_dfa.alphabet))}")
        print(f"  Начальное состояние: {original_dfa.start_state}")
        print(f"  Допускающие состояния: {', '.join(sorted(original_dfa.accept_states))}")

        # Выбор алгоритма минимизации
        print("\n" + "=" * 60)
        print("Выберите алгоритм минимизации:")
        print("1. Алгоритм таблицы различий")
        print("2. Алгоритм Хопкрофта")
        choice = input("Ваш выбор (1 или 2): ").strip()

        if choice == '1':
            minimized_dfa = minimize_dfa_table(original_dfa)
            algo_name = "таблицы различий"
        elif choice == '2':
            minimized_dfa = minimize_dfa_hopcroft(original_dfa)
            algo_name = "Хопкрофта"
        else:
            print("Неверный выбор. Используется алгоритм таблицы различий.")
            minimized_dfa = minimize_dfa_table(original_dfa)
            algo_name = "таблицы различий"

        print(f"\nМинимизация выполнена (алгоритм {algo_name}):")
        print(f"  Состояния: {', '.join(sorted(minimized_dfa.states))}")
        print(f"  Алфавит: {', '.join(sorted(minimized_dfa.alphabet))}")
        print(f"  Начальное состояние: {minimized_dfa.start_state}")
        print(f"  Допускающие состояния: {', '.join(sorted(minimized_dfa.accept_states))}")

        # Проверка эквивалентности
        print("\n" + "=" * 60)
        print("Проверка эквивалентности исходного и минимизированного ДКА:")

        # Тестовые строки для проверки
        test_strings = ["", "a", "b", "aa", "ab", "ba", "bb", "aba", "bab", "aabb"]
        test_strings = [s for s in test_strings if all(c in original_dfa.alphabet for c in s)]

        equivalent, message = are_equivalent(original_dfa, minimized_dfa, test_strings)
        print(f"  Результат: {message}")

        # Дополнительная проверка с ручным вводом строк
        print("\n" + "=" * 60)
        print("Ручная проверка эквивалентности (пустая строка для завершения):")

        while True:
            test_str = input("\nВведите строку для проверки: ").strip()

            if not test_str:
                print("Завершение ручной проверки.")
                break

            try:
                result1 = original_dfa.process_input(test_str)
                result2 = minimized_dfa.process_input(test_str)

                if result1 == result2:
                    print(f"Оба автомата {'принимают' if result1 else 'отвергают'} строку '{test_str}'")
                else:
                    print(f"НЕСОВПАДЕНИЕ: Исходный ДКА - {result1}, Минимизированный ДКА - {result2}")

            except ValueError as e:
                print(f"Ошибка: {e}")

        # Сохранение минимизированного ДКА
        print("\n" + "=" * 60)
        save_choice = input("Сохранить минимизированный ДКА в CSV-файл? (да/нет): ").strip().lower()

        if save_choice in ['да', 'д', 'yes', 'y']:
            output_file = input("Введите имя файла для сохранения: ").strip()
            write_dfa_to_csv(minimized_dfa, output_file)
            print(f"Минимизированный ДКА сохранен в файл '{output_file}'")

    except FileNotFoundError:
        print(f"Ошибка: Файл '{csv_file}' не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    main()