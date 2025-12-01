import csv
from collections import defaultdict


class NFA:
    def __init__(self, states, alphabet, transitions, start_state, accept_states):
        """
        Инициализация НКА

        Параметры:
        - states: множество состояний
        - alphabet: алфавит (символы входной строки + 'ε' для эпсилон-переходов)
        - transitions: словарь переходов
        - start_state: начальное состояние
        - accept_states: множество допускающих состояний
        """
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start_state = start_state
        self.accept_states = accept_states

    def epsilon_closure(self, states):
        """
        Вычисление ε-замыкания множества состояний

        Возвращает все состояния, достижимые из данных состояний
        с помощью нуля или более ε-переходов
        """
        closure = set(states)
        stack = list(states)

        while stack:
            current_state = stack.pop()

            # Если есть ε-переходы из текущего состояния
            if 'ε' in self.transitions[current_state]:
                for next_state in self.transitions[current_state]['ε']:
                    if next_state not in closure:
                        closure.add(next_state)
                        stack.append(next_state)

        return closure

    def process_input(self, input_string):
        """
        Обработка входной строки НКА

        Возвращает True, если строка принимается автоматом,
        и False в противном случае
        """
        # Начинаем с ε-замыкания начального состояния
        current_states = self.epsilon_closure({self.start_state})

        # Обрабатываем каждый символ входной строки
        for symbol in input_string:
            # Проверяем, что символ есть в алфавите
            if symbol not in self.alphabet and symbol != 'ε':
                raise ValueError(f"Символ '{symbol}' не найден в алфавите")

            next_states = set()

            # Для каждого текущего состояния находим все возможные переходы по текущему символу
            for state in current_states:
                if symbol in self.transitions[state]:
                    next_states.update(self.transitions[state][symbol])

            # Вычисляем ε-замыкание для нового множества состояний
            current_states = self.epsilon_closure(next_states)

            # Если после обработки символа нет активных состояний, строка не принимается
            if not current_states:
                return False

        # Проверяем, есть ли среди текущих состояний допускающее
        return any(state in self.accept_states for state in current_states)


def read_nfa_from_csv(filepath):
    """
    Чтение описания НКА из CSV-файла

    Формат CSV:
    - Первая строка: заголовки (первая ячейка пустая, затем символы алфавита)
    - Последующие строки: для каждого состояния указываются переходы
    - Последний столбец: '*' для допускающих состояний
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        data = list(reader)

    # Извлекаем алфавит из первой строки (пропускаем первую пустую ячейку)
    alphabet = data[0][1:]

    # Инициализируем структуры для хранения данных об автомате
    states = set()
    transitions = defaultdict(lambda: defaultdict(set))
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

        # Обрабатываем переходы для каждого символа алфавита
        for j, symbol in enumerate(alphabet):
            if j + 1 < len(row):  # Проверяем, что в строке достаточно столбцов
                target_states = row[j + 1].strip()
                if target_states:  # Если есть переходы
                    # Разделяем состояния, если их несколько (через запятую или пробел)
                    for target in target_states.replace(',', ' ').split():
                        target = target.strip()
                        if target:
                            transitions[state_name][symbol].add(target)

    return NFA(states, alphabet, transitions, start_state, accept_states)


def main():
    """
    Основная функция программы
    """
    print("Программа моделирования НКА")
    print("=" * 50)

    try:
        # Чтение автомата из CSV-файла
        csv_file = input("Введите путь к CSV-файлу с описанием НКА: ")
        nfa = read_nfa_from_csv(csv_file)

        print(f"\nНКА успешно загружен:")
        print(f"  Состояния: {', '.join(sorted(nfa.states))}")
        print(f"  Алфавит: {', '.join(nfa.alphabet)}")
        print(f"  Начальное состояние: {nfa.start_state}")
        print(f"  Допускающие состояния: {', '.join(sorted(nfa.accept_states))}")

        # Обработка входных цепочек
        print("\n" + "=" * 50)
        print("Введите цепочки для проверки (пустая строка для завершения):")

        while True:
            input_string = input("\nВведите цепочку: ").strip()

            if not input_string:
                print("Завершение работы программы.")
                break

            try:
                result = nfa.process_input(input_string)
                status = "ПРИНЯТА" if result else "ОТВЕРГНУТА"
                print(f"Цепочка '{input_string}': {status}")
            except ValueError as e:
                print(f"Ошибка: {e}")

    except FileNotFoundError:
        print(f"Ошибка: Файл '{csv_file}' не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    main()