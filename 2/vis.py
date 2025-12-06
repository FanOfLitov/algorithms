import csv
import graphviz
from collections import defaultdict
from main import NFA, read_nfa_from_csv


class NFAGraphVisualizer:
    def __init__(self, nfa):

        self.nfa = nfa
        self.dot = graphviz.Digraph(format='png')
        self.dot.attr(rankdir='LR')  # Ориентация слева направо

    def draw_nfa(self, highlight_path=None):

        # Настройка стилей
        self.dot.attr('node', shape='circle')

        # Добавление состояний
        for state in sorted(self.nfa.states):
            # Определяем форму состояния
            if state == self.nfa.start_state:
                # Начальное состояние
                self.dot.node(state, shape='circle', style='bold')
                # Добавляем невидимый узел для стрелки к начальному состоянию
                self.dot.node(f'start_{state}', shape='point', style='invis')
                self.dot.edge(f'start_{state}', state)
            elif state in self.nfa.accept_states:
                # Допускающее состояние
                self.dot.node(state, shape='doublecircle')
            else:
                # Обычное состояние
                self.dot.node(state, shape='circle')

            # Выделение пути, если задан
            if highlight_path and state in highlight_path:
                self.dot.node(state, fillcolor='lightblue', style='filled')

        # Добавление переходов
        for from_state, transitions in self.nfa.transitions.items():
            for symbol, to_states in transitions.items():
                for to_state in to_states:
                    # Настройка метки перехода
                    label = symbol if symbol != 'ε' else 'ε'
                    self.dot.edge(from_state, to_state, label=label)

        # Добавление заголовка
        self.dot.attr(label='Недетерминированный конечный автомат', labelloc='t', fontsize='16')

        return self.dot

    def visualize_trace(self, input_string):
        """
        Визуализирует прохождение автомата по входной строке

        Возвращает список графов для каждого шага
        """
        traces = []
        current_states = self.nfa.epsilon_closure({self.nfa.start_state})
        step = 0

        # Шаг 0: начальное состояние
        dot_step = graphviz.Digraph(format='png')
        dot_step.attr(rankdir='LR',
                      label=f'Шаг {step}: Начальное состояние\nАктивные состояния: {sorted(current_states)}')
        self._add_states_to_graph(dot_step, current_states, step)
        traces.append(dot_step)

        # Обрабатываем каждый символ
        for symbol in input_string:
            step += 1
            next_states = set()

            # Для каждого текущего состояния находим переходы
            for state in current_states:
                if symbol in self.nfa.transitions[state]:
                    next_states.update(self.nfa.transitions[state][symbol])

            # Вычисляем ε-замыкание
            current_states = self.nfa.epsilon_closure(next_states)

            # Создаем граф для текущего шага
            dot_step = graphviz.Digraph(format='png')
            dot_step.attr(rankdir='LR',
                          label=f'Шаг {step}: Символ "{symbol}"\nАктивные состояния: {sorted(current_states)}')
            self._add_states_to_graph(dot_step, current_states, step)
            traces.append(dot_step)

            if not current_states:
                break

        return traces

    def _add_states_to_graph(self, dot, active_states, step):
        """Добавляет состояния на граф с подсветкой активных"""
        for state in sorted(self.nfa.states):
            if state in active_states:
                # Активное состояние
                if state in self.nfa.accept_states:
                    dot.node(f'{state}_{step}', label=state, shape='doublecircle',
                             fillcolor='lightgreen', style='filled', fontsize='12')
                else:
                    dot.node(f'{state}_{step}', label=state, shape='circle',
                             fillcolor='lightblue', style='filled', fontsize='12')
            else:
                # Неактивное состояние
                if state in self.nfa.accept_states:
                    dot.node(f'{state}_{step}', label=state, shape='doublecircle',
                             fillcolor='white', style='filled', fontsize='10')
                else:
                    dot.node(f'{state}_{step}', label=state, shape='circle',
                             fillcolor='white', style='filled', fontsize='10')


