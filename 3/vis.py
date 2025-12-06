import csv
import os
from collections import defaultdict


class StepByStepDFA:
    """Класс для пошагового выполнения ДКА"""

    def __init__(self, csv_file=None, dfa_info=None):
        if csv_file:
            self.load_from_csv(csv_file)
        elif dfa_info:
            self.load_from_info(dfa_info)

    def load_from_csv(self, csv_file):
        """Загрузка ДКА из CSV файла"""
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            data = list(reader)

        # Извлекаем алфавит
        self.alphabet = data[0][1:-1]

        # Инициализируем структуры
        self.states = []
        self.transitions = defaultdict(dict)
        self.accept_states = set()

        # Обрабатываем строки
        for i, row in enumerate(data[1:]):
            state_name = row[0].strip()
            self.states.append(state_name)

            if i == 0:
                self.start_state = state_name

            # Проверяем, является ли состояние допускающим
            if len(row) > len(self.alphabet) + 1 and row[len(self.alphabet) + 1] == '*':
                self.accept_states.add(state_name)
            elif row[-1] == '*':
                self.accept_states.add(state_name)

            # Заполняем переходы
            for j, symbol in enumerate(self.alphabet):
                if j + 1 < len(row) and row[j + 1].strip():
                    self.transitions[state_name][symbol] = row[j + 1].strip()

    def load_from_info(self, dfa_info):
        """Загрузка ДКА из словаря"""
        self.states = dfa_info['states']
        self.alphabet = dfa_info['alphabet']
        self.transitions = dfa_info['transitions']
        self.start_state = dfa_info['start_state']
        self.accept_states = dfa_info['accept_states']

    def process_step_by_step(self, input_string):
        """Пошаговая обработка строки с выводом в консоль"""
        print(f"\n{'=' * 60}")
        print(f"ПОШАГОВАЯ ОБРАБОТКА СТРОКИ: '{input_string}'")
        print(f"{'=' * 60}\n")

        current_state = self.start_state
        step = 1

        print(f"Шаг {step}: Начальное состояние: {current_state}")
        print(f"       Текущая строка: '{input_string}'")
        print(f"       Индекс символа: 0/{len(input_string)}")
        print()

        for idx, symbol in enumerate(input_string):
            step += 1

            # Проверяем допустимость символа
            if symbol not in self.alphabet:
                print(f"Шаг {step}: ОШИБКА! Символ '{symbol}' не в алфавите")
                print(f"       Алфавит: {', '.join(self.alphabet)}")
                return False

            # Проверяем наличие перехода
            if symbol in self.transitions.get(current_state, {}):
                next_state = self.transitions[current_state][symbol]

                print(f"Шаг {step}: Символ: '{symbol}'")
                print(f"       Переход: {current_state} --({symbol})--> {next_state}")
                print(f"       Обработано: '{input_string[:idx + 1]}'")
                print(f"       Осталось: '{input_string[idx + 1:]}'")
                print(f"       Текущее состояние: {next_state}")

                current_state = next_state
            else:
                print(f"Шаг {step}: ОШИБКА! Нет перехода из состояния {current_state} по символу '{symbol}'")
                print(f"       Доступные переходы из {current_state}:")
                if current_state in self.transitions:
                    for sym, target in self.transitions[current_state].items():
                        print(f"         {sym} -> {target}")
                else:
                    print(f"         Нет переходов")
                return False

            print()

        # Финальное состояние
        step += 1
        is_accepted = current_state in self.accept_states

        print(f"Шаг {step}: КОНЕЦ ОБРАБОТКИ")
        print(f"       Финальное состояние: {current_state}")
        print(f"       Это {'ДОПУСКАЮЩЕЕ' if is_accepted else 'НЕДОПУСКАЮЩЕЕ'} состояние")
        print(f"\n{'=' * 60}")
        print(f"РЕЗУЛЬТАТ: Строка '{input_string}' {'ПРИНЯТА' if is_accepted else 'ОТВЕРГНУТА'}")
        print(f"{'=' * 60}")

        return is_accepted

    def process_interactive(self):
        """Интерактивный режим пошагового выполнения"""
        print("\n" + "=" * 60)
        print("ИНТЕРАКТИВНЫЙ РЕЖИМ ПОШАГОВОГО ВЫПОЛНЕНИЯ")
        print("=" * 60)

        input_string = input("\nВведите строку для обработки: ").strip()

        print(f"\nНачинаем обработку строки: '{input_string}'")
        print("Нажмите Enter для перехода к следующему шагу...")

        current_state = self.start_state
        processed = ""
        remaining = input_string

        print(f"\nТекущее состояние: {current_state}")
        print(f"Обработано: '{processed}'")
        print(f"Осталось: '{remaining}'")

        input("\nНажмите Enter для начала...")

        for idx, symbol in enumerate(input_string):
            # Проверяем символ
            if symbol not in self.alphabet:
                print(f"\nОШИБКА: Символ '{symbol}' не в алфавите!")
                print(f"Алфавит: {', '.join(self.alphabet)}")
                return False

            # Проверяем переход
            if symbol in self.transitions.get(current_state, {}):
                next_state = self.transitions[current_state][symbol]

                print(f"\n{'=' * 40}")
                print(f"ШАГ {idx + 1}:")
                print(f"  Текущий символ: '{symbol}'")
                print(f"  Из состояния: {current_state}")
                print(f"  В состояние: {next_state}")
                print(f"  Переход: {current_state} --({symbol})--> {next_state}")

                current_state = next_state
                processed = input_string[:idx + 1]
                remaining = input_string[idx + 1:]

                print(f"\nТекущее состояние: {current_state}")
                print(f"Обработано: '{processed}'")
                print(f"Осталось: '{remaining}'")

                if idx < len(input_string) - 1:
                    input("\nНажмите Enter для следующего шага...")
            else:
                print(f"\nОШИБКА: Нет перехода из {current_state} по '{symbol}'!")
                print(f"Доступные переходы из {current_state}:")
                if current_state in self.transitions:
                    for sym, target in self.transitions[current_state].items():
                        print(f"  {sym} -> {target}")
                return False

        # Финальный результат
        is_accepted = current_state in self.accept_states

        print(f"\n{'=' * 60}")
        print(f"ОБРАБОТКА ЗАВЕРШЕНА!")
        print(f"Финальное состояние: {current_state}")
        print(f"Это {'ДОПУСКАЮЩЕЕ' if is_accepted else 'НЕДОПУСКАЮЩЕЕ'} состояние")
        print(f"\nРЕЗУЛЬТАТ: Строка '{input_string}' {'ПРИНЯТА' if is_accepted else 'ОТВЕРГНУТА'}")

        return is_accepted

    def show_info(self):
        """Отображение информации о ДКА"""
        print("\n" + "=" * 60)
        print("ИНФОРМАЦИЯ О ДКА")
        print("=" * 60)

        print(f"Состояния: {', '.join(sorted(self.states))}")
        print(f"Алфавит: {', '.join(sorted(self.alphabet))}")
        print(f"Начальное состояние: {self.start_state}")
        print(f"Допускающие состояния: {', '.join(sorted(self.accept_states))}")

        print("\nТаблица переходов:")
        print("-" * 40)

        # Заголовок
        header = ["Состояние"] + sorted(self.alphabet) + ["Допускающее"]
        print(" | ".join(header))
        print("-" * (len(" | ".join(header))))

        # Строки
        for state in sorted(self.states):
            row = [state]
            for symbol in sorted(self.alphabet):
                row.append(self.transitions.get(state, {}).get(symbol, "-"))

            # Маркер допускающего состояния
            if state in self.accept_states:
                row.append("*")
            else:
                row.append("")

            print(" | ".join(row))


