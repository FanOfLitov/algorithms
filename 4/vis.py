import graphviz
import os
from typing import Set, Dict, List
from collections import defaultdict


class AutomataVisualizer:
    """Класс для визуализации автоматов (НКА/ДКА)"""

    def __init__(self):
        self.graph_counter = 0

    def visualize_nfa(self, nfa, title="НКА", highlight_states=None, filename=None):
        """Визуализация недетерминированного конечного автомата"""
        dot = graphviz.Digraph(format='png')
        dot.attr(rankdir='LR', size='10,7')

        # Собираем все состояния
        all_states = self._collect_nfa_states(nfa.start)

        # Добавляем состояния
        for state in all_states:
            node_attrs = {}

            if state == nfa.start:
                # Начальное состояние
                node_attrs['style'] = 'filled'
                node_attrs['fillcolor'] = 'lightblue'

            if state.is_final:
                # Конечное состояние
                node_attrs['shape'] = 'doublecircle'
            else:
                node_attrs['shape'] = 'circle'

            if highlight_states and state in highlight_states:
                node_attrs['color'] = 'red'
                node_attrs['penwidth'] = '3'

            dot.node(str(state.id), label=f"q{state.id}", **node_attrs)

        # Добавляем начальную стрелку
        dot.node('start', shape='point')
        dot.edge('start', str(nfa.start.id))

        # Собираем и добавляем переходы
        transitions = self._collect_nfa_transitions(all_states)

        for (from_state, symbol), to_states in transitions.items():
            for to_state in to_states:
                edge_label = 'ε' if symbol == '' else symbol
                dot.edge(str(from_state.id), str(to_state.id), label=edge_label)

        # Добавляем заголовок
        dot.attr(label=title, labelloc='t', fontsize='16')

        # Сохраняем
        if not filename:
            filename = f"nfa_{self.graph_counter}"
            self.graph_counter += 1

        self._save_graph(dot, filename)

        return dot

    def visualize_dfa(self, dfa, title="ДКА", highlight_path=None, filename=None):
        """Визуализация детерминированного конечного автомата"""
        dot = graphviz.Digraph(format='png')
        dot.attr(rankdir='LR', size='10,7')

        # Добавляем состояния
        for state in sorted(dfa.states):
            node_attrs = {}

            if state == dfa.start_state:
                # Начальное состояние
                node_attrs['style'] = 'filled'
                node_attrs['fillcolor'] = 'lightblue'

            if state in dfa.accept_states:
                # Конечное состояние
                node_attrs['shape'] = 'doublecircle'
            else:
                node_attrs['shape'] = 'circle'

            dot.node(str(state), label=f"q{state}", **node_attrs)

        # Добавляем начальную стрелку
        dot.node('start', shape='point')
        dot.edge('start', str(dfa.start_state))

        # Добавляем переходы
        for from_state, transitions in dfa.transitions.items():
            for symbol, to_state in transitions.items():
                dot.edge(str(from_state), str(to_state), label=symbol)

        # Добавляем заголовок
        dot.attr(label=title, labelloc='t', fontsize='16')

        # Сохраняем
        if not filename:
            filename = f"dfa_{self.graph_counter}"
            self.graph_counter += 1

        self._save_graph(dot, filename)

        return dot

    def visualize_regex_processing(self, regex, input_string, interpreter, filename=None):
        """Визуализация всего процесса от регулярного выражения до ДКА"""
        # Шаг 1: Преобразование в обратную польскую запись
        postfix = interpreter.to_postfix(regex)

        # Шаг 2: Построение НКА
        nfa = interpreter.build_nfa_from_postfix(postfix)

        # Шаг 3: Преобразование в ДКА
        dfa = interpreter.nfa_to_dfa(nfa)

        # Шаг 4: Обработка входной строки
        result = dfa.process_input(input_string)

        # Создаем общий граф
        dot = graphviz.Digraph(format='png')
        dot.attr(rankdir='TB', size='12,8')

        with dot.subgraph(name='cluster_nfa') as c:
            c.attr(label='НКА из регулярного выражения', style='rounded', fontsize='14')
            nfa_dot = self._create_nfa_subgraph(nfa)
            c.subgraph(nfa_dot)

        with dot.subgraph(name='cluster_dfa') as c:
            c.attr(label='ДКА (после детерминизации)', style='rounded', fontsize='14')
            dfa_dot = self._create_dfa_subgraph(dfa, highlight_path=input_string)
            c.subgraph(dfa_dot)

        # Добавляем информацию о результате
        result_text = "✓ Строка ПРИНЯТА" if result else "✗ Строка ОТВЕРГНУТА"
        dot.attr(label=f"Регулярное выражение: {regex}\nВходная строка: '{input_string}'\nРезультат: {result_text}",
                 labelloc='t', fontsize='16')

        # Сохраняем
        if not filename:
            filename = f"regex_processing_{self.graph_counter}"
            self.graph_counter += 1

        self._save_graph(dot, filename)

        return dot, result

    def _collect_nfa_states(self, start_state, visited=None):
        """Сбор всех состояний НКА"""
        if visited is None:
            visited = set()

        if start_state in visited:
            return visited

        visited.add(start_state)

        # Рекурсивно обходим переходы
        for symbol, states in start_state.transitions.items():
            for state in states:
                self._collect_nfa_states(state, visited)

        # Рекурсивно обходим ε-переходы
        for state in start_state.epsilon_transitions:
            self._collect_nfa_states(state, visited)

        return visited

    def _collect_nfa_transitions(self, states):
        """Сбор всех переходов НКА"""
        transitions = defaultdict(list)

        for state in states:
            # Обычные переходы
            for symbol, to_states in state.transitions.items():
                for to_state in to_states:
                    transitions[(state, symbol)].append(to_state)

            # ε-переходы
            for to_state in state.epsilon_transitions:
                transitions[(state, '')].append(to_state)

        return transitions

    def _create_nfa_subgraph(self, nfa):
        """Создание подграфа для НКА"""
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR')

        all_states = self._collect_nfa_states(nfa.start)

        for state in all_states:
            if state == nfa.start:
                dot.node(str(state.id), f"q{state.id}", style='filled', fillcolor='lightblue')
            elif state.is_final:
                dot.node(str(state.id), f"q{state.id}", shape='doublecircle')
            else:
                dot.node(str(state.id), f"q{state.id}", shape='circle')

        transitions = self._collect_nfa_transitions(all_states)

        for (from_state, symbol), to_states in transitions.items():
            for to_state in to_states:
                label = 'ε' if symbol == '' else symbol
                dot.edge(str(from_state.id), str(to_state.id), label=label)

        return dot

    def _create_dfa_subgraph(self, dfa, highlight_path=None):
        """Создание подграфа для ДКА с выделением пути"""
        dot = graphviz.Digraph()
        dot.attr(rankdir='LR')

        # Симулируем путь, если задана строка
        path_states = []
        if highlight_path:
            current_state = dfa.start_state
            path_states.append(current_state)

            for symbol in highlight_path:
                if (current_state in dfa.transitions and
                        symbol in dfa.transitions[current_state]):
                    current_state = dfa.transitions[current_state][symbol]
                    path_states.append(current_state)
                else:
                    break

        for state in sorted(dfa.states):
            node_attrs = {}

            if state == dfa.start_state:
                node_attrs['style'] = 'filled'
                node_attrs['fillcolor'] = 'lightblue'

            if state in dfa.accept_states:
                node_attrs['shape'] = 'doublecircle'
            else:
                node_attrs['shape'] = 'circle'

            if state in path_states:
                node_attrs['color'] = 'red'
                node_attrs['penwidth'] = '2'

            dot.node(str(state), f"q{state}", **node_attrs)

        for from_state, transitions in dfa.transitions.items():
            for symbol, to_state in transitions.items():
                edge_attrs = {}

                # Выделяем переходы, которые входят в путь
                if (highlight_path and from_state in path_states and
                        to_state in path_states):
                    idx = path_states.index(from_state)
                    if idx + 1 < len(path_states) and path_states[idx + 1] == to_state:
                        edge_attrs['color'] = 'red'
                        edge_attrs['penwidth'] = '2'

                dot.edge(str(from_state), str(to_state), label=symbol, **edge_attrs)

        return dot

    def _save_graph(self, dot, filename):
        """Сохранение графа в файл"""
        output_dir = 'visualizations'
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, filename)
        dot.render(output_path, view=False, cleanup=True)
        print(f"✓ Граф сохранен как {output_path}.png")


