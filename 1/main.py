import sys
import csv
import os
from typing import Dict, List, Set, Tuple


class DFA:


    def __init__(self, csv_file: str):
        """Инициализация ДКА из CSV файла"""
        self.states: Dict[str, Dict[str, str]] = {}
        self.alphabet: List[str] = []
        self.start_state: str = ""
        self.final_states: Set[str] = set()

        self._load_from_csv(csv_file)

    def _load_from_csv(self, csv_file: str) -> None:

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                headers = next(reader)

                if len(headers) < 3:
                    raise ValueError("CSV файл должен содержать как минимум 3 столбца")

                self.alphabet = [h.strip() for h in headers[1:-1]]  # Символы алфавита

                for row in reader:
                    if not row or all(cell == '' for cell in row):  # Пропускаем пустые строки
                        continue

                    state = row[0].strip()
                    if not state:
                        continue

                    # Устанавливаем начальное состояние как первое состояние в файле
                    if not self.start_state:
                        self.start_state = state

                    # Создаем переходы для текущего состояния
                    transitions = {}
                    for i, symbol in enumerate(self.alphabet):
                        if i + 1 < len(row):
                            transitions[symbol] = row[i + 1].strip()
                        else:
                            transitions[symbol] = state  # По умолчанию остаемся в том же состоянии

                    # Проверяем, является ли состояние конечным
                    is_final = row[-1].strip() if len(row) > len(self.alphabet) + 1 else '0'
                    if is_final == '1':
                        self.final_states.add(state)

                    self.states[state] = transitions

        except FileNotFoundError:
            print(f"Ошибка: Файл '{csv_file}' не найден")
            sys.exit(1)
        except Exception as e:
            print(f"Ошибка при чтении CSV файла: {e}")
            sys.exit(1)

    def validate_string(self, input_str: str) -> Tuple[bool, List[str]]:
        """Проверка цепочки на допуск ДКА

        Возвращает:
            bool: Допускается ли цепочка
            List[str]: Последовательность состояний
        """
        current_state = self.start_state
        state_sequence = [current_state]

        for symbol in input_str:
            # Проверка на недопустимый символ
            if symbol not in self.alphabet:
                return False, state_sequence

            # Получение следующего состояния
            if current_state not in self.states:
                return False, state_sequence

            next_state = self.states[current_state].get(symbol)
            if not next_state:
                return False, state_sequence

            current_state = next_state
            state_sequence.append(current_state)

        # Проверка, является ли конечное состояние допускающим
        is_accepted = current_state in self.final_states
        return is_accepted, state_sequence

    def get_info(self) -> Dict:
        """Получение информации о ДКА"""
        return {
            'num_states': len(self.states),
            'alphabet': self.alphabet,
            'start_state': self.start_state,
            'final_states': list(self.final_states),
            'states': list(self.states.keys())
        }


def run_batch_test(dfa: DFA, test_cases: List[Tuple[str, bool]]) -> None:
    """Запуск пакетного тестирования"""
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ПАКЕТНОГО ТЕСТИРОВАНИЯ")
    print("=" * 60)

    passed = 0
    failed = 0

    for input_str, expected in test_cases:
        is_accepted, state_sequence = dfa.validate_string(input_str)

        if is_accepted == expected:
            status = "✓ ПРОЙДЕН"
            passed += 1
        else:
            status = "✗ НЕ ПРОЙДЕН"
            failed += 1

        result_str = "допускается" if is_accepted else "не допускается"
        expected_str = "должна допускаться" if expected else "не должна допускаться"

        print(f"{status}: '{input_str}' -> {result_str} (ожидалось: {expected_str})")
        if not is_accepted == expected:
            print(f"  Последовательность состояний: {' -> '.join(state_sequence)}")

    print(f"\nИТОГО: {passed} пройдено, {failed} не пройдено")
    print("=" * 60)


