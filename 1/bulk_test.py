#!/usr/bin/env python3
"""
Скрипт для массового тестирования ДКА с различными конфигурациями
Использует класс DFA напрямую без subprocess
"""

import tempfile
import csv
import random
import time
import os
import sys
from typing import List, Tuple, Dict

# Добавляем текущую директорию в путь Python
sys.path.append('.')

try:
    from main import DFA
except ImportError:
    print("Ошибка: Не удалось импортировать модуль main.py")
    print("Убедитесь, что файл main.py находится в той же директории.")
    sys.exit(1)


def create_test_dfa(num_states: int = 5, alphabet: List[str] = None,
                    start_state: str = "q0") -> Tuple[str, Dict]:
    """Создание тестового ДКА и возврат пути к CSV файлу и описания"""
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

    # Создаем описание ДКА
    description = {
        'num_states': num_states,
        'alphabet': alphabet,
        'states': states,
        'file_path': temp_file.name
    }

    return temp_file.name, description


def create_specific_dfa() -> Tuple[str, Dict]:
    """Создание конкретного ДКА для предсказуемого тестирования"""
    # ДКА, который допускает цепочки, содержащие "ab" и заканчивающиеся на 'b'
    csv_content = """,a,b,Final
q0,q1,q0,0
q1,q1,q2,0
q2,q1,q2,1"""

    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
    temp_file.write(csv_content)
    temp_file.close()

    description = {
        'num_states': 3,
        'alphabet': ['a', 'b'],
        'states': ['q0', 'q1', 'q2'],
        'file_path': temp_file.name,
        'name': 'ДКА для цепочек, содержащих "ab" и заканчивающихся на "b"'
    }

    return temp_file.name, description