def visualize_nfa_from_csv(csv_file, input_string=None):
    """
    Основная функция визуализации

    Параметры:
    - csv_file: путь к CSV-файлу с описанием НКА
    - input_string: входная строка для трассировки (опционально)
    """
    # Чтение НКА из CSV
    nfa = read_nfa_from_csv(csv_file)

    # Создание визуализатора
    visualizer = NFAGraphVisualizer(nfa)

    # Визуализация самого НКА
    print("Создание графа НКА...")
    dot_nfa = visualizer.draw_nfa()
    dot_nfa.render('nfa_graph', view=True, cleanup=True)
    print("Граф НКА сохранен в nfa_graph.png")

    # Визуализация трассировки, если задана входная строка
    if input_string:
        print(f"\nТрассировка для строки '{input_string}':")
        traces = visualizer.visualize_trace(input_string)

        # Проверка результата
        result = nfa.process_input(input_string)
        status = "ПРИНЯТА" if result else "ОТВЕРГНУТА"
        print(f"Результат: цепочка {status}")

        # Сохранение каждого шага трассировки
        for i, trace in enumerate(traces):
            filename = f'nfa_trace_step_{i}'
            trace.render(filename, view=(i == len(traces) - 1), cleanup=True)
            print(f"  Шаг {i} сохранен в {filename}.png")

        # Создание общего графа с трассировкой
        print("\nСоздание общего графа с трассировкой...")
        active_states = set()
        current_states = nfa.epsilon_closure({nfa.start_state})
        active_states.update(current_states)

        for symbol in input_string:
            next_states = set()
            for state in current_states:
                if symbol in nfa.transitions[state]:
                    next_states.update(nfa.transitions[state][symbol])
            current_states = nfa.epsilon_closure(next_states)
            active_states.update(current_states)

        dot_trace = visualizer.draw_nfa(highlight_path=active_states)
        dot_trace.attr(label=f'НКА с трассировкой для строки "{input_string}"\nЦепочка {status}',
                       labelloc='t', fontsize='14')
        dot_trace.render('nfa_trace', view=True, cleanup=True)
        print("Граф трассировки сохранен в nfa_trace.png")


def interactive_visualization():
    """Интерактивный режим визуализации"""
    print("Визуализатор НКА")
    print("=" * 50)

    csv_file = input("Введите путь к CSV-файлу с описанием НКА: ").strip()

    try:
        nfa = read_nfa_from_csv(csv_file)
        visualizer = NFAGraphVisualizer(nfa)

        # Визуализация НКА
        print("\nСоздание графа НКА...")
        dot_nfa = visualizer.draw_nfa()
        dot_nfa.render('nfa_graph', view=True, cleanup=True)
        print("Граф НКА сохранен в nfa_graph.png")

        # Трассировка
        print("\n" + "=" * 50)
        print("Трассировка цепочек (пустая строка для выхода):")

        while True:
            input_string = input("\nВведите цепочку для трассировки: ").strip()

            if not input_string:
                print("Завершение работы.")
                break

            try:
                # Проверка символов
                for symbol in input_string:
                    if symbol not in nfa.alphabet and symbol != 'ε':
                        raise ValueError(f"Символ '{symbol}' не найден в алфавите")

                # Визуализация трассировки
                traces = visualizer.visualize_trace(input_string)

                # Проверка результата
                result = nfa.process_input(input_string)
                status = "ПРИНЯТА" if result else "ОТВЕРГНУТА"
                print(f"Результат: цепочка {status}")

                # Сохранение шагов трассировки
                for i, trace in enumerate(traces):
                    filename = f'nfa_trace_{input_string}_step_{i}'
                    trace.render(filename, view=False, cleanup=True)
                    print(f"  Шаг {i} сохранен в {filename}.png")

                # Создание общего графа с трассировкой
                active_states = set()
                current_states = nfa.epsilon_closure({nfa.start_state})
                active_states.update(current_states)

                for symbol in input_string:
                    next_states = set()
                    for state in current_states:
                        if symbol in nfa.transitions[state]:
                            next_states.update(nfa.transitions[state][symbol])
                    current_states = nfa.epsilon_closure(next_states)
                    active_states.update(current_states)

                dot_trace = visualizer.draw_nfa(highlight_path=active_states)
                dot_trace.attr(label=f'НКА с трассировкой для "{input_string}"\nЦепочка {status}',
                               labelloc='t', fontsize='14')
                dot_trace.render(f'nfa_trace_{input_string}', view=True, cleanup=True)
                print(f"Граф трассировки сохранен в nfa_trace_{input_string}.png")

            except ValueError as e:
                print(f"Ошибка: {e}")

    except FileNotFoundError:
        print(f"Ошибка: Файл '{csv_file}' не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    # Пример использования:
    # 1. Визуализация НКА из файла с трассировкой
    # visualize_nfa_from_csv('nfa1.csv', 'ab')

    # 2. Интерактивный режим
    interactive_visualization()