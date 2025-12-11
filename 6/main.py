import csv
import sys
import json
from collections import defaultdict
from typing import List, Dict, Tuple, Set, Optional
import graphviz
import matplotlib.pyplot as plt
import networkx as nx
from IPython.display import display, HTML


class PushdownAutomaton:
    """Класс для имитации работы магазинного автомата"""

    def __init__(self):
        self.states: Set[str] = set()
        self.input_alphabet: Set[str] = set()
        self.stack_alphabet: Set[str] = set()
        self.transitions: Dict[Tuple[str, str, str], List[Tuple[str, str]]] = defaultdict(list)
        self.start_state: str = ""
        self.start_stack_symbol: str = ""
        self.accepting_states: Set[str] = set()
        self.accept_by_final_state: bool = True
        self.accept_by_empty_stack: bool = False
        self.transition_history: List[Dict] = []

    def load_from_csv(self, csv_file: str) -> None:
        """
        Загрузка описания автомата из CSV файла

        Формат CSV:
        current_state,input_symbol,stack_top,new_state,stack_push
        """
        self.transitions.clear()
        self.states.clear()
        self.input_alphabet.clear()
        self.stack_alphabet.clear()

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                current_state = row['current_state'].strip()
                input_symbol = row['input_symbol'].strip()
                stack_top = row['stack_top'].strip()
                new_state = row['new_state'].strip()
                stack_push = row['stack_push'].strip()

                # Добавляем состояния в алфавиты
                self.states.update([current_state, new_state])

                # Добавляем символы в алфавиты
                if input_symbol and input_symbol != 'ε':
                    self.input_alphabet.add(input_symbol)

                if stack_top and stack_top != 'ε':
                    self.stack_alphabet.add(stack_top)

                # Обработка символов для помещения в стек
                if stack_push != 'ε':
                    for symbol in stack_push:
                        if symbol != 'ε':
                            self.stack_alphabet.add(symbol)

                # Добавляем переход
                key = (current_state, input_symbol, stack_top)
                self.transitions[key].append((new_state, stack_push))

    def set_start_configuration(self, start_state: str, start_stack_symbol: str) -> None:
        """Установка начальной конфигурации"""
        self.start_state = start_state
        self.start_stack_symbol = start_stack_symbol
        self.stack_alphabet.add(start_stack_symbol)

    def set_accepting_states(self, states: List[str]) -> None:
        """Установка допускающих состояний"""
        self.accepting_states = set(states)

    def set_acceptance_mode(self, by_final_state: bool = True, by_empty_stack: bool = False) -> None:
        """Установка режима допуска"""
        self.accept_by_final_state = by_final_state
        self.accept_by_empty_stack = by_empty_stack

    def validate_configuration(self) -> List[str]:
        """Проверка корректности конфигурации автомата"""
        errors = []

        if not self.start_state:
            errors.append("Не задано начальное состояние")

        if not self.start_stack_symbol:
            errors.append("Не задан начальный символ стека")

        if self.accept_by_final_state and not self.accepting_states:
            errors.append("Режим допуска по конечному состоянию выбран, но нет допускающих состояний")

        if self.start_state and self.start_state not in self.states:
            errors.append(f"Начальное состояние '{self.start_state}' не найдено в множестве состояний")

        if self.start_stack_symbol and self.start_stack_symbol not in self.stack_alphabet:
            errors.append(f"Начальный символ стека '{self.start_stack_symbol}' не найден в стековом алфавите")

        return errors

    def simulate(self, input_string: str, max_steps: int = 10000, verbose: bool = False) -> Tuple[bool, List[str]]:
        """
        Имитация работы автомата на входной цепочке

        Возвращает:
        - accept: допускается ли цепочка
        - history: история работы автомата
        """
        self.transition_history = []

        # Проверяем входные символы
        for symbol in input_string:
            if symbol not in self.input_alphabet and symbol != 'ε':
                return False, [f"Ошибка: символ '{symbol}' не найден во входном алфавите"]

        # Инициализация
        configurations = [{
            'state': self.start_state,
            'stack': [self.start_stack_symbol],
            'position': 0,
            'history': [f"Начало: состояние={self.start_state}, стек=['{self.start_stack_symbol}']"],
            'path': []
        }]

        step = 0
        visited = set()

        while configurations and step < max_steps:
            step += 1
            next_configurations = []

            for config in configurations:
                state = config['state']
                stack = config['stack'].copy()
                position = config['position']
                history = config['history'].copy()
                path = config['path'].copy()

                # Проверяем, была ли уже такая конфигурация
                config_key = (state, tuple(stack), position)
                if config_key in visited:
                    continue
                visited.add(config_key)

                # Проверка условия допуска
                if self._check_acceptance(state, stack, position, input_string):
                    history.append("✓ Цепочка допускается")
                    self.transition_history = path
                    return True, history

                # Получаем текущий символ (может быть ε)
                current_input = input_string[position] if position < len(input_string) else None

                # Возможные переходы
                possible_transitions = []

                # 1. Переходы по входному символу
                if current_input is not None:
                    # Проверяем переходы с текущим символом
                    stack_top = stack[-1] if stack else 'ε'
                    key = (state, current_input, stack_top)
                    if key in self.transitions:
                        for new_state, stack_push in self.transitions[key]:
                            possible_transitions.append((
                                new_state, stack_push, current_input, position + 1
                            ))

                    # Проверяем переходы с ε на стеке
                    key_eps_stack = (state, current_input, 'ε')
                    if key_eps_stack in self.transitions and not stack:
                        for new_state, stack_push in self.transitions[key_eps_stack]:
                            possible_transitions.append((
                                new_state, stack_push, current_input, position + 1
                            ))

                # 2. ε-переходы (без чтения входного символа)
                # С обычным символом на стеке
                stack_top = stack[-1] if stack else 'ε'
                key_eps_input = (state, 'ε', stack_top)
                if key_eps_input in self.transitions:
                    for new_state, stack_push in self.transitions[key_eps_input]:
                        possible_transitions.append((
                            new_state, stack_push, 'ε', position
                        ))

                # С ε на стеке
                if not stack:
                    key_eps_both = (state, 'ε', 'ε')
                    if key_eps_both in self.transitions:
                        for new_state, stack_push in self.transitions[key_eps_both]:
                            possible_transitions.append((
                                new_state, stack_push, 'ε', position
                            ))

                # Применяем переходы
                for new_state, stack_push, used_symbol, new_position in possible_transitions:
                    new_stack = stack.copy()

                    # Удаляем верхний символ стека (если не ε)
                    if stack and stack_top != 'ε':
                        new_stack.pop()
                    elif not stack and stack_top == 'ε':
                        # Стек пустой и переход по ε
                        pass

                    # Добавляем новые символы в стек
                    if stack_push != 'ε':
                        for symbol in reversed(stack_push):
                            new_stack.append(symbol)

                    # Создаем новую конфигурацию
                    used_symbol_str = f"'{used_symbol}'" if used_symbol != 'ε' else 'ε'
                    history_entry = (f"Шаг {step}: состояние={state}->{new_state}, "
                                     f"символ={used_symbol_str}, стек={stack}->{new_stack}")

                    transition_record = {
                        'step': step,
                        'from_state': state,
                        'to_state': new_state,
                        'input': used_symbol,
                        'stack_top': stack_top,
                        'stack_push': stack_push,
                        'stack_before': stack.copy(),
                        'stack_after': new_stack.copy()
                    }

                    new_config = {
                        'state': new_state,
                        'stack': new_stack,
                        'position': new_position,
                        'history': history + [history_entry],
                        'path': path + [transition_record]
                    }

                    next_configurations.append(new_config)

            configurations = next_configurations

        # Если не нашли допускающую конфигурацию
        if step >= max_steps:
            return False, [f"Превышено максимальное количество шагов ({max_steps})"]

        return False, ["Цепочка не допускается"]

    def _check_acceptance(self, state: str, stack: List[str], position: int, input_string: str) -> bool:
        """Проверка условий допуска"""
        input_consumed = position == len(input_string)

        if self.accept_by_final_state and self.accept_by_empty_stack:
            # Допуск по конечному состоянию И пустому стеку
            return (input_consumed and
                    state in self.accepting_states and
                    len(stack) == 0)
        elif self.accept_by_final_state:
            # Допуск только по конечному состоянию
            return input_consumed and state in self.accepting_states
        elif self.accept_by_empty_stack:
            # Допуск только по пустому стеку
            return input_consumed and len(stack) == 0
        else:
            return False

    def visualize_transitions(self, output_file: str = 'pda_graph'):
        """
        Визуализация графа переходов автомата
        """
        dot = graphviz.Digraph(comment='Pushdown Automaton', format='png')

        # Настройка стилей
        dot.attr(rankdir='LR', size='10,10')

        # Добавление состояний
        for state in self.states:
            if state == self.start_state:
                # Начальное состояние
                dot.node(state, state, shape='circle', style='bold', color='green')
            elif state in self.accepting_states:
                # Допускающее состояние
                dot.node(state, state, shape='doublecircle', color='blue')
            else:
                # Обычное состояние
                dot.node(state, state, shape='circle')

        # Добавление переходов
        for (from_state, input_symbol, stack_top), transitions in self.transitions.items():
            for to_state, stack_push in transitions:
                # Форматирование метки перехода
                label = f"{input_symbol}, {stack_top} → {stack_push}"

                # Разные цвета для разных типов переходов
                edge_attrs = {}
                if input_symbol == 'ε':
                    edge_attrs['color'] = 'red'
                    edge_attrs['style'] = 'dashed'
                elif stack_push == 'ε':
                    edge_attrs['color'] = 'orange'
                else:
                    edge_attrs['color'] = 'black'

                dot.edge(from_state, to_state, label=label, **edge_attrs)

        # Сохранение и отображение
        dot.render(output_file, view=True, cleanup=True)
        print(f"Граф переходов сохранен в {output_file}.png")

        return dot

    def visualize_path(self, input_string: str, output_file: str = 'pda_path'):
        """
        Визуализация пути для конкретной входной цепочки
        """
        # Запускаем симуляцию для получения истории
        accept, history = self.simulate(input_string)

        if not accept:
            print(f"Цепочка '{input_string}' не допускается, невозможно визуализировать путь")
            return

        dot = graphviz.Digraph(comment='PDA Execution Path', format='png')
        dot.attr(rankdir='LR', size='12,8')

        # Создаем узлы для каждого шага
        steps = [f"Нач: {self.start_state}, стек: [{self.start_stack_symbol}]"]

        for i, transition in enumerate(self.transition_history):
            step_desc = f"Шаг {i + 1}: {transition['from_state']}→{transition['to_state']}\n"
            step_desc += f"Вход: {transition['input']}\n"
            step_desc += f"Стек: {transition['stack_before']}→{transition['stack_after']}"
            steps.append(step_desc)

        # Добавляем финальный шаг
        final_state = self.transition_history[-1]['to_state'] if self.transition_history else self.start_state
        steps.append(f"Конец: {final_state}\nЦепочка допущена!")

        # Создаем узлы
        for i, step in enumerate(steps):
            color = 'green' if i == 0 else 'lightblue' if i < len(steps) - 1 else 'gold'
            dot.node(f'step{i}', step, shape='rectangle', style='filled',
                     color=color, fontsize='10')

        # Создаем ребра
        for i in range(len(steps) - 1):
            dot.edge(f'step{i}', f'step{i + 1}', arrowhead='normal')

        # Сохранение
        dot.render(output_file, view=True, cleanup=True)
        print(f"Путь выполнения сохранен в {output_file}.png")

        return dot

    def print_detailed_info(self):
        """Вывод подробной информации об автомате и переходах"""
        print("=" * 80)
        print("ПОДРОБНАЯ ИНФОРМАЦИЯ О МАГАЗИННОМ АВТОМАТЕ")
        print("=" * 80)

        print(f"Состояния ({len(self.states)}): {', '.join(sorted(self.states))}")
        print(f"Входной алфавит ({len(self.input_alphabet)}): {', '.join(sorted(self.input_alphabet))}")
        print(f"Стековый алфавит ({len(self.stack_alphabet)}): {', '.join(sorted(self.stack_alphabet))}")
        print(f"Начальное состояние: {self.start_state}")
        print(f"Начальный символ стека: {self.start_stack_symbol}")
        print(f"Допускающие состояния: {', '.join(sorted(self.accepting_states))}")

        mode = []
        if self.accept_by_final_state:
            mode.append("по конечному состоянию")
        if self.accept_by_empty_stack:
            mode.append("по пустому стеку")
        print(f"Режим допуска: {' + '.join(mode) if mode else 'не задан'}")

        print("\n" + "=" * 80)
        print("ПЕРЕХОДЫ:")
        print("=" * 80)

        transitions_count = 0
        for (from_state, input_symbol, stack_top), to_list in self.transitions.items():
            for to_state, stack_push in to_list:
                transitions_count += 1
                print(f"δ({from_state}, {input_symbol}, {stack_top}) = ({to_state}, {stack_push})")

        print(f"\nВсего переходов: {transitions_count}")
        print("=" * 80)

    def export_to_json(self, filename: str = 'pda_description.json'):
        """Экспорт описания автомата в JSON файл"""
        data = {
            'states': list(self.states),
            'input_alphabet': list(self.input_alphabet),
            'stack_alphabet': list(self.stack_alphabet),
            'start_state': self.start_state,
            'start_stack_symbol': self.start_stack_symbol,
            'accepting_states': list(self.accepting_states),
            'accept_by_final_state': self.accept_by_final_state,
            'accept_by_empty_stack': self.accept_by_empty_stack,
            'transitions': []
        }

        for (from_state, input_symbol, stack_top), to_list in self.transitions.items():
            for to_state, stack_push in to_list:
                data['transitions'].append({
                    'from': from_state,
                    'input': input_symbol,
                    'stack_top': stack_top,
                    'to': to_state,
                    'stack_push': stack_push
                })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Описание автомата экспортировано в {filename}")

    def print_info(self) -> None:
        """Вывод информации об автомате"""
        print("=" * 60)
        print("ИНФОРМАЦИЯ О МАГАЗИННОМ АВТОМАТЕ")
        print("=" * 60)
        print(f"Состояния: {', '.join(sorted(self.states))}")
        print(f"Входной алфавит: {', '.join(sorted(self.input_alphabet))}")
        print(f"Стековый алфавит: {', '.join(sorted(self.stack_alphabet))}")
        print(f"Начальное состояние: {self.start_state}")
        print(f"Начальный символ стека: {self.start_stack_symbol}")
        print(f"Допускающие состояния: {', '.join(sorted(self.accepting_states))}")
        print(f"Режим допуска: {'по конечному состоянию' if self.accept_by_final_state else ''} "
              f"{'и' if self.accept_by_final_state and self.accept_by_empty_stack else ''} "
              f"{'по пустому стеку' if self.accept_by_empty_stack else ''}")
        print(f"Количество переходов: {sum(len(v) for v in self.transitions.values())}")
        print("=" * 60)


