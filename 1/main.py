import sys
import csv


def main():
    if len(sys.argv) < 2:
        print("Использование: python main.py <csv_file> [input_strings]")
        sys.exit(1)

    csv_file = sys.argv[1]
    dfa = {}
    alphabet = []
    start_state = None
    final_states = set()

    # Чтение описания автомата из CSV
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        headers = next(reader)
        alphabet = headers[1:-1]  # Символы алфавита
        for row in reader:
            state = row[0]
            if start_state is None:
                start_state = state
            transitions = {}
            for i, symbol in enumerate(alphabet):
                transitions[symbol] = row[i + 1]
            is_final = row[-1].strip()
            if is_final == '1':
                final_states.add(state)
            dfa[state] = transitions

    # Чтение цепочек для проверки
    if len(sys.argv) > 2:
        input_strings = sys.argv[2:]
    else:
        input_strings = [input("Введите цепочку: ")]

    # Проверка каждой цепочки
    for input_str in input_strings:
        current_state = start_state
        try:
            for symbol in input_str:
                current_state = dfa[current_state][symbol]
            if current_state in final_states:
                print(f"Цепочка '{input_str}' допускается.")
            else:
                print(f"Цепочка '{input_str}' не допускается.")
        except KeyError:
            print(f"Цепочка '{input_str}' содержит недопустимый символ или переход не определён.")


if __name__ == "__main__":
    main()