def visualize_from_csv(csv_file):
    """Визуализация автоматов из CSV файла"""
    from main import read_test_cases_from_csv, RegexInterpreter

    visualizer = AutomataVisualizer()
    interpreter = RegexInterpreter()

    test_cases = read_test_cases_from_csv(csv_file)

    print(f"Загружено {len(test_cases)} тестовых случаев")

    for i, test_case in enumerate(test_cases, 1):
        regex = test_case.get('regex', '')
        test_string = test_case.get('test_string', '')

        if not regex:
            print(f"Тест {i}: Пропущен (нет регулярного выражения)")
            continue

        try:
            print(f"\nТест {i}: Визуализация '{regex}'")

            # Визуализируем процесс обработки
            if test_string:
                dot, result = visualizer.visualize_regex_processing(
                    regex, test_string, interpreter,
                    filename=f"test_{i}_{regex[:10]}"
                )
                print(f"  Результат: {'ПРИНЯТА' if result else 'ОТВЕРГНУТА'}")
            else:
                # Только НКА и ДКА
                postfix = interpreter.to_postfix(regex)
                nfa = interpreter.build_nfa_from_postfix(postfix)
                dfa = interpreter.nfa_to_dfa(nfa)

                visualizer.visualize_nfa(nfa, filename=f"test_{i}_nfa")
                visualizer.visualize_dfa(dfa, filename=f"test_{i}_dfa")
                print(f"  Созданы графы НКА и ДКА")

        except Exception as e:
            print(f"  Ошибка: {e}")