def main():

    if len(sys.argv) < 2:
        print("Использование: python main.py <csv_file> [input_strings]")
        print("ИЛИ: py main.py <csv_file> [input_strings]")
        print("ИЛИ: python3 main.py <csv_file> [input_strings]")
        print("\nПримеры:")
        print("  python main.py dfa.csv abab baba aaabbb")
        print("  python main.py dfa.csv (для интерактивного режима)")
        print("\nДля пакетного тестирования:")
        print("  python main.py dfa.csv --test")
        sys.exit(1)

    csv_file = sys.argv[1]


    if not os.path.exists(csv_file):
        print(f"Ошибка: Файл '{csv_file}' не найден")
        print("Убедитесь, что файл существует в текущей директории.")
        sys.exit(1)


    try:
        dfa = DFA(csv_file)
        info = dfa.get_info()

        print("=" * 60)
        print("ДЕТЕРМИНИРОВАННЫЙ КОНЕЧНЫЙ АВТОМАТ (ДКА)")
        print("=" * 60)
        print(f"Файл конфигурации: {csv_file}")
        print(f"Количество состояний: {info['num_states']}")
        print(f"Алфавит: {', '.join(info['alphabet'])}")
        print(f"Начальное состояние: {info['start_state']}")
        print(f"Конечные состояния: {', '.join(info['final_states'])}")
        print("=" * 60)

    except Exception as e:
        print(f"Ошибка при инициализации ДКА: {e}")
        sys.exit(1)


    if len(sys.argv) > 2 and sys.argv[2] == '--test':
        # Режим пакетного тестирования
        test_cases = [

            ("", False),  # Пустая строка
            ("a", False),  # q0->q1
            ("b", False),  # q0->q0
            ("ab", True),  # q0->q1->q2 ✓
            ("ba", False),  # q0->q0->q1
            ("aba", False),  # q0->q1->q2->q1
            ("bab", False),  # q0->q0->q1->q2
            ("aa", False),  # q0->q1->q1
            ("bb", False),  # q0->q0->q0
            ("abab", True),  # q0->q1->q2->q1->q2 ✓
            ("baba", False),  # q0->q0->q1->q2->q1
            ("abba", False),  # q0->q1->q2->q0->q1
            ("baab", False),  # q0->q0->q1->q1->q1
        ]

        run_batch_test(dfa, test_cases)

    elif len(sys.argv) > 2:

        input_strings = sys.argv[2:]
        print("\nПРОВЕРКА ЦЕПОЧЕК:")
        print("-" * 60)

        for input_str in input_strings:
            is_accepted, state_sequence = dfa.validate_string(input_str)

            if is_accepted:
                print(f"✓ Цепочка '{input_str}' ДОПУСКАЕТСЯ")
            else:
                print(f"✗ Цепочка '{input_str}' НЕ ДОПУСКАЕТСЯ")

            print(f"  Последовательность состояний: {' → '.join(state_sequence)}")
            print("-" * 60)

    else:
        # Интерактивный режим
        print("\nИНТЕРАКТИВНЫЙ РЕЖИМ")
        print("(для выхода введите 'exit' или 'quit')")
        print("-" * 60)

        while True:
            try:
                input_str = input("Введите цепочку для проверки: ").strip()

                if input_str.lower() in ['exit', 'quit', 'выход']:
                    print("Завершение работы...")
                    break

                if not input_str:
                    print("Введена пустая строка. Попробуйте еще раз.")
                    continue

                is_accepted, state_sequence = dfa.validate_string(input_str)

                if is_accepted:
                    print(f"✓ Цепочка '{input_str}' ДОПУСКАЕТСЯ")
                else:
                    print(f"✗ Цепочка '{input_str}' НЕ ДОПУСКАЕТСЯ")

                print(f"  Последовательность состояний: {' → '.join(state_sequence)}")
                print("-" * 60)

            except KeyboardInterrupt:
                print("\n\nЗавершение работы...")
                break
            except Exception as e:
                print(f"Произошла ошибка: {e}")
                print("-" * 60)


if __name__ == "__main__":
    main()