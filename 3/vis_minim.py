import csv
from collections import defaultdict, deque
import graphviz
import os


class DFA:
    def __init__(self, states, alphabet, transitions, start_state, accept_states):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions
        self.start_state = start_state
        self.accept_states = set(accept_states)

    def process_input(self, input_string):
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
        """Получить только достижимые состояния из начального"""
        reachable = set()
        stack = [self.start_state]

        while stack:
            state = stack.pop()
            if state in reachable:
                continue
            reachable.add(state)

            for symbol in self.alphabet:
                if symbol in self.transitions[state]:
                    next_state = self.transitions[state][symbol]
                    if next_state not in reachable:
                        stack.append(next_state)

        return reachable

    def is_trap_state(self, state):
        """
        Проверяет, является ли состояние ловушкой (поглощающим).
        Ловушка - это состояние, из которого нет выхода в другие состояния,
        и оно не является допускающим.
        """
        # Если состояние допускающее - это не ловушка
        if state in self.accept_states:
            return False

        # Проверяем все переходы из этого состояния
        # Если все переходы ведут обратно в это же состояние - это ловушка
        for symbol in self.alphabet:
            if symbol in self.transitions[state]:
                next_state = self.transitions[state][symbol]
                if next_state != state:
                    return False  # Есть переход в другое состояние

        return True  # Все переходы ведут в само состояние

    def get_useful_states(self):
        """
        Получает только полезные состояния:
        1. Достижимые из начального
        2. Не являющиеся ловушками
        """
        reachable = self.get_reachable_states()
        useful_states = set()

        for state in reachable:
            if not self.is_trap_state(state):
                useful_states.add(state)

        return useful_states

    def minimize_and_visualize(self, algorithm='hopcroft'):
        """
        Минимизация ДКА и визуализация результата БЕЗ ЛОВУШЕК
        """
        if algorithm == 'table':
            minimized = minimize_dfa_table(self)
        else:
            minimized = minimize_dfa_hopcroft(self)

        # Получаем только полезные состояния (без ловушек)
        useful_states = minimized.get_useful_states()

        # Если начальное состояние стало ловушкой, выбираем первое полезное
        if minimized.start_state not in useful_states and useful_states:
            # Ищем ближайшее достижимое полезное состояние
            new_start = self._find_nearest_useful_state(minimized.start_state, minimized)
            if new_start:
                start_state = new_start
            else:
                start_state = next(iter(useful_states))
        else:
            start_state = minimized.start_state

        # Создаем новый ДКА только с полезными состояниями
        useful_accept = minimized.accept_states & useful_states

        # Фильтруем переходы
        useful_transitions = {}
        for state in useful_states:
            useful_transitions[state] = {}
            for symbol in minimized.alphabet:
                if symbol in minimized.transitions[state]:
                    next_state = minimized.transitions[state][symbol]
                    if next_state in useful_states:
                        useful_transitions[state][symbol] = next_state
                    elif next_state in minimized.states:
                        # Если переход ведет в ловушку, перенаправляем его в "dead"
                        useful_transitions[state][symbol] = "dead"

        # Добавляем состояние "dead", если есть переходы в него
        dead_exists = False
        for state in useful_transitions.values():
            if "dead" in state.values():
                dead_exists = True
                break

        if dead_exists:
            useful_states.add("dead")
            useful_transitions["dead"] = {}
            for symbol in minimized.alphabet:
                useful_transitions["dead"][symbol] = "dead"

        minimized_useful = DFA(
            useful_states,
            minimized.alphabet,
            useful_transitions,
            start_state,
            useful_accept
        )

        # Визуализируем
        visualize_dfa(minimized_useful, title="Минимизированный ДКА (без ловушек)",
                      highlight_path=minimized_useful.start_state)

        return minimized_useful

    def _find_nearest_useful_state(self, start_state, dfa):
        """Находит ближайшее полезное состояние из данного"""
        visited = set()
        queue = deque([start_state])

        while queue:
            state = queue.popleft()
            if state in visited:
                continue
            visited.add(state)

            if not dfa.is_trap_state(state):
                return state

            for symbol in dfa.alphabet:
                if symbol in dfa.transitions[state]:
                    next_state = dfa.transitions[state][symbol]
                    if next_state not in visited:
                        queue.append(next_state)

        return None


def read_dfa_from_csv(filepath):
    """Чтение описания ДКА из CSV-файла"""
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

    # НЕ добавляем ловушки автоматически!
    # Только если переходы не указаны, оставляем как есть
    # Это позволяет видеть настоящие ловушки в исходном автомате

    return DFA(states, alphabet, transitions, start_state, accept_states)


def visualize_dfa(dfa, title="ДКА", filename=None, highlight_path=None):
    """
    Визуализация ДКА с помощью graphviz
    highlight_path: если задан, подсвечивает путь из этого состояния
    """
    if filename is None:
        filename = "dfa_graph"

    dot = graphviz.Digraph(comment=title)
    dot.attr(rankdir='LR', label=title, labelloc='t', fontsize='16')

    # Определяем стили для разных типов состояний
    for state in sorted(dfa.states):
        # Проверяем, является ли состояние ловушкой
        is_trap = dfa.is_trap_state(state) if hasattr(dfa, 'is_trap_state') else False

        # Стили для разных типов состояний
        if state == dfa.start_state:
            if is_trap:
                dot.node(state, f"{state}\n(ловушка)", shape='circle', style='filled',
                         fillcolor='lightgrey', color='red', penwidth='2')
                dot.node('start', '', shape='point', width='0.1')
                dot.edge('start', state)
            elif state in dfa.accept_states:
                dot.node(state, shape='doublecircle', style='filled', fillcolor='lightblue')
                dot.node('start', '', shape='point', width='0.1')
                dot.edge('start', state)
            else:
                dot.node(state, shape='circle', style='filled', fillcolor='lightgreen')
                dot.node('start', '', shape='point', width='0.1')
                dot.edge('start', state)
        elif state == "dead":
            dot.node(state, "dead", shape='circle', style='filled',
                     fillcolor='lightgrey', color='red', penwidth='2')
        elif is_trap:
            dot.node(state, f"{state}\n(ловушка)", shape='circle', style='filled',
                     fillcolor='lightgrey', color='red', penwidth='2')
        elif state in dfa.accept_states:
            dot.node(state, shape='doublecircle', style='filled', fillcolor='lightblue')
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

    print(f"\n✓ Граф сохранен в файл: {output_file}")

    # Пытаемся открыть файл
    try:
        if os.name == 'nt':  # Windows
            os.startfile(output_file)
        elif os.name == 'posix':  # Linux, macOS
            if os.uname().sysname == 'Linux':
                os.system(f'xdg-open {output_file}')
            else:  # macOS
                os.system(f'open {output_file}')
    except:
        print("Не удалось автоматически открыть файл. Откройте его вручную.")

    return dot


def visualize_path(dfa, input_string, filename="dfa_path"):
    """
    Визуализация только пути обработки конкретной строки
    """
    dot = graphviz.Digraph(comment="Путь обработки строки")
    dot.attr(rankdir='LR', label=f"Путь обработки: '{input_string}'",
             labelloc='t', fontsize='16')

    # Выполняем обработку строки и запоминаем путь
    current_state = dfa.start_state
    path = [current_state]

    for symbol in input_string:
        if symbol not in dfa.alphabet:
            print(f"Символ '{symbol}' не в алфавите!")
            return None

        if symbol in dfa.transitions[current_state]:
            current_state = dfa.transitions[current_state][symbol]
            path.append(current_state)
        else:
            print(f"Нет перехода из {current_state} по символу '{symbol}'!")
            return None

    # Рисуем только состояния на пути
    for i, state in enumerate(set(path)):  # Используем set для уникальных состояний
        if state == dfa.start_state:
            dot.node(state, shape='doublecircle' if state in dfa.accept_states else 'circle',
                     style='filled', fillcolor='lightgreen')
        elif state in dfa.accept_states:
            dot.node(state, shape='doublecircle')
        else:
            dot.node(state, shape='circle')

    # Рисуем переходы на пути
    current_state = dfa.start_state
    dot.node('start', '', shape='point')
    dot.edge('start', current_state)

    for i, symbol in enumerate(input_string):
        next_state = dfa.transitions[current_state][symbol]

        # Определяем цвет для перехода
        color = 'blue' if i % 2 == 0 else 'green'

        dot.edge(current_state, next_state, label=symbol, color=color, penwidth='2')
        current_state = next_state

    # Сохраняем
    output_file = f"{filename}.png"
    dot.render(filename=filename, format='png', cleanup=True)

    print(f"\n✓ Путь обработки сохранен в файл: {output_file}")

    try:
        if os.name == 'nt':
            os.startfile(output_file)
        elif os.name == 'posix':
            if os.uname().sysname == 'Linux':
                os.system(f'xdg-open {output_file}')
            else:
                os.system(f'open {output_file}')
    except:
        print("Не удалось автоматически открыть файл.")

    return dot


def main():
    """Основная функция программы"""
    print("Программа минимизации ДКА с удалением ловушек")
    print("=" * 60)

    try:
        # Чтение исходного ДКА
        csv_file = input("Введите путь к CSV-файлу с описанием ДКА: ").strip()
        if not csv_file:
            csv_file = "dfa.csv"  # Использовать файл по умолчанию

        original_dfa = read_dfa_from_csv(csv_file)

        print(f"\nИсходный ДКА загружен из '{csv_file}':")
        print(f"  Состояния: {', '.join(sorted(original_dfa.states))}")
        print(f"  Алфавит: {', '.join(sorted(original_dfa.alphabet))}")
        print(f"  Начальное состояние: {original_dfa.start_state}")
        print(f"  Допускающие состояния: {', '.join(sorted(original_dfa.accept_states))}")

        # Находим ловушки
        trap_states = [state for state in original_dfa.states
                       if original_dfa.is_trap_state(state)]
        if trap_states:
            print(f"  Ловушки (будут удалены): {', '.join(sorted(trap_states))}")

        # Визуализация исходного ДКА
        print("\n" + "=" * 60)
        vis_choice = input("Визуализировать исходный ДКА? (да/нет): ").strip().lower()
        if vis_choice in ['да', 'д', 'yes', 'y', '']:
            visualize_dfa(original_dfa, title="Исходный ДКА", filename="original_dfa")

        # Выбор алгоритма минимизации
        print("\n" + "=" * 60)
        print("Выберите алгоритм минимизации:")
        print("1. Алгоритм таблицы различий")
        print("2. Алгоритм Хопкрофта")
        choice = input("Ваш выбор (1 или 2, Enter для 2): ").strip()

        if choice == '1':
            minimized_dfa = minimize_dfa_table(original_dfa)
            algo_name = "таблицы различий"
        else:
            minimized_dfa = minimize_dfa_hopcroft(original_dfa)
            algo_name = "Хопкрофта"

        print(f"\nМинимизация выполнена (алгоритм {algo_name}):")
        print(f"  Состояния до удаления ловушек: {', '.join(sorted(minimized_dfa.states))}")

        # Находим ловушки в минимизированном автомате
        trap_states_min = [state for state in minimized_dfa.states
                           if minimized_dfa.is_trap_state(state)]
        if trap_states_min:
            print(f"  Ловушки в минимизированном: {', '.join(sorted(trap_states_min))}")

        # Визуализация минимизированного ДКА БЕЗ ловушек
        print("\n" + "=" * 60)
        print("Визуализация минимизированного ДКА без ловушек...")
        minimized_useful = minimized_dfa.minimize_and_visualize(algo_name)

        print(f"\n  Состояния после удаления ловушек: {', '.join(sorted(minimized_useful.states))}")
        print(f"  Начальное состояние: {minimized_useful.start_state}")
        print(f"  Допускающие состояния: {', '.join(sorted(minimized_useful.accept_states))}")

        # Пошаговая обработка строки
        print("\n" + "=" * 60)
        test_str = input("Введите строку для тестирования (например, 'ab', Enter для 'ab'): ").strip()
        if not test_str:
            test_str = "ab"  # Значение по умолчанию

        print(f"\nТестирование строки '{test_str}':")

        # Обработка исходным автоматом
        try:
            result_orig = original_dfa.process_input(test_str)
            print(f"  Исходный ДКА: {'ПРИНЯТА' if result_orig else 'ОТВЕРГНУТА'}")
        except Exception as e:
            print(f"  Исходный ДКА: Ошибка - {e}")

        # Обработка минимизированным автоматом
        try:
            result_min = minimized_useful.process_input(test_str)
            print(f"  Минимизированный ДКА: {'ПРИНЯТА' if result_min else 'ОТВЕРГНУТА'}")
        except Exception as e:
            print(f"  Минимизированный ДКА: Ошибка - {e}")

        # Визуализация пути
        vis_path = input(f"\nВизуализировать путь обработки строки '{test_str}'? (да/нет): ").strip().lower()
        if vis_path in ['да', 'д', 'yes', 'y', '']:
            visualize_path(minimized_useful, test_str, filename="dfa_path")

        # Сохранение минимизированного ДКА в CSV
        print("\n" + "=" * 60)
        save_choice = input("Сохранить минимизированный ДКА в CSV-файл? (да/нет): ").strip().lower()

        if save_choice in ['да', 'д', 'yes', 'y']:
            output_file = input("Введите имя файла (Enter для 'minimized_dfa.csv'): ").strip()
            if not output_file:
                output_file = "minimized_dfa.csv"

            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                header = ['state'] + sorted(minimized_useful.alphabet) + ['accept']
                writer.writerow(header)

                for state in sorted(minimized_useful.states):
                    row = [state]
                    for symbol in sorted(minimized_useful.alphabet):
                        row.append(minimized_useful.transitions[state].get(symbol, ''))

                    if state in minimized_useful.accept_states:
                        row.append('*')
                    else:
                        row.append('')

                    writer.writerow(row)

            print(f"✓ Минимизированный ДКА сохранен в файл '{output_file}'")

    except FileNotFoundError:
        print(f"✗ Ошибка: Файл '{csv_file}' не найден.")
        print("Создайте файл dfa.csv со следующим содержимым:")
        print("state,a,b,accept")
        print("q0,q1,q2,")
        print("q1,q2,q3,")
        print("q2,q2,q2,")
        print("q3,q3,q3,*")
    except Exception as e:
        print(f"✗ Произошла ошибка: {e}")
        import traceback
        traceback.print_exc()


def minimize_dfa_table(dfa):
    """Минимизация ДКА с использованием алгоритма таблицы различий"""
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
    """Минимизация ДКА с использованием алгоритма Хопкрофта"""
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


if __name__ == "__main__":
    # Проверка наличия graphviz
    try:
        import graphviz

        main()
    except ImportError:
        print("Ошибка: Для работы визуализатора требуется установить graphviz")