def load_pda_from_config(config_file: str) -> PushdownAutomaton:
    """
    Загрузка автомата из конфигурационного файла

    Формат конфигурации:
    csv_file=automaton.csv
    start_state=q0
    start_stack_symbol=Z
    accepting_states=q2
    acceptance_mode=final_state  # или empty_stack, или both
    """
    pda = PushdownAutomaton()

    config = {}
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()

    # Загружаем автомат из CSV
    pda.load_from_csv(config['csv_file'])

    # Устанавливаем начальную конфигурацию
    pda.set_start_configuration(config['start_state'], config['start_stack_symbol'])

    # Устанавливаем допускающие состояния
    accepting_states = config.get('accepting_states', '').split(',')
    pda.set_accepting_states([s.strip() for s in accepting_states if s.strip()])

    # Устанавливаем режим допуска
    acceptance_mode = config.get('acceptance_mode', 'final_state')
    if acceptance_mode == 'final_state':
        pda.set_acceptance_mode(by_final_state=True, by_empty_stack=False)
    elif acceptance_mode == 'empty_stack':
        pda.set_acceptance_mode(by_final_state=False, by_empty_stack=True)
    elif acceptance_mode == 'both':
        pda.set_acceptance_mode(by_final_state=True, by_empty_stack=True)

    return pda


def interactive_mode():
    """Интерактивный режим работы программы"""
    print("МАГАЗИННЫЙ АВТОМАТ - ИНТЕРАКТИВНЫЙ РЕЖИМ")
    print("=" * 60)

    # Запрос файла с автоматом
    csv_file = input("Введите путь к CSV файлу с описанием автомата: ").strip()

    # Создание автомата
    pda = PushdownAutomaton()

    try:
        pda.load_from_csv(csv_file)
    except FileNotFoundError:
        print(f"Ошибка: файл '{csv_file}' не найден")
        return
    except Exception as e:
        print(f"Ошибка при загрузке CSV: {e}")
        return

    # Запрос начальной конфигурации
    start_state = input(f"Введите начальное состояние (доступные: {', '.join(sorted(pda.states))}): ").strip()
    start_stack = input(f"Введите начальный символ стека: ").strip()
    pda.set_start_configuration(start_state, start_stack)

    # Запрос допускающих состояний
    accepting = input(
        f"Введите допускающие состояния через запятую (доступные: {', '.join(sorted(pda.states))}): ").strip()
    pda.set_accepting_states([s.strip() for s in accepting.split(',')])

    # Запрос режима допуска
    print("\nВыберите режим допуска:")
    print("1. По конечному состоянию")
    print("2. По пустому стеку")
    print("3. По конечному состоянию и пустому стеку")
    mode_choice = input("Ваш выбор (1-3): ").strip()

    if mode_choice == '1':
        pda.set_acceptance_mode(by_final_state=True, by_empty_stack=False)
    elif mode_choice == '2':
        pda.set_acceptance_mode(by_final_state=False, by_empty_stack=True)
    elif mode_choice == '3':
        pda.set_acceptance_mode(by_final_state=True, by_empty_stack=True)
    else:
        print("Используется режим по умолчанию (по конечному состоянию)")

    # Проверка конфигурации
    errors = pda.validate_configuration()
    if errors:
        print("\nОшибки в конфигурации:")
        for error in errors:
            print(f"  - {error}")
        return

    # Вывод информации об автомате
    pda.print_detailed_info()

    # Визуализация графа переходов
    viz = input("\nВизуализировать граф переходов? (y/n): ").strip().lower()
    if viz == 'y':
        pda.visualize_transitions()

    # Экспорт в JSON
    export = input("\nЭкспортировать описание автомата в JSON? (y/n): ").strip().lower()
    if export == 'y':
        pda.export_to_json()

    # Обработка цепочек
    print("\n" + "=" * 60)
    print("ВВОД ЦЕПОЧЕК (для выхода введите 'exit' или 'quit')")
    print("=" * 60)

    while True:
        chain = input("\nВведите цепочку для проверки: ").strip()

        if chain.lower() in ['exit', 'quit', 'выход']:
            print("Завершение работы...")
            break

        if not chain:
            print("Введена пустая цепочка")
            chain = ""

        accept, history = pda.simulate(chain, verbose=False)

        print(f"\nРезультат: {'✓ ДОПУСКАЕТСЯ' if accept else '✗ НЕ ДОПУСКАЕТСЯ'}")

        # Вывод подробной информации по запросу
        details = input("Показать подробную информацию о выполнении? (y/n): ").strip().lower()
        if details == 'y':
            print("\nИстория работы:")
            for i, entry in enumerate(history):
                print(f"  {entry}")
                if i >= 20:  # Ограничиваем вывод
                    print(f"  ... и еще {len(history) - i} шагов")
                    break

        # Визуализация пути
        if accept:
            viz_path = input("Визуализировать путь выполнения? (y/n): ").strip().lower()
            if viz_path == 'y':
                pda.visualize_path(chain)