def generate_test_strings(alphabet: List[str], num_strings: int = 50,
                          min_length: int = 0, max_length: int = 20) -> List[str]:
    """Генерация тестовых строк"""
    strings = []

    # Добавляем специальные случаи
    if min_length <= 0:
        strings.append('')  # Пустая строка

    # Короткие строки (1-5 символов)
    for length in range(max(1, min_length), min(6, max_length + 1)):
        for _ in range(min(3, num_strings // 10)):
            strings.append(''.join(random.choice(alphabet) for _ in range(length)))

    # Случайные строки
    remaining = num_strings - len(strings)
    for _ in range(remaining):
        length = random.randint(min_length, max_length)
        strings.append(''.join(random.choice(alphabet) for _ in range(length)))

    # Удаляем дубликаты
    unique_strings = []
    seen = set()
    for s in strings:
        if s not in seen:
            seen.add(s)
            unique_strings.append(s)

    return unique_strings[:num_strings]


def run_dfa_test(dfa: DFA, test_strings: List[str]) -> Dict:
    """Запуск тестов для конкретного ДКА"""
    results = {
        'total': len(test_strings),
        'accepted': 0,
        'rejected': 0,
        'errors': 0,
        'details': []
    }

    for test_str in test_strings:
        try:
            is_accepted, state_sequence = dfa.validate_string(test_str)

            results['details'].append({
                'string': test_str,
                'accepted': is_accepted,
                'state_sequence': state_sequence,
                'error': None
            })

            if is_accepted:
                results['accepted'] += 1
            else:
                results['rejected'] += 1

        except Exception as e:
            results['errors'] += 1
            results['details'].append({
                'string': test_str,
                'accepted': False,
                'state_sequence': [],
                'error': str(e)
            })

    return results


def run_comprehensive_tests():
    """Запуск всестороннего тестирования"""
    print("\n" + "=" * 80)
    print("ВСЕСТОРОННЕЕ ТЕСТИРОВАНИЕ ПРОГРАММЫ ДКА")
    print("=" * 80)

    test_results = []
    temp_files = []  # Для отслеживания временных файлов

    try:
        # Тест 1: Простой ДКА (из примера)
        print("\n1. Тестирование простого ДКА (3 состояния, алфавит {a, b}):")
        simple_dfa = """,a,b,Final
q0,q1,q0,0
q1,q1,q2,0
q2,q1,q0,1"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            f.write(simple_dfa)
            simple_csv = f.name
            temp_files.append(simple_csv)

        dfa = DFA(simple_csv)
        test_strings = ['ab', 'ba', 'abab', 'baba', 'aa', 'bb', 'abba', 'baab', '', 'a', 'b']
        results = run_dfa_test(dfa, test_strings)

        print(f"  Загружен ДКА с {len(dfa.states)} состояниями")
        print(f"  Алфавит: {dfa.alphabet}")
        print(f"  Начальное состояние: {dfa.start_state}")
        print(f"  Конечные состояния: {list(dfa.final_states)}")
        print(f"  Протестировано цепочек: {results['total']}")
        print(f"  Допущено: {results['accepted']}, Отвергнуто: {results['rejected']}")

        # Показываем несколько примеров
        print(f"  Примеры результатов:")
        for detail in results['details'][:5]:
            status = "✓" if detail['accepted'] else "✗"
            print(f"    {status} '{detail['string']}' -> {'допускается' if detail['accepted'] else 'не допускается'}")

        test_results.append({
            'name': 'Простой ДКА',
            'results': results,
            'success': results['errors'] == 0
        })

        # Тест 2: Случайные ДКА
        print("\n2. Тестирование случайных ДКА:")
        random_results = []

        for i in range(3):
            print(f"\n  ДКА #{i + 1}:")
            random_csv, description = create_test_dfa(
                num_states=random.randint(3, 8),
                alphabet=random.choice([['a', 'b'], ['0', '1'], ['x', 'y', 'z']])
            )
            temp_files.append(random_csv)

            dfa = DFA(random_csv)
            test_strings = generate_test_strings(dfa.alphabet, num_strings=20)
            results = run_dfa_test(dfa, test_strings)

            print(f"    Состояний: {description['num_states']}, Алфавит: {description['alphabet']}")
            print(f"    Цепочек: {results['total']}, Ошибок: {results['errors']}")

            random_results.append(results)

            if results['errors'] > 0:
                print(f"    *Bad* Найдены ошибки при обработке!")

        test_results.append({
            'name': 'Случайные ДКА (3 шт)',
            'results': {
                'total': sum(r['total'] for r in random_results),
                'errors': sum(r['errors'] for r in random_results),
                'accepted': sum(r['accepted'] for r in random_results),
                'rejected': sum(r['rejected'] for r in random_results)
            },
            'success': all(r['errors'] == 0 for r in random_results)
        })

        # Тест 3: ДКА с большим алфавитом
        print("\n3. Тестирование ДКА с расширенным алфавитом:")
        complex_dfa = """,a,b,c,d,Final
q0,q1,q0,q2,q0,0
q1,q1,q2,q0,q1,0
q2,q0,q1,q2,q2,1
q3,q0,q2,q1,q3,0"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            f.write(complex_dfa)
            complex_csv = f.name
            temp_files.append(complex_csv)

        dfa = DFA(complex_csv)
        test_strings = ['abcd', 'dcba', 'aaabbb', 'abc', 'ddd', 'abcabc', '', 'a', 'bcd']
        results = run_dfa_test(dfa, test_strings)

        print(f"  Алфавит: {dfa.alphabet} (4 символа)")
        print(f"  Состояний: {len(dfa.states)}")
        print(f"  Протестировано цепочек: {results['total']}")
        print(f"  Ошибок: {results['errors']}")

        test_results.append({
            'name': 'ДКА с расширенным алфавитом',
            'results': results,
            'success': results['errors'] == 0
        })

        # Тест 4: Производительность
        print("\n4. Тестирование производительности:")
        start_time = time.time()

        performance_csv, _ = create_test_dfa(num_states=10, alphabet=['a', 'b', 'c', 'd', 'e'])
        temp_files.append(performance_csv)

        dfa = DFA(performance_csv)

        # Генерируем длинные строки
        long_strings = []
        for _ in range(10):
            length = random.randint(50, 200)
            long_strings.append(''.join(random.choice('abcde') for _ in range(length)))

        performance_results = []
        for i, test_str in enumerate(long_strings[:5], 1):  # Тестируем только 5 длинных строк
            try:
                test_start = time.time()
                is_accepted, _ = dfa.validate_string(test_str)
                test_time = time.time() - test_start

                performance_results.append({
                    'length': len(test_str),
                    'time': test_time,
                    'success': True
                })

                print(f"    Цепочка {i} (длина {len(test_str)}): {test_time:.4f} сек")
            except Exception as e:
                performance_results.append({
                    'length': len(test_str),
                    'time': 0,
                    'success': False,
                    'error': str(e)
                })
                print(f"    Цепочка {i} (длина {len(test_str)}): ОШИБКА - {e}")

        total_time = time.time() - start_time

        avg_time = sum(r['time'] for r in performance_results) / len(performance_results) if performance_results else 0
        success_rate = sum(1 for r in performance_results if r['success']) / len(
            performance_results) * 100 if performance_results else 0

        print(f"  Общее время: {total_time:.2f} сек")
        print(f"  Среднее время на цепочку: {avg_time:.4f} сек")
        print(f"  Успешность: {success_rate:.1f}%")

        test_results.append({
            'name': 'Тест производительности',
            'results': {
                'total_time': total_time,
                'avg_time': avg_time,
                'success_rate': success_rate
            },
            'success': success_rate >= 90.0
        })

        # Тест 5: Граничные случаи
        print("\n5. Тестирование граничных случаев:")

        # ДКА с одним состоянием
        single_state_dfa = """,a,b,Final
q0,q0,q0,1"""

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            f.write(single_state_dfa)
            single_csv = f.name
            temp_files.append(single_csv)

        dfa = DFA(single_csv)

        edge_cases = [
            ("", True, "Пустая строка"),
            ("a", True, "Один символ"),
            ("b", True, "Другой символ"),
            ("ababab", True, "Длинная цепочка"),
            ("a" * 100, True, "100 одинаковых символов"),
        ]

        edge_results = []
        print("  ДКА с одним состоянием (всегда допускает):")
        for test_str, expected, description in edge_cases:
            is_accepted, _ = dfa.validate_string(test_str)
            passed = is_accepted == expected
            edge_results.append(passed)

            status = "✓" if passed else "✗"
            print(f"    {status} '{test_str[:20]}{'...' if len(test_str) > 20 else ''}' -> "
                  f"{'допускается' if is_accepted else 'не допускается'} "
                  f"(ожидалось: {'допускается' if expected else 'не допускается'})")

        test_results.append({
            'name': 'Граничные случаи',
            'results': {
                'total': len(edge_cases),
                'passed': sum(edge_results),
                'failed': len(edge_results) - sum(edge_results)
            },
            'success': all(edge_results)
        })

        # Итоговая статистика
        print("\n" + "=" * 80)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 80)

        total_tests = len(test_results)
        passed_tests = sum(1 for tr in test_results if tr['success'])
        failed_tests = total_tests - passed_tests

        print(f"Всего тестовых групп: {total_tests}")
        print(f"Успешно пройдено: {passed_tests}")
        print(f"Не пройдено: {failed_tests}")

        if failed_tests == 0:
            print("\n*Good* ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print("\n*Bad* НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ:")
            for tr in test_results:
                if not tr['success']:
                    print(f"  - {tr['name']}")

        # Детальная статистика
        print("\nДЕТАЛЬНАЯ СТАТИСТИКА:")
        print("-" * 80)

        for tr in test_results:
            status = "*Good*" if tr['success'] else "*Bad*"
            print(f"{status} {tr['name']}")

            if 'total' in tr['results']:
                print(f"    Обработано цепочек: {tr['results']['total']}")
            if 'errors' in tr['results']:
                print(f"    Ошибок: {tr['results']['errors']}")
            if 'accepted' in tr['results']:
                print(f"    Допущено: {tr['results']['accepted']}, Отвергнуто: {tr['results']['rejected']}")
            if 'avg_time' in tr['results']:
                print(f"    Среднее время: {tr['results']['avg_time']:.4f} сек")
            if 'passed' in tr['results']:
                print(f"    Пройдено тестов: {tr['results']['passed']}/{tr['results']['total']}")

            print()

    finally:
        # Очистка временных файлов
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except:
                pass  # Игнорируем ошибки при удалении

        print(f"Очищено временных файлов: {len(temp_files)}")


def run_stress_test():
    """Запуск нагрузочного тестирования"""
    print("\n" + "=" * 80)
    print("НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ ДКА")
    print("=" * 80)

    temp_files = []

    try:
        # Создаем несколько ДКА разной сложности
        dfas = []

        print("Создание тестовых ДКА...")
        for i in range(5):
            num_states = random.randint(5, 15)
            alphabet_size = random.randint(2, 5)
            alphabet = [chr(ord('a') + j) for j in range(alphabet_size)]

            csv_path, description = create_test_dfa(num_states=num_states, alphabet=alphabet)
            temp_files.append(csv_path)

            try:
                dfa = DFA(csv_path)
                dfas.append({
                    'dfa': dfa,
                    'description': description,
                    'name': f'ДКА #{i + 1}'
                })
                print(f"  Создан {dfas[-1]['name']}: {num_states} состояний, алфавит {alphabet}")
            except Exception as e:
                print(f"  Ошибка при создании ДКА #{i + 1}: {e}")

        if not dfas:
            print("*bad* Не удалось создать ни одного ДКА для тестирования")
            return

        # Генерируем тестовые строки
        print("\nГенерация тестовых строк...")
        all_test_strings = []

        for dfa_info in dfas:
            dfa = dfa_info['dfa']
            test_strings = generate_test_strings(
                dfa.alphabet,
                num_strings=100,
                min_length=0,
                max_length=50
            )
            all_test_strings.append((dfa_info, test_strings))
            print(f"  Для {dfa_info['name']} сгенерировано {len(test_strings)} строк")

        # Запускаем тестирование
        print("\nЗапуск нагрузочного тестирования...")
        start_time = time.time()

        results = []
        total_strings = 0
        total_errors = 0

        for dfa_info, test_strings in all_test_strings:
            dfa = dfa_info['dfa']
            dfa_start = time.time()

            dfa_results = {
                'accepted': 0,
                'rejected': 0,
                'errors': 0,
                'total': len(test_strings)
            }

            for test_str in test_strings:
                try:
                    is_accepted, _ = dfa.validate_string(test_str)
                    if is_accepted:
                        dfa_results['accepted'] += 1
                    else:
                        dfa_results['rejected'] += 1
                except Exception:
                    dfa_results['errors'] += 1

            dfa_time = time.time() - dfa_start

            results.append({
                'name': dfa_info['name'],
                'results': dfa_results,
                'time': dfa_time,
                'strings_per_second': dfa_results['total'] / dfa_time if dfa_time > 0 else 0
            })

            total_strings += dfa_results['total']
            total_errors += dfa_results['errors']

        total_time = time.time() - start_time

        # Вывод результатов
        print("\nРЕЗУЛЬТАТЫ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ:")
        print("-" * 80)

        print(f"Всего ДКА: {len(dfas)}")
        print(f"Всего цепочек: {total_strings}")
        print(f"Общее время: {total_time:.2f} сек")
        print(f"Средняя скорость: {total_strings / total_time:.1f} цеп./сек")
        print(f"Всего ошибок: {total_errors}")

        print("\nРезультаты по ДКА:")
        for result in results:
            status = "good" if result['results']['errors'] == 0 else "⚠bad" if result['results']['errors'] < 5 else "*bad*"
            print(f"{status} {result['name']}:")
            print(f"    Цепочек: {result['results']['total']}, Ошибок: {result['results']['errors']}")
            print(f"    Допущено: {result['results']['accepted']}, Отвергнуто: {result['results']['rejected']}")
            print(f"    Время: {result['time']:.2f} сек, Скорость: {result['strings_per_second']:.1f} цеп./сек")

        # Оценка производительности
        print("\nОЦЕНКА ПРОИЗВОДИТЕЛЬНОСТИ:")
        print("-" * 80)

        if total_errors == 0:
            print("*good* Ошибок не обнаружено")
        else:
            error_rate = total_errors / total_strings * 100
            print(f"*bad*  Обнаружено ошибок: {total_errors} ({error_rate:.2f}%)")

        avg_speed = total_strings / total_time
        if avg_speed > 1000:
            print(f"🚀 Отличная производительность: {avg_speed:.1f} цеп./сек")
        elif avg_speed > 100:
            print(f"*Good* Хорошая производительность: {avg_speed:.1f} цеп./сек")
        else:
            print(f"️*Bad*  Средняя производительность: {avg_speed:.1f} цеп./сек")

    finally:
        # Очистка временных файлов
        for file_path in temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except:
                pass

        print(f"\nОчищено временных файлов: {len(temp_files)}")


def main():
    """Основная функция"""
    print("МАССОВОЕ ТЕСТИРОВАНИЕ ДЕТЕРМИНИРОВАННОГО КОНЕЧНОГО АВТОМАТА")
    print("=" * 80)

    print("Выберите тип тестирования:")
    print("1. Комплексное тестирование (рекомендуется)")
    print("2. Нагрузочное тестирование")
    print("3. Быстрое тестирование")
    print("4. Выход")

    try:
        choice = input("\nВведите номер (1-4): ").strip()

        if choice == '1':
            run_comprehensive_tests()
        elif choice == '2':
            run_stress_test()
        elif choice == '3':
            print("\nЗапуск быстрого тестирования...")
            # Используем простой ДКА для быстрого теста
            simple_dfa = """,a,b,Final
q0,q1,q0,0
q1,q1,q2,0
q2,q1,q0,1"""

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
                f.write(simple_dfa)
                simple_csv = f.name

            try:
                dfa = DFA(simple_csv)
                test_strings = generate_test_strings(['a', 'b'], num_strings=20)
                results = run_dfa_test(dfa, test_strings)

                print(f"Протестировано цепочек: {results['total']}")
                print(f"Допущено: {results['accepted']}, Отвергнуто: {results['rejected']}")
                print(f"Ошибок: {results['errors']}")

                if results['errors'] == 0:
                    print("*Good* Быстрое тестирование пройдено успешно!")
                else:
                    print("*Bad* В быстром тестировании обнаружены ошибки")
            finally:
                if os.path.exists(simple_csv):
                    os.unlink(simple_csv)
        elif choice == '4':
            print("Выход...")
        else:
            print("Неверный выбор. Запуск комплексного тестирования по умолчанию...")
            run_comprehensive_tests()

    except KeyboardInterrupt:
        print("\n\nТестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении тестирования: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()