import csv
from collections import defaultdict, deque
import graphviz
import os


class DFA:
    def __init__(self, states, alphabet, transitions, start_state, accept_states):
        """
        Инициализация ДКА
        """
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions
        self.start_state = start_state
        self.accept_states = set(accept_states)

    def process_input(self, input_string):
        """
        Обработка входной строки ДКА
        """
        current_state = self.start_state

        for symbol in input_string:
            if symbol not in self.alphabet:
                raise ValueError(f"Символ '{symbol}' не найден в алфавите")

            if symbol in self.transitions[current_state]:
                current_state = self.transitions[current_state][symbol]
            else:
                return False

        return current_state in self.accept_states

    def get_reachable_states(self):
        """
        Получить только достижимые состояния из начального
        """
        reachable = set()
        stack = [self.start_state]

        while stack:
            state = stack.pop()
            if state in reachable:
                continue
            reachable.add(state)

            # Добавляем все состояния, в которые можно перейти
            for symbol in self.alphabet:
                if symbol in self.transitions[state]:
                    next_state = self.transitions[state][symbol]
                    if next_state not in reachable:
                        stack.append(next_state)

        return reachable

    def minimize_and_visualize(self, algorithm='hopcroft'):
        """
        Минимизация ДКА и визуализация результата
        """
        if algorithm == 'table':
            minimized = minimize_dfa_table(self)
        else:
            minimized = minimize_dfa_hopcroft(self)

        # Получаем только достижимые состояния
        reachable = minimized.get_reachable_states()

        # Создаем новый ДКА только с достижимыми состояниями
        reachable_states = minimized.states & reachable
        reachable_accept = minimized.accept_states & reachable

        # Фильтруем переходы
        reachable_transitions = {}
        for state in reachable_states:
            reachable_transitions[state] = {}
            for symbol in minimized.alphabet:
                if symbol in minimized.transitions[state]:
                    next_state = minimized.transitions[state][symbol]
                    if next_state in reachable_states:
                        reachable_transitions[state][symbol] = next_state

        minimized_reachable = DFA(
            reachable_states,
            minimized.alphabet,
            reachable_transitions,
            minimized.start_state if minimized.start_state in reachable_states else next(iter(reachable_states)),
            reachable_accept
        )

        # Визуализируем
        visualize_dfa(minimized_reachable, title="Минимизированный ДКА (только достижимые состояния)")

        return minimized_reachable


def read_dfa_from_csv(filepath):
    """
    Чтение описания ДКА из CSV-файла
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        data = list(reader)

    alphabet = data[0][1:-1]

    states = set()
    transitions = {}
    start_state = None
    accept_states = set()

    for i, row in enumerate(data[1:]):
        state_name = row[0].strip()
        states.add(state_name)

        if i == 0:
            start_state = state_name

        if row[-1] == '*':
            accept_states.add(state_name)

        state_transitions = {}
        for j, symbol in enumerate(alphabet):
            if j + 1 < len(row):
                target_state = row[j + 1].strip()
                if target_state:
                    state_transitions[symbol] = target_state

        transitions[state_name] = state_transitions

    # Добавляем ловушки для отсутствующих переходов
    for state in states:
        for symbol in alphabet:
            if symbol not in transitions[state]:
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
    Минимизация ДКА с использованием алгоритма таблицы различий
    """
    partition = [dfa.accept_states.copy(), dfa.states - dfa.accept_states]
    partition = [group for group in partition if group]

    changed = True
    while changed:
        changed = False
        new_partition = []

        for group in partition:
            if len(group) <= 1:
                new_partition.append(group)
                continue

            subgroup_dict = {}
            for state in group:
                signature = []
                for symbol in sorted(dfa.alphabet):
                    next_state = dfa.transitions[state].get(symbol, state)
                    for i, p in enumerate(partition):
                        if next_state in p:
                            signature.append(i)
                            break
                signature = tuple(signature)

                if signature not in subgroup_dict:
                    subgroup_dict[signature] = set()
                subgroup_dict[signature].add(state)

            for subgroup in subgroup_dict.values():
                new_partition.append(subgroup)

            if len(subgroup_dict) > 1:
                changed = True

        partition = new_partition

    state_to_class = {}
    for i, group in enumerate(partition):
        for state in group:
            state_to_class[state] = i

    new_states = set([f"C{i}" for i in range(len(partition))])
    new_alphabet = dfa.alphabet
    new_transitions = {}
    new_start_state = f"C{state_to_class[dfa.start_state]}"
    new_accept_states = set()

    for i, group in enumerate(partition):
        class_name = f"C{i}"
        new_transitions[class_name] = {}

        if any(state in dfa.accept_states for state in group):
            new_accept_states.add(class_name)

        representative = next(iter(group))
        for symbol in dfa.alphabet:
            if symbol in dfa.transitions[representative]:
                next_state = dfa.transitions[representative][symbol]
                next_class = state_to_class[next_state]
                new_transitions[class_name][symbol] = f"C{next_class}"

    return DFA(new_states, new_alphabet, new_transitions, new_start_state, new_accept_states)