def batch_mode(config_file: str, chains_file: str):
    """Пакетный режим работы программы"""
    print(f"Загрузка автомата из конфигурации: {config_file}")

    try:
        pda = load_pda_from_config(config_file)
    except Exception as e:
        print(f"Ошибка при загрузке конфигурации: {e}")
        return

    # Проверка конфигурации
    errors = pda.validate_configuration()
    if errors:
        print("Ошибки в конфигурации:")
        for error in errors:
            print(f"  - {error}")
        return

    pda.print_detailed_info()

    # Визуализация графа
    viz = input("\nВизуализировать граф переходов? (y/n): ").strip().lower()
    if viz == 'y':
        pda.visualize_transitions()

    # Чтение цепочек из файла
    print(f"\nЧтение цепочек из файла: {chains_file}")
    print("=" * 60)

    try:
        with open(chains_file, 'r', encoding='utf-8') as f:
            chains = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Ошибка: файл '{chains_file}' не найден")
        return

    # Проверка цепочек
    results = []
    for chain in chains:
        accept, _ = pda.simulate(chain, verbose=False)
        results.append((chain, accept))

        status = "✓ ДОПУСКАЕТСЯ" if accept else "✗ НЕ ДОПУСКАЕТСЯ"
        print(f"{chain:20} -> {status}")

    # Сохранение результатов
    output_file = "pda_results.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Результаты проверки цепочек\n")
        f.write("=" * 60 + "\n")
        f.write(f"Автомат из: {config_file}\n")
        f.write(f"Цепочки из: {chains_file}\n")
        f.write("=" * 60 + "\n\n")

        for chain, accept in results:
            status = "ДОПУСКАЕТСЯ" if accept else "НЕ ДОПУСКАЕТСЯ"
            f.write(f"{chain:20} -> {status}\n")

        # Статистика
        accepted = sum(1 for _, accept in results if accept)
        f.write(f"\nСтатистика:\n")
        f.write(f"Всего цепочек: {len(results)}\n")
        f.write(f"Допущено: {accepted}\n")
        f.write(f"Отвергнуто: {len(results) - accepted}\n")

    print(f"\nРезультаты сохранены в файл: {output_file}")


def main():
    """Основная функция программы"""
    print("МАГАЗИННЫЙ АВТОМАТ (PDA) SIMULATOR")
    print("=" * 60)
    print("Режимы работы:")
    print("1. Интерактивный режим")
    print("2. Пакетный режим (с конфигурационным файлом)")
    print("3. Пример использования")
    print("4. Запуск тестов")

    choice = input("\nВыберите режим (1-4): ").strip()

    if choice == '1':
        interactive_mode()
    elif choice == '2':
        config_file = input("Введите путь к конфигурационному файлу: ").strip()
        chains_file = input("Введите путь к файлу с цепочками: ").strip()
        batch_mode(config_file, chains_file)
    elif choice == '3':
        run_example()
    elif choice == '4':
        run_tests()
    else:
        print("Неверный выбор. Запуск интерактивного режима...")
        interactive_mode()


def run_example():
    """Запуск примера работы программы"""
    print("\n" + "=" * 80)
    print("ПРИМЕР: Магазинный автомат для языка {a^n b^n | n >= 0}")
    print("=" * 80)

    # Создание примера CSV файла
    example_csv = """current_state,input_symbol,stack_top,new_state,stack_push
q0,a,Z,q0,AZ
q0,a,A,q0,AA
q0,b,A,q1,ε
q1,b,A,q1,ε
q1,ε,Z,q2,Z"""

    # Сохранение примера CSV
    with open('example_pda.csv', 'w', encoding='utf-8') as f:
        f.write(example_csv)

    print("Создан пример CSV файла: example_pda.csv")

    # Создание конфигурационного файла
    example_config = """csv_file=example_pda.csv
start_state=q0
start_stack_symbol=Z
accepting_states=q2
acceptance_mode=final_state"""

    with open('example_config.txt', 'w', encoding='utf-8') as f:
        f.write(example_config)

    print("Создан пример конфигурационного файла: example_config.txt")

    # Создание файла с цепочками
    example_chains = """aaabbb
aabb
ab
aabbb
aaaabb
ε"""

    with open('example_chains.txt', 'w', encoding='utf-8') as f:
        f.write(example_chains)

    print("Создан пример файла с цепочками: example_chains.txt")

    # Запуск пакетного режима
    print("\n" + "=" * 80)
    print("ЗАПУСК ПРОВЕРКИ ПРИМЕРА")
    print("=" * 80)

    try:
        pda = load_pda_from_config('example_config.txt')
        pda.print_detailed_info()

        # Визуализация графа
        print("\nВизуализация графа переходов...")
        pda.visualize_transitions('example_pda_graph')

        with open('example_chains.txt', 'r', encoding='utf-8') as f:
            chains = [line.strip() for line in f if line.strip()]

        print("\nРезультаты проверки цепочек:")
        for chain in chains:
            accept, _ = pda.simulate(chain, verbose=False)
            status = "✓ ДОПУСКАЕТСЯ" if accept else "✗ НЕ ДОПУСКАЕТСЯ"
            chain_display = chain if chain else "ε (пустая)"
            print(f"  {chain_display:20} -> {status}")

            # Визуализация пути для допускаемых цепочек
            if accept and chain:
                pda.visualize_path(chain, f'example_path_{chain}')

        # Экспорт в JSON
        pda.export_to_json('example_pda.json')
        print(f"\nОписание автомата экспортировано в example_pda.json")

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()


def run_tests():
    """Запуск тестов"""
    import subprocess
    import sys

    print("\n" + "=" * 80)
    print("ЗАПУСК ТЕСТОВ")
    print("=" * 80)

    result = subprocess.run([sys.executable, '-m', 'pytest', 'test.py', '-v'])

    if result.returncode == 0:
        print("\n Все тесты пройдены успешно!")
    else:
        print("\n Некоторые тесты не пройдены.")


if __name__ == "__main__":
    main()