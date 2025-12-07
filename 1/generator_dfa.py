#!/usr/bin/env python3
"""
Генератор тестовых CSV файлов для ДКА
"""

import csv
import random
import os


def generate_dfa_csv(filename: str, num_states: int = 5, alphabet: list = None,
                     start_state: str = "q0", final_prob: float = 0.3):
    """Генерация CSV файла с описанием ДКА"""

    if alphabet is None:
        alphabet = ['a', 'b']

    states = [f'q{i}' for i in range(num_states)]

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Заголовок
        header = [''] + alphabet + ['Final']
        writer.writerow(header)

        # Состояния
        for i, state in enumerate(states):
            row = [state]

            # Переходы для каждого символа алфавита
            for _ in alphabet:
                target = random.choice(states)
                row.append(target)

            # Конечное состояние
            is_final = '1' if random.random() < final_prob else '0'
            row.append(is_final)

            writer.writerow(row)

    print(f"Создан файл: {filename}")
    print(f"  Состояний: {num_states}")
    print(f"  Алфавит: {alphabet}")
    print(f"  Вероятность конечного состояния: {final_prob * 100}%")

    return filename


def generate_specific_dfa(filename: str, pattern: str = "ends_with_ab"):
    """Генерация специфического ДКА"""

    if pattern == "ends_with_ab":
        # ДКА, распознающий цепочки, оканчивающиеся на "ab"
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['', 'a', 'b', 'Final'])
            writer.writerow(['q0', 'q1', 'q0', '0'])
            writer.writerow(['q1', 'q1', 'q2', '0'])
            writer.writerow(['q2', 'q1', 'q0', '1'])

        print(f"Создан файл: {filename} (ДКА для цепочек, оканчивающихся на 'ab')")

    elif pattern == "contains_aa":
        # ДКА, распознающий цепочки, содержащие "aa"
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['', 'a', 'b', 'Final'])
            writer.writerow(['q0', 'q1', 'q0', '0'])
            writer.writerow(['q1', 'q2', 'q0', '0'])
            writer.writerow(['q2', 'q2', 'q2', '1'])

        print(f"Создан файл: {filename} (ДКА для цепочек, содержащих 'aa')")

    elif pattern == "even_a":
        # ДКА, распознающий цепочки с четным числом 'a'
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['', 'a', 'b', 'Final'])
            writer.writerow(['q0', 'q1', 'q0', '1'])  # четное число 'a' (0 - четное)
            writer.writerow(['q1', 'q0', 'q1', '0'])  # нечетное число 'a'

        print(f"Создан файл: {filename} (ДКА для цепочек с четным числом 'a')")

    return filename


def main():
    """Основная функция"""
    print("ГЕНЕРАТОР CSV ФАЙЛОВ ДЛЯ ДКА")
    print("=" * 50)

    print("\nВыберите тип ДКА для генерации:")
    print("1. Случайный ДКА")
    print("2. ДКА для цепочек, оканчивающихся на 'ab'")
    print("3. ДКА для цепочек, содержащих 'aa'")
    print("4. ДКА для цепочек с четным числом 'a'")
    print("5. Выход")

    try:
        choice = input("\nВведите номер (1-5): ").strip()

        if choice == '1':
            num_states = int(input("Количество состояний (по умолчанию 5): ") or "5")
            alphabet_str = input("Алфавит (через запятую, по умолчанию a,b): ") or "a,b"
            alphabet = [s.strip() for s in alphabet_str.split(',')]
            filename = input("Имя файла (по умолчанию random_dfa.csv): ") or "random_dfa.csv"

            generate_dfa_csv(filename, num_states, alphabet)

        elif choice in ['2', '3', '4']:
            patterns = {'2': 'ends_with_ab', '3': 'contains_aa', '4': 'even_a'}
            pattern = patterns[choice]
            filename = input(f"Имя файла (по умолчанию {pattern}.csv): ") or f"{pattern}.csv"

            generate_specific_dfa(filename, pattern)

        elif choice == '5':
            print("Выход...")
            return

        print(f"\nФайл '{filename}' создан успешно.")
        print("Используйте его с программой: python xml_lexer.py <имя_файла.csv>")

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == '__main__':
    main()