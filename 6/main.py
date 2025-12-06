import csv
import sys
from collections import defaultdict
from typing import List, Dict, Tuple, Set, Optional


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

    def load_from_csv(self, csv_file: str) -> None:
        """
        Загрузка описания автомата из CSV файла

        Формат CSV:
        current_state,input_symbol,stack_top,new_state,stack_push
        """
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
                for symbol in stack_push:
                    if symbol != 'ε':
                        self.stack_alphabet.add(symbol)

                # Добавляем переход
                key = (current_state, input_symbol if input_symbol else 'ε',
                       stack_top if stack_top else 'ε')
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
        # Проверяем входные символы
        for symbol in input_string:
            if symbol not in self.input_alphabet:
                return False, [f"Ошибка: символ '{symbol}' не найден во входном алфавите"]

        # Инициализация
        current_configurations = [{
            'state': self.start_state,
            'stack': [self.start_stack_symbol],
            'position': 0,
            'history': [f"Начало: состояние={self.start_state}, стек=['{self.start_stack_symbol}']"]
        }]

        step = 0
        visited_configurations = set()

        while current_configurations and step < max_steps:
            step += 1
            new_configurations = []

            for config in current_configurations:
                state = config['state']
                stack = config['stack'].copy()
                position = config['position']
                history = config['history'].copy()

                # Проверяем, была ли уже такая конфигурация
                config_key = (state, tuple(stack), position)
                if config_key in visited_configurations:
                    continue
                visited_configurations.add(config_key)

                # Проверка условия допуска
                if self._check_acceptance(state, stack, position, input_string):
                    history.append("✓ Цепочка допускается")
                    return True, history

                # Получаем возможные переходы
                transitions = []

                # Переходы с чтением входного символа
                if position < len(input_string):
                    input_symbol = input_string[position]
                    key = (state, input_symbol, stack[-1] if stack else 'ε')
                    for new_state, stack_push in self.transitions.get(key, []):
                        transitions.append((new_state, stack_push, input_symbol, position + 1))

                # Эпсилон-переходы (без чтения входного символа)
                key_epsilon = (state, 'ε', stack[-1] if stack else 'ε')
                for new_state, stack_push in self.transitions.get(key_epsilon, []):
                    transitions.append((new_state, stack_push, 'ε', position))

                # Применяем переходы
                for new_state, stack_push, used_symbol, new_position in transitions:
                    new_stack = stack.copy()

                    # Удаляем верхний символ стека
                    if stack:
                        new_stack.pop()

                    # Добавляем новые символы в стек
                    for symbol in reversed(stack_push):
                        if symbol != 'ε':
                            new_stack.append(symbol)

                    # Создаем новую конфигурацию
                    used_symbol_str = f"'{used_symbol}'" if used_symbol != 'ε' else 'ε'
                    history_entry = (f"Шаг {step}: состояние={state}->{new_state}, "
                                     f"символ={used_symbol_str}, стек={stack}->{new_stack}")

                    new_config = {
                        'state': new_state,
                        'stack': new_stack,
                        'position': new_position,
                        'history': history + [history_entry]
                    }

                    new_configurations.append(new_config)

            current_configurations = new_configurations

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
    pda.print_info()

    # Обработка цепочек
    print("\nВВОД ЦЕПОЧЕК (для выхода введите 'exit' или 'quit')")
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
        details = input("Показать подробную информацию? (y/n): ").strip().lower()
        if details == 'y':
            print("\nИстория работы:")
            for entry in history[-10:]:  # Показываем последние 10 шагов
                print(f"  {entry}")


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

    pda.print_info()

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
        for chain, accept in results:
            status = "ДОПУСКАЕТСЯ" if accept else "НЕ ДОПУСКАЕТСЯ"
            f.write(f"{chain:20} -> {status}\n")

    print(f"\nРезультаты сохранены в файл: {output_file}")


def main():
    """Основная функция программы"""
    print("МАГАЗИННЫЙ АВТОМАТ (PDA) SIMULATOR")
    print("=" * 60)
    print("Режимы работы:")
    print("1. Интерактивный режим")
    print("2. Пакетный режим (с конфигурационным файлом)")
    print("3. Пример использования")

    choice = input("\nВыберите режим (1-3): ").strip()

    if choice == '1':
        interactive_mode()
    elif choice == '2':
        config_file = input("Введите путь к конфигурационному файлу: ").strip()
        chains_file = input("Введите путь к файлу с цепочками: ").strip()
        batch_mode(config_file, chains_file)
    elif choice == '3':
        run_example()
    else:
        print("Неверный выбор. Запуск интерактивного режима...")
        interactive_mode()


def run_example():
    """Запуск примера работы программы"""
    print("\n" + "=" * 60)
    print("ПРИМЕР: Магазинный автомат для языка {a^n b^n | n >= 0}")
    print("=" * 60)

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
    print("\n" + "=" * 60)
    print("ЗАПУСК ПРОВЕРКИ ПРИМЕРА")
    print("=" * 60)

    try:
        pda = load_pda_from_config('example_config.txt')
        pda.print_info()

        with open('example_chains.txt', 'r', encoding='utf-8') as f:
            chains = [line.strip() for line in f if line.strip()]

        print("\nРезультаты проверки цепочек:")
        for chain in chains:
            accept, _ = pda.simulate(chain, verbose=False)
            status = "✓ ДОПУСКАЕТСЯ" if accept else "✗ НЕ ДОПУСКАЕТСЯ"
            chain_display = chain if chain else "ε (пустая)"
            print(f"  {chain_display:20} -> {status}")

    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()