def main():
    """Основная функция"""
    print("ПОШАГОВЫЙ ИСПОЛНИТЕЛЬ ДКА")
    print("=" * 60)

    csv_file = input("Введите путь к CSV-файлу с ДКА: ").strip()

    if not os.path.exists(csv_file):
        print(f"✗ Файл {csv_file} не найден!")
        return

    # Создаем исполнитель
    try:
        dfa_executor = StepByStepDFA(csv_file)

        while True:
            print("\n" + "=" * 60)
            print("МЕНЮ:")
            print("  1. Пошаговая обработка строки (полный вывод)")
            print("  2. Интерактивный режим (с паузами)")
            print("  3. Показать информацию о ДКА")
            print("  4. Тестировать несколько строк")
            print("  0. Выход")
            print("=" * 60)

            choice = input("Выберите действие (0-4): ").strip()

            if choice == '0':
                print("Выход из программы.")
                break

            elif choice == '1':
                input_string = input("\nВведите строку для обработки: ").strip()
                if input_string:
                    dfa_executor.process_step_by_step(input_string)
                else:
                    print("Введите непустую строку.")

            elif choice == '2':
                dfa_executor.process_interactive()

            elif choice == '3':
                dfa_executor.show_info()

            elif choice == '4':
                print("\nТЕСТИРОВАНИЕ НЕСКОЛЬКИХ СТРОК")
                print("Введите строки для тестирования (пустая строка для завершения):")

                test_strings = []
                while True:
                    test_str = input(f"Строка {len(test_strings) + 1}: ").strip()
                    if not test_str:
                        break

                    # Проверяем символы
                    invalid_chars = [c for c in test_str if c not in dfa_executor.alphabet]
                    if invalid_chars:
                        print(f"  ✗ Символы {set(invalid_chars)} не в алфавите!")
                        continue

                    test_strings.append(test_str)

                if test_strings:
                    print(f"\nТестирование {len(test_strings)} строк...")
                    for test_str in test_strings:
                        print(f"\n{'=' * 40}")
                        print(f"Строка: '{test_str}'")
                        result = dfa_executor.process_step_by_step(test_str)
                        print(f"Результат: {'ПРИНЯТА' if result else 'ОТВЕРГНУТА'}")
                else:
                    print("Не введено ни одной строки.")

            else:
                print("Неверный выбор. Попробуйте снова.")

            input("\nНажмите Enter для продолжения...")

    except Exception as e:
        print(f"✗ Ошибка: {e}")


if __name__ == '__main__':
    main()