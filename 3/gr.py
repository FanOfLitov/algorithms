import csv
import graphviz
import os
from collections import defaultdict


def read_dfa_for_visualization(filepath):
    """Чтение ДКА из CSV файла для визуализации"""
    with open(filepath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        data = list(reader)

    # Извлекаем алфавит
    alphabet = data[0][1:-1]

    # Собираем информацию о состояниях и переходах
    states = []
    transitions = defaultdict(dict)
    accept_states = set()
    start_state = data[1][0].strip() if len(data) > 1 else None

    for i, row in enumerate(data[1:]):
        state_name = row[0].strip()
        states.append(state_name)

        # Проверяем, является ли состояние допускающим
        if len(row) > len(alphabet) + 1 and row[len(alphabet) + 1] == '*':
            accept_states.add(state_name)
        elif row[-1] == '*':  # альтернативная проверка
            accept_states.add(state_name)

        # Собираем переходы
        for j, symbol in enumerate(alphabet):
            if j + 1 < len(row):
                target = row[j + 1].strip()
                if target:  # если переход существует
                    transitions[state_name][symbol] = target

    return {
        'states': states,
        'alphabet': alphabet,
        'transitions': dict(transitions),
        'accept_states': accept_states,
        'start_state': start_state
    }


def visualize_dfa(dfa_info, output_file='dfa_graph'):
    """Визуализация ДКА"""

    # Создаем граф
    dot = graphviz.Digraph(comment='DFA', format='png')
    dot.attr(rankdir='LR', size='8,5')

    # Добавляем состояния
    for state in dfa_info['states']:
        node_attrs = {}

        if state == dfa_info['start_state']:
            # Начальное состояние
            node_attrs['style'] = 'filled'
            node_attrs['fillcolor'] = 'lightblue'

        if state in dfa_info['accept_states']:
            # Допускающее состояние
            node_attrs['shape'] = 'doublecircle'
        else:
            node_attrs['shape'] = 'circle'

        dot.node(state, **node_attrs)

    # Добавляем невидимое начальное состояние для стрелки
    dot.node('', '', shape='point')
    if dfa_info['start_state']:
        dot.edge('', dfa_info['start_state'])

    # Добавляем переходы
    for from_state, trans in dfa_info['transitions'].items():
        for symbol, to_state in trans.items():
            dot.edge(from_state, to_state, label=symbol)

    # Добавляем петли (самопереходы)
    for state in dfa_info['states']:
        if state in dfa_info['transitions']:
            for symbol, target in dfa_info['transitions'][state].items():
                if target == state:
                    dot.edge(state, state, label=symbol, dir='both')

    # Сохраняем граф
    output_dir = 'graphs'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_file)

    # Рендерим граф
    dot.render(output_path, view=False, cleanup=True)

    print(f"✓ Граф сохранен как {output_path}.png")
    print(f"  Состояния: {', '.join(dfa_info['states'])}")
    print(f"  Алфавит: {', '.join(dfa_info['alphabet'])}")
    print(f"  Начальное состояние: {dfa_info['start_state']}")
    print(f"  Допускающие состояния: {', '.join(dfa_info['accept_states'])}")

    return dot