def minimize_dfa_hopcroft(dfa):
    """
    Минимизация ДКА с использованием алгоритма Хопкрофта
    """
    P = [dfa.accept_states.copy(), dfa.states - dfa.accept_states]
    P = [block for block in P if block]

    W = deque()
    for block in P:
        W.append(block)

    while W:
        A = W.popleft()

        for symbol in dfa.alphabet:
            X = set()
            for state in dfa.states:
                if dfa.transitions[state].get(symbol, state) in A:
                    X.add(state)

            new_P = []
            for Y in P:
                intersection = Y & X
                difference = Y - X

                if intersection and difference:
                    new_P.append(intersection)
                    new_P.append(difference)

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
                    new_P.append(Y)

            P = new_P

    state_to_block = {}
    for i, block in enumerate(P):
        for state in block:
            state_to_block[state] = i

    new_states = set([f"B{i}" for i in range(len(P))])
    new_alphabet = dfa.alphabet
    new_transitions = {}
    new_start_state = f"B{state_to_block[dfa.start_state]}"
    new_accept_states = set()

    for i, block in enumerate(P):
        block_name = f"B{i}"
        new_transitions[block_name] = {}

        if any(state in dfa.accept_states for state in block):
            new_accept_states.add(block_name)

        representative = next(iter(block))
        for symbol in dfa.alphabet:
            if symbol in dfa.transitions[representative]:
                next_state = dfa.transitions[representative][symbol]
                next_block = state_to_block[next_state]
                new_transitions[block_name][symbol] = f"B{next_block}"

    return DFA(new_states, new_alphabet, new_transitions, new_start_state, new_accept_states)


def visualize_dfa(dfa, title="ДКА", filename="dfa_graph"):
    """
    Визуализация ДКА с помощью graphviz
    """
    dot = graphviz.Digraph(comment=title)
    dot.attr(rankdir='LR', label=title, labelloc='t', fontsize='16')

    # Добавляем состояния
    for state in sorted(dfa.states):
        if state == dfa.start_state:
            # Начальное состояние с дополнительным кругом
            dot.node('start', '', shape='point', width='0.1')
            if state in dfa.accept_states:
                dot.node(state, shape='doublecircle')
                dot.edge('start', state)
            else:
                dot.node(state, shape='circle')
                dot.edge('start', state)
        elif state in dfa.accept_states:
            dot.node(state, shape='doublecircle')
        else:
            dot.node(state, shape='circle')

    # Добавляем переходы
    for from_state in dfa.transitions:
        transitions_by_target = defaultdict(list)

        for symbol, to_state in dfa.transitions[from_state].items():
            transitions_by_target[to_state].append(symbol)

        for to_state, symbols in transitions_by_target.items():
            if from_state == to_state:
                # Петля
                dot.edge(from_state, from_state, label=', '.join(sorted(symbols)))
            else:
                dot.edge(from_state, to_state, label=', '.join(sorted(symbols)))

    # Сохраняем и показываем граф
    output_file = f"{filename}.png"
    dot.render(filename=filename, format='png', cleanup=True)

    # Пытаемся открыть файл
    try:
        if os.name == 'nt':  # Windows
            os.startfile(output_file)
        elif os.name == 'posix':  # Linux, macOS
            os.system(f'xdg-open {output_file}' if os.uname().sysname == 'Linux' else f'open {output_file}')
    except:
        print(f"Граф сохранен в файл: {output_file}")

    return dot


def step_by_step_execution(dfa, input_string):
    """
    Пошаговое выполнение ДКА
    """
    print(f"\n{'=' * 60}")
    print(f"ПОШАГОВАЯ ОБРАБОТКА СТРОКИ: '{input_string}'")
    print(f"{'=' * 60}\n")

    current_state = dfa.start_state
    step = 1

    print(f"Шаг {step}: Начальное состояние: {current_state}")
    print(f"       Текущая строка: '{input_string}'")
    print(f"       Индекс символа: 0/{len(input_string)}")
    print()

    for idx, symbol in enumerate(input_string):
        step += 1

        if symbol not in dfa.alphabet:
            print(f"Шаг {step}: ОШИБКА! Символ '{symbol}' не в алфавите")
            return False

        if symbol in dfa.transitions.get(current_state, {}):
            next_state = dfa.transitions[current_state][symbol]

            print(f"Шаг {step}: Символ: '{symbol}'")
            print(f"       Переход: {current_state} --({symbol})--> {next_state}")
            print(f"       Обработано: '{input_string[:idx + 1]}'")
            print(f"       Осталось: '{input_string[idx + 1:]}'")
            print(f"       Текущее состояние: {next_state}")

            current_state = next_state
        else:
            print(f"Шаг {step}: ОШИБКА! Нет перехода из состояния {current_state} по символу '{symbol}'")
            return False

        print()

    step += 1
    is_accepted = current_state in dfa.accept_states

    print(f"Шаг {step}: КОНЕЦ ОБРАБОТКИ")
    print(f"       Финальное состояние: {current_state}")
    print(f"       Это {'ДОПУСКАЮЩЕЕ' if is_accepted else 'НЕДОПУСКАЮЩЕЕ'} состояние")
    print(f"\n{'=' * 60}")
    print(f"РЕЗУЛЬТАТ: Строка '{input_string}' {'ПРИНЯТА' if is_accepted else 'ОТВЕРГНУТА'}")
    print(f"{'=' * 60}")

    return is_accepted


def main():
    """
    Основная функция программы
    """
    print("Программа минимизации ДКА с визуализацией")
    print("=" * 60)

    try:
        # Чтение исходного ДКА
        csv_file = input("Введите путь к CSV-файлу с описанием ДКА: ").strip()
        original_dfa = read_dfa_from_csv(csv_file)

        print(f"\nИсходный ДКА загружен:")
        print(f"  Состояния: {', '.join(sorted(original_dfa.states))}")
        print(f"  Алфавит: {', '.join(sorted(original_dfa.alphabet))}")
        print(f"  Начальное состояние: {original_dfa.start_state}")
        print(f"  Допускающие состояния: {', '.join(sorted(original_dfa.accept_states))}")

        # Визуализация исходного ДКА
        print("\n" + "=" * 60)
        vis_choice = input("Визуализировать исходный ДКА? (да/нет): ").strip().lower()
        if vis_choice in ['да', 'д', 'yes', 'y']:
            visualize_dfa(original_dfa, title="Исходный ДКА", filename="original_dfa")

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

        # Визуализация минимизированного ДКА (только достижимые состояния)
        print("\n" + "=" * 60)
        print("Визуализация минимизированного ДКА...")
        minimized_reachable = minimized_dfa.minimize_and_visualize(algo_name)

        # Пошаговая обработка строки
        print("\n" + "=" * 60)
        test_str = input("Введите строку для пошаговой обработки минимизированным ДКА (пусто - пропустить): ").strip()
        if test_str:
            step_by_step_execution(minimized_reachable, test_str)

        # Тестирование нескольких строк
        print("\n" + "=" * 60)
        print("Тестирование нескольких строк (пустая строка для завершения):")

        test_strings = []
        while True:
            test_str = input(f"Строка {len(test_strings) + 1}: ").strip()
            if not test_str:
                break
            test_strings.append(test_str)

        if test_strings:
            print(f"\nРезультаты тестирования {len(test_strings)} строк:")
            print("-" * 40)
            for test_str in test_strings:
                try:
                    result_orig = original_dfa.process_input(test_str)
                    result_min = minimized_reachable.process_input(test_str)
                    status = "✓" if result_orig == result_min else "✗"
                    print(f"{status} '{test_str}': оригинал={result_orig}, минимизированный={result_min}")
                except ValueError as e:
                    print(f"✗ '{test_str}': {e}")

        # Сохранение минимизированного ДКА
        print("\n" + "=" * 60)
        save_choice = input("Сохранить минимизированный ДКА в CSV-файл? (да/нет): ").strip().lower()

        if save_choice in ['да', 'д', 'yes', 'y']:
            output_file = input("Введите имя файла для сохранения: ").strip()
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                header = ['state'] + sorted(minimized_reachable.alphabet) + ['accept']
                writer.writerow(header)

                for state in sorted(minimized_reachable.states):
                    row = [state]
                    for symbol in sorted(minimized_reachable.alphabet):
                        row.append(minimized_reachable.transitions[state].get(symbol, ''))

                    if state in minimized_reachable.accept_states:
                        row.append('*')
                    else:
                        row.append('')

                    writer.writerow(row)

            print(f"Минимизированный ДКА сохранен в файл '{output_file}'")

    except FileNotFoundError:
        print(f"Ошибка: Файл '{csv_file}' не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Проверка наличия graphviz
    try:
        import graphviz

        main()
    except ImportError:
        print("Ошибка: Для работы визуализатора требуется установить graphviz")
        print("Установите: pip install graphviz")
        print("Также необходимо установить Graphviz с официального сайта: https://graphviz.org/download/")