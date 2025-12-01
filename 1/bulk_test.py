#!/usr/bin/env python3
"""
Скрипт для массового тестирования ДКА с различными конфигурациями
"""

import subprocess
import tempfile
import csv
import random
import time
from typing import List, Tuple


def create_random_dfa(num_states: int = 5, alphabet: List[str] = None) -> str:
    """Создание случайного ДКА и возврат пути к CSV файлу"""
    if alphabet is None:
        alphabet = ['a', 'b']

    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')

    # Заголовок CSV
    header = [','] + alphabet + ['Final']
    temp_file.write(','.join(header) + '\n')

    # Генерация случайных переходов
    states = [f'q{i}' for i in range(num_states)]

    for i, state in enumerate(states):
        row = [state]

        # Случайные переходы для каждого символа алфавита
        for _ in alphabet:
            target_state = random.choice(states)
            row.append(target_state)

        # Случайное определение конечного состояния (примерно 30% состояний - конечные)
        is_final = '1' if random.random() < 0.3 else '0'
        row.append(is_final)

        temp_file.write(','.join(row) + '\n')

    temp_file.close()
    return temp_file.name


def generate_test_strings(alphabet: List[str], num_strings: int = 50) -> List[str]:
    """Генерация тестовых строк"""
    strings = []

    # Добавляем специальные случаи
    strings.append('')  # Пустая строка

    # Короткие строки
    for length in range(1, 6):
        for _ in range(5):
            strings.append(''.join(random.choice(alphabet) for _ in range(length)))

    # Длинные строки
    for _ in range(num_strings - len(strings)):
        length = random.randint(1, 20)
        strings.append(''.join(random.choice(alphabet) for _ in range(length)))

    return strings[:num_strings]


def run_comprehensive_tests():
    """Запуск всестороннего тестирования"""
    print("=" * 80)
    print("ВСЕСТОРОННЕЕ ТЕСТИРОВАНИЕ ПРОГРАММЫ ДКА")
    print("=" * 80)

    test_results = []

    # Тест 1: Простой ДКА (из примера)
    print("\n1. Тестирование простого ДКА (3 состояния):")
    simple_dfa = """
,a,b,Final
q0,q1,q0,0
q1,q1,q2,0
q2,q1,q0,1
"""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
        f.write(simple_dfa)
        simple_csv = f.name

    test_strings = ['ab', 'ba', 'abab', 'baba', 'aa', 'bb', 'abba', 'baab', '', 'a', 'b']
    run_test_set("Простой ДКА", simple_csv, test_strings)

    # Тест 2: Случайные ДКА
    print("\n2. Тестирование случайных ДКА:")
    for i in range(3):
        print(f"\n  ДКА #{i + 1}:")
        random_csv = create_random_dfa(num_states=random.randint(3, 8))
        test_strings = generate_test_strings(['a', 'b'], num_strings=30)
        run_test_set(f"Случайный ДКА #{i + 1}", random_csv, test_strings, show_details=False)

    # Тест 3: ДКА с большим алфавитом
    print("\n3. Тестирование ДКА с расширенным алфавитом:")
    complex_dfa = """
,a,b,c,d,Final
q0,q1,q0,q2,q0,0
q1,q1,q2,q0,q1,0
q2,q0,q1,q2,q2,1
q3,q0,q2,q1,q3,0
"""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
        f.write(complex_dfa)
        complex_csv = f.name

    test_strings = ['abcd', 'dcba', 'aaabbb', 'abc', 'ddd', 'abcabc', '', 'a', 'bcd']
    run_test_set("ДКА с расширенным алфавитом", complex_csv, test_strings)

    # Тест 4: Производительность
    print("\n4. Тестирование производительности:")
    start_time = time.time()

    large_dfa = create_random_dfa(num_states=15, alphabet=['a', 'b', 'c', 'd', 'e'])
    long_strings = [''.join(random.choice('abcde') for _ in range(100)) for _ in range(10)]

    for test_str in long_strings[:3]:  # Тестируем только 3 длинные строки
        result = subprocess.run(
            ['python', 'main.py', large_dfa, test_str],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            print(f"  Длина {len(test_str)}: OK")
        else:
            print(f"  Длина {len(test_str)}: ERROR")

    end_time = time.time()
    print(f"  Время выполнения: {end_time - start_time:.2f} секунд")

    print("\n" + "=" * 80)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)


def run_test_set(test_name: str, csv_file: str, test_strings: List[str], show_details: bool = True):
    """Запуск набора тестов для конкретного ДКА"""
    print(f"  {test_name}")
    print("  " + "-" * 40)

    total = len(test_strings)
    successful = 0
    failed = 0

    for i, test_str in enumerate(test_strings, 1):
        try:
            result = subprocess.run(
                ['python', 'main.py', csv_file, test_str],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=2  # Таймаут 2 секунды на тест
            )

            if result.returncode == 0:
                successful += 1
                if show_details:
                    print(f"  {i:3d}. '{test_str}' - OK")
            else:
                failed += 1
                if show_details:
                    print(f"  {i:3d}. '{test_str}' - ERROR: {result.stderr[:50]}")

        except subprocess.TimeoutExpired:
            failed += 1
            if show_details:
                print(f"  {i:3d}. '{test_str}' - TIMEOUT")
        except Exception as e:
            failed += 1
            if show_details:
                print(f"  {i:3d}. '{test_str}' - EXCEPTION: {str(e)[:50]}")

    print(f"  ИТОГО: {successful} успешно, {failed} с ошибками")

    if not show_details:
        # Показываем пример работы
        if test_strings:
            example_str = test_strings[0]
            result = subprocess.run(
                ['python', 'main.py', csv_file, example_str],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 2:
                    print(f"  Пример: '{example_str}' -> {lines[-2]}")


if __name__ == '__main__':
    run_comprehensive_tests()