def interactive_visualization():
    """Интерактивная визуализация"""
    from main import RegexInterpreter

    visualizer = AutomataVisualizer()
    interpreter = RegexInterpreter()

    print("ВИЗУАЛИЗАТОР АВТОМАТОВ ДЛЯ РЕГУЛЯРНЫХ ВЫРАЖЕНИЙ")
    print("=" * 60)

    while True:
        print("\n" + "=" * 60)
        print("Меню:")
        print("1. Визуализировать регулярное выражение")
        print("2. Визуализировать с тестовой строкой")
        print("3. Загрузить из CSV файла")
        print("4. Выход")

        choice = input("\nВыберите действие (1-4): ").strip()

        if choice == '1':
            regex = input("Введите регулярное выражение: ").strip()

            try:
                postfix = interpreter.to_postfix(regex)
                nfa = interpreter.build_nfa_from_postfix(postfix)
                dfa = interpreter.nfa_to_dfa(nfa)

                visualizer.visualize_nfa(nfa, title=f"НКА для '{regex}'")
                visualizer.visualize_dfa(dfa, title=f"ДКА для '{regex}'")

                print(f"✓ Созданы графы для выражения: {regex}")

            except Exception as e:
                print(f"✗ Ошибка: {e}")

        elif choice == '2':
            regex = input("Введите регулярное выражение: ").strip()
            test_string = input("Введите тестовую строку: ").strip()

            try:
                dot, result = visualizer.visualize_regex_processing(
                    regex, test_string, interpreter,
                    filename=f"processing_{regex[:10]}_{test_string[:10]}"
                )

                print(f"✓ Результат: строка '{test_string}' {'ПРИНЯТА' if result else 'ОТВЕРГНУТА'}")

            except Exception as e:
                print(f"✗ Ошибка: {e}")

        elif choice == '3':
            csv_file = input("Введите путь к CSV файлу: ").strip()

            if os.path.exists(csv_file):
                visualize_from_csv(csv_file)
            else:
                print(f"✗ Файл {csv_file} не найден!")

        elif choice == '4':
            print("Выход из программы.")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == '__main__':
    interactive_visualization()