def visualize_dfa_trace(dfa_info, input_string, output_file='dfa_trace'):
    """Визуализация пути обработки строки"""

    # Симулируем обработку строки
    current_state = dfa_info['start_state']
    path = [(current_state, "начальное")]

    for symbol in input_string:
        if symbol in dfa_info['transitions'].get(current_state, {}):
            next_state = dfa_info['transitions'][current_state][symbol]
            path.append((symbol, "символ"))
            path.append((next_state, f"после '{symbol}'"))
            current_state = next_state
        else:
            path.append((f"Нет перехода по '{symbol}'", "ошибка"))
            break

    # Создаем граф
    dot = graphviz.Digraph(comment='DFA Trace', format='png')
    dot.attr(rankdir='LR', size='8,5')

    # Добавляем состояния с цветовой маркировкой
    for state in dfa_info['states']:
        node_attrs = {}

        # Проверяем, проходит ли путь через это состояние
        path_states = [p[0] for p in path if isinstance(p[0], str) and p[0] in dfa_info['states']]

        if state in path_states:
            node_attrs['color'] = 'red'
            node_attrs['penwidth'] = '2'

        if state == dfa_info['start_state']:
            node_attrs['style'] = 'filled'
            node_attrs['fillcolor'] = 'lightblue'

        if state in dfa_info['accept_states']:
            node_attrs['shape'] = 'doublecircle'
        else:
            node_attrs['shape'] = 'circle'

        dot.node(state, **node_attrs)

    # Добавляем начальную стрелку
    dot.node('', '', shape='point')
    if dfa_info['start_state']:
        dot.edge('', dfa_info['start_state'])

    # Добавляем переходы с выделением пути
    for from_state, trans in dfa_info['transitions'].items():
        for symbol, to_state in trans.items():
            edge_attrs = {}

            # Проверяем, входит ли этот переход в путь
            for i in range(len(path) - 2):
                if (isinstance(path[i], tuple) and isinstance(path[i + 1], tuple) and
                        isinstance(path[i + 2], tuple)):
                    state1, desc1 = path[i]
                    sym, desc2 = path[i + 1]
                    state2, desc3 = path[i + 2]

                    if (state1 == from_state and state2 == to_state and
                            sym == symbol):
                        edge_attrs['color'] = 'red'
                        edge_attrs['penwidth'] = '2'
                        break

            dot.edge(from_state, to_state, label=symbol, **edge_attrs)

    # Добавляем информацию о результате
    final_state = current_state
    is_accepted = final_state in dfa_info['accept_states']

    dot.attr(label=f'Обработка строки: "{input_string}"\n'
                   f'Финальное состояние: {final_state}\n'
                   f'Результат: {"ПРИНЯТА" if is_accepted else "ОТВЕРГНУТА"}',
             labelloc='t', fontsize='12')

    # Сохраняем граф
    output_dir = 'graphs'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_file)

    dot.render(output_path, view=False, cleanup=True)

    print(f"✓ Граф с путем сохранен как {output_path}.png")
    print(f"  Путь: {' → '.join([str(p[0]) for p in path])}")
    print(f"  Строка '{input_string}' {'принята' if is_accepted else 'отвергнута'}")

    return dot, is_accepted


def create_step_by_step_visualization(dfa_info, input_string):
    """Создание пошаговой визуализации"""

    current_state = dfa_info['start_state']
    steps = []

    # Начальный шаг
    steps.append({
        'state': current_state,
        'symbol': None,
        'remaining': input_string,
        'processed': ''
    })

    # Обрабатываем каждый символ
    for i, symbol in enumerate(input_string):
        processed = input_string[:i]
        remaining = input_string[i + 1:]

        if symbol in dfa_info['transitions'].get(current_state, {}):
            next_state = dfa_info['transitions'][current_state][symbol]
            steps.append({
                'state': current_state,
                'symbol': symbol,
                'next_state': next_state,
                'remaining': remaining,
                'processed': processed + symbol
            })
            current_state = next_state
        else:
            steps.append({
                'state': current_state,
                'symbol': symbol,
                'next_state': 'НЕТ ПЕРЕХОДА',
                'remaining': remaining,
                'processed': processed + symbol
            })
            break

    # Создаем отдельные графы для каждого шага
    output_dir = 'graphs/steps'
    os.makedirs(output_dir, exist_ok=True)

    for i, step in enumerate(steps):
        dot = graphviz.Digraph(format='png')
        dot.attr(rankdir='LR', size='8,5')

        # Добавляем состояния
        for state in dfa_info['states']:
            node_attrs = {}

            if state == step.get('state'):
                node_attrs['style'] = 'filled'
                node_attrs['fillcolor'] = 'lightblue'

            if state in dfa_info['accept_states']:
                node_attrs['shape'] = 'doublecircle'
            else:
                node_attrs['shape'] = 'circle'

            dot.node(state, **node_attrs)

        # Добавляем начальную стрелку
        dot.node('', '', shape='point')
        if dfa_info['start_state']:
            dot.edge('', dfa_info['start_state'])

        # Добавляем переходы
        for from_state, trans in dfa_info['transitions'].items():
            for symbol, to_state in trans.items():
                edge_attrs = {}

                # Подсвечиваем текущий переход
                if (from_state == step.get('state') and
                        symbol == step.get('symbol') and
                        to_state == step.get('next_state')):
                    edge_attrs['color'] = 'red'
                    edge_attrs['penwidth'] = '3'

                dot.edge(from_state, to_state, label=symbol, **edge_attrs)

        # Добавляем информацию о шаге
        if step['symbol'] is None:
            label = f'Шаг {i}: Начальное состояние\nСостояние: {step["state"]}\nОбработано: "{step["processed"]}"\nОсталось: "{step["remaining"]}"'
        else:
            label = (f'Шаг {i}: Символ "{step["symbol"]}"\n'
                     f'Из: {step["state"]} → В: {step.get("next_state", "?")}\n'
                     f'Обработано: "{step["processed"]}"\n'
                     f'Осталось: "{step["remaining"]}"')

        dot.attr(label=label, labelloc='t', fontsize='12')

        # Сохраняем шаг
        output_path = os.path.join(output_dir, f'step_{i:02d}')
        dot.render(output_path, view=False, cleanup=True)

    print(f"✓ Создано {len(steps)} шагов в папке {output_dir}/")

    return steps


def main():
    """Основная функция визуализатора"""
    print("=" * 60)
    print("ВИЗУАЛИЗАТОР ДЕТЕРМИНИРОВАННЫХ КОНЕЧНЫХ АВТОМАТОВ")
    print("=" * 60)

    csv_file = input("\nВведите путь к CSV-файлу с ДКА: ").strip()

    if not os.path.exists(csv_file):
        print(f"✗ Файл '{csv_file}' не найден!")
        return

    try:
        # Читаем ДКА
        dfa_info = read_dfa_for_visualization(csv_file)

        print(f"\n✓ ДКА успешно загружен:")
        print(f"  Состояния: {', '.join(dfa_info['states'])}")
        print(f"  Алфавит: {', '.join(dfa_info['alphabet'])}")
        print(f"  Начальное состояние: {dfa_info['start_state']}")
        print(f"  Допускающие состояния: {', '.join(dfa_info['accept_states'])}")

        # Визуализация графа
        print("\n" + "=" * 60)
        graph_name = input("Введите имя для файла графа (по умолчанию 'dfa_graph'): ").strip()
        if not graph_name:
            graph_name = 'dfa_graph'

        visualize_dfa(dfa_info, graph_name)

        # Визуализация пути для строки
        print("\n" + "=" * 60)
        while True:
            test_string = input("Введите строку для тестирования (или 'q' для выхода): ").strip()

            if test_string.lower() == 'q':
                break

            if not test_string:
                print("Пожалуйста, введите строку.")
                continue

            # Проверяем символы
            invalid_chars = [c for c in test_string if c not in dfa_info['alphabet']]
            if invalid_chars:
                print(f"✗ В строке есть недопустимые символы: {set(invalid_chars)}")
                print(f"  Алфавит ДКА: {', '.join(dfa_info['alphabet'])}")
                continue

            print(f"\nТестирование строки: '{test_string}'")

            # Визуализация пути
            trace_name = f"trace_{test_string}" if len(test_string) < 10 else "dfa_trace"
            dot_trace, result = visualize_dfa_trace(dfa_info, test_string, trace_name)

            # Пошаговая визуализация
            create_choice = input("\nСоздать пошаговую визуализацию? (да/нет): ").strip().lower()
            if create_choice in ['да', 'д', 'yes', 'y']:
                steps = create_step_by_step_visualization(dfa_info, test_string)

                # Показываем путь в консоли
                print("\nПуть обработки:")
                print("-" * 40)
                for i, step in enumerate(steps):
                    if step['symbol'] is None:
                        print(f"Шаг {i}: Начальное состояние: {step['state']}")
                    else:
                        print(f"Шаг {i}: {step['state']} --({step['symbol']})--> {step['next_state']}")
                print("-" * 40)
                print(f"Результат: строка {'принята' if result else 'отвергнута'}")

            print("\n" + "-" * 40)

    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()