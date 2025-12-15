
import csv
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Set
from graphviz import Digraph


# 1. ГРАММАТИКА В НОРМАЛЬНОЙ ФОРМЕ ХОМСКОГО (CNF)

@dataclass
class Grammar:
    start: str
    productions: Dict[str, List[Tuple[str, ...]]]  # left -> list of right parts (tuples)


# 2. PDA представление

@dataclass
class PDA:
    states: Set[str]
    start_state: str
    accept_state: str
    transitions: Dict[Tuple[str, Optional[str], str], List[Tuple[str, str]]]
    # key: (state, input_symbol_or_None_for_epsilon, stack_top)
    # value: list of (next_state, push_string) where push_string is appended (no reversal)


# 3. Преобразование CNF-gram -> PDA (стандартная конструкция)
def grammar_to_pda(g: Grammar) -> PDA:
    """
    Преобразует грамматику в НФХ (CNF) в PDA с допуском по пустому стеку (реализуем как переход в q2 при удалении Z).
    Важные соглашения:
      - Стек представлен строкой, где последний символ - вершина.
      - 'Z' - символ дна стека.
      - push_string записывается как последовательность символов, которые добавляются к стеку после POP.
        Например, для A -> BC мы хотим после POP(A) получить ... + "CB" (т.е. B будет вершиной).
    """
    states = {"q0", "q1", "q2"}
    start_state = "q0"
    accept_state = "q2"

    transitions: Dict[Tuple[str, Optional[str], str], List[Tuple[str, str]]] = {}

    def add_transition(state: str, inp: Optional[str], top: str, next_state: str, to_push: str):
        key = (state, inp, top)
        transitions.setdefault(key, []).append((next_state, to_push))

    # Начальный переход: с q0 по ε на q1, заменяем Z на Z S (чтобы Z остался внизу, S - на вершине)
    # Т.е. POP 'Z' и PUSH 'Z' + start -> стек "...Z S" (S - вершина)
    add_transition("q0", None, "Z", "q1", "Z" + g.start)

    # Определим терминалы: символы в правых частях длины 1, которые не являются нетерминалами (не-uppercase)
    terminals: Set[str] = set()
    for A, prods in g.productions.items():
        for prod in prods:
            if len(prod) == 1:
                sym = prod[0]
                # считаем терминал, если это одиночный символ и он не заглавный (простая эвристика)
                if not (sym.isupper()):
                    terminals.add(sym)

    # Для каждого терминала a: добавляем переход считывания (q1, a, a) -> (q1, ε) (т.е. убрать терминал с вершины и прочитать его)
    for a in terminals:
        add_transition("q1", a, a, "q1", "")  # "" — означает никаких push (т.е. просто POP)

    # Для каждой продукции:
    # A -> BC  : (q1, ε, A) -> (q1, CB)  (POP A, PUSH C then B; B будет вершиной)
    # A -> a   : (q1, ε, A) -> (q1, a)   (POP A, PUSH terminal a)
    for A, prods in g.productions.items():
        for prod in prods:
            if len(prod) == 2:
                B, C = prod
                # Проверяем, что B и C — нетерминалы (в CNF)
                add_transition("q1", None, A, "q1", C + B)
            elif len(prod) == 1:
                a = prod[0]
                # Если это терминал (a), то заменяем A на a на стеке
                add_transition("q1", None, A, "q1", a)
            else:
                # Неожиданный формат — игнорируем (CNF предполагает длину 1 или 2)
                continue

    # Переход в принимающее состояние: если на вершине Z и вход пуст, POP Z и перейти в q2
    # Реализуем как (q1, ε, 'Z') -> (q2, "") (удалить Z)
    add_transition("q1", None, "Z", "q2", "")

    return PDA(states, start_state, accept_state, transitions)


# 4. Симулятор PDA (с ε-замыканием и недетерминизмом)

def run_pda(pda: PDA, input_string: str, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Симулятор PDA.
    Возвращает (accepted: bool, history_lines: List[str]).
    Поддерживает:
      - ε-переходы (inp == None)
      - недетерминизм (несколько конфигураций)
      - стек как строку (последний символ - вершина)
    Условие допуска: достигнуто состояние q2, позиция == len(input_string) и стек == "" (дно Z был удалён).
    """
    history: List[str] = []

    def log(s: str):
        if verbose:
            print(s)
        history.append(s)

    log(f"Начинаем разбор: '{input_string}'")
    log("-" * 60)

    # Конфигурация: (state, pos, stack_str)
    # Начальное: q0, pos=0, стек="Z"
    active: Set[Tuple[str, int, str]] = {("q0", 0, "Z")}

    max_iterations = 10000  # защита от бесконечных циклов
    iterations = 0

    # Вспомог: применить ε-замыкание к множеству конфигураций
    def epsilon_closure(configs: Set[Tuple[str, int, str]]) -> Set[Tuple[str, int, str]]:
        stack = list(configs)
        closure = set(configs)
        while stack:
            conf = stack.pop()
            state, pos, st = conf
            top = st[-1] if st else ""  # если стек пуст, top == ""
            key = (state, None, top)
            if key in pda.transitions:
                for (nstate, push) in pda.transitions[key]:
                    # формируем новый стек: POP top, затем append push
                    if not st:
                        continue  # невозможный POP, пропускаем
                    new_stack = st[:-1] + push
                    new_conf = (nstate, pos, new_stack)
                    if new_conf not in closure:
                        closure.add(new_conf)
                        stack.append(new_conf)
        return closure

    while active and iterations < max_iterations:
        iterations += 1
        log(f"\nИтерация {iterations}, активных конфигураций: {len(active)}")
        for conf in list(active)[:5] if verbose else []:
            state, pos, st = conf
            rem = input_string[pos:] if pos < len(input_string) else "ε"
            log(f"  пример: ({state}, '{rem}', '{st}')")

        # 1) Расширяем активный набор через ε-замыкание
        closure = epsilon_closure(active)

        # Проверяем принятие прямо в ε-замыкании
        for (state, pos, st) in closure:
            if state == pda.accept_state and pos == len(input_string) and st == "":
                log(f"\n  ✓ Принято: конфигурация ({state}, pos={pos}, stack='{st}')")
                return True, history

        # 2) Пытаемся потребить один символ входа из любой конфигурации closure
        next_active: Set[Tuple[str, int, str]] = set()

        for (state, pos, st) in closure:
            if pos >= len(input_string):
                continue  # нечего читать
            ch = input_string[pos]
            top = st[-1] if st else ""
            key = (state, ch, top)
            if key in pda.transitions:
                for (nstate, push) in pda.transitions[key]:
                    # POP топ, затем PUSH push
                    if not st:
                        continue
                    new_stack = st[:-1] + push
                    new_conf = (nstate, pos + 1, new_stack)
                    next_active.add(new_conf)
                    if verbose:
                        log(f"    δ({state}, '{ch}', {top}) -> ({nstate}, '{push}') => ({nstate}, pos={pos+1}, stack='{new_stack}')")

        # Обновляем активные конфигурации как next_active.
        active = next_active

    # после цикла: проверьем финальные состояния (на случай, если итерации истекли)
    closure = epsilon_closure(active)
    for (state, pos, st) in closure:
        if state == pda.accept_state and pos == len(input_string) and st == "":
            log(f"\n  ✓ Принято: ({state}, pos={pos}, stack='{st}')")
            return True, history

    log("\n  ✗ Отказано")
    if verbose:
        log(f"  Итераций: {iterations}")
        log(f"  Оставшиеся конфигурации: {len(active)}")
        for (s, p, st) in active:
            rem = input_string[p:] if p < len(input_string) else "ε"
            log(f"    ({s}, '{rem}', '{st}')")

    return False, history


# 5. Поиск подстроки: проверяем все префиксы суффикса
def pda_find_substring(pda: PDA, text: str, verbose: bool = False) -> List[int]:
    """
    Для каждой позиции i в тексте пробуем все префиксы текста[i:j].
    Если хоть один префикс принимается PDA, считаем, что с позиции i начинается подходящая подстрока.
    Возвращаем список позиций (начал подстрок).
    """
    positions: List[int] = []
    if verbose:
        print(f"\nПоиск подстрок в тексте: '{text}'")

    n = len(text)
    for i in range(n):
        found = False
        # пробуем все конечные позиции j > i
        for j in range(i + 1, n + 1):
            substr = text[i:j]
            accepted, _ = run_pda(pda, substr, verbose=False)
            if accepted:
                positions.append(i)
                found = True
                if verbose:
                    print(f"  ✓ позиция {i}: найдено '{substr}'")
                break
        if verbose and not found:
            print(f"  ✗ позиция {i}: никаких подходящих префиксов")
    if verbose:
        print(f"Итого найдено позиций: {len(positions)} -> {positions}")
    return positions


# 6. ТЕСТЫ

def run_tests():
    print("ЗАПУСК ТЕСТОВ")
    print("=" * 60)

    all_passed = True

    # Тест 1: Простая грамматика S → AB, A → a, B → b (генерирует 'ab')
    print("\n1) Тест простая грамматика (S -> AB, A->a, B->b):")
    grammar1 = Grammar(
        start="S",
        productions={
            "S": [("A", "B")],
            "A": [("a",)],
            "B": [("b",)]
        }
    )
    pda1 = grammar_to_pda(grammar1)

    print("\n   Проверка отдельных строк с verbose:")
    res, _ = run_pda(pda1, "ab", verbose=True)
    print(f"   'ab' -> {'ПРИНЯТО' if res else 'ОТВЕРГНУТО'}")
    res2, _ = run_pda(pda1, "a", verbose=True)
    print(f"   'a'  -> {'ПРИНЯТО' if res2 else 'ОТВЕРГНУТО'}")

    test_cases = [
        ("ab", True, "правильная строка 'ab'"),
        ("a", False, "только 'a' - неполная"),
        ("b", False, "только 'b'"),
        ("", False, "пустая строка"),
        ("aba", False, "лишний символ в конце"),
    ]
    for s, expected, desc in test_cases:
        got = run_pda(pda1, s, verbose=False)[0]
        if got == expected:
            print(f"  ✓ '{s}': {desc}")
        else:
            print(f"  ✗ '{s}': {desc}. Ожидалось {expected}, получили {got}")
            all_passed = False

    # Поиск подстрок: у нас грамматика распознаёт 'ab', поэтому на тексте 'xxabxabxxaba'
    # ожидаем позиции 2 и 5 (там начинаются 'ab')
    print("\n   Тест поиска подстрок для grammar1 в 'xxabxabxxaba':")
    positions = pda_find_substring(pda1, "xxabxabxxaba", verbose=True)
    expected_positions = [2, 5]
    if positions == expected_positions:
        print("  ✓ Поиск подстрок - OK")
    else:
        print(f"  ✗ Поиск подстрок - ожидалось {expected_positions}, получили {positions}")
        all_passed = False

    # Тест 2: Грамматика a^n b^n в CNF (S -> X S1 | X Y ; S1 -> S Y ; X->a ; Y->b)
    # Эта грамматика генерирует a^n b^n для n>=1
    print("\n2) Тест грамматики a^n b^n (n=1,2):")
    grammar2 = Grammar(
        start="S",
        productions={
            "S": [("X", "S1"), ("X", "Y")],
            "S1": [("S", "Y")],
            "X": [("a",)],
            "Y": [("b",)]
        }
    )
    pda2 = grammar_to_pda(grammar2)

    test_cases2 = [
        ("ab", True, "a^1 b^1"),
        ("aabb", True, "a^2 b^2"),
        ("a", False, "только 'a'"),
        ("abb", False, "не парное кол-во"),
    ]
    for s, expected, desc in test_cases2:
        got = run_pda(pda2, s, verbose=False)[0]
        if got == expected:
            print(f"  ✓ '{s}': {desc}")
        else:
            print(f"  ✗ '{s}': {desc}. Ожидалось {expected}, получили {got}")
            all_passed = False

    # Тест 3: язык 'ab' или 'cd'
    print("\n3) Тест языка 'ab' или 'cd':")
    grammar3 = Grammar(
        start="S",
        productions={
            "S": [("A", "B"), ("C", "D")],
            "A": [("a",)],
            "B": [("b",)],
            "C": [("c",)],
            "D": [("d",)]
        }
    )
    pda3 = grammar_to_pda(grammar3)
    test_cases3 = [
        ("ab", True, "ab"),
        ("cd", True, "cd"),
        ("a", False, "только a"),
    ]
    for s, expected, desc in test_cases3:
        got = run_pda(pda3, s, verbose=False)[0]
        if got == expected:
            print(f"  ✓ '{s}': {desc}")
        else:
            print(f"  ✗ '{s}': {desc}. Ожидалось {expected}, получили {got}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("good!")
    else:
        print("ok")

    return all_passed


# 7. Демонстрационный режим (упрощённый)
def demonstration_mode():
    print("\n" + "=" * 60)
    print("ДЕМОНСТРАЦИЯ")
    print("=" * 60)
    grammar = Grammar(
        start="S",
        productions={
            "S": [("A", "B")],
            "A": [("a",)],
            "B": [("b",)]
        }
    )
    pda = grammar_to_pda(grammar)

    options = {
        "1": ("Анализ 'ab'", "ab"),
        "2": ("Анализ 'a'", "a"),
        "3": ("Поиск подстрок 'xxabxab'", "xxabxab")
    }

    while True:
        print("\nВыберите действие:")
        print("1 - Проанализировать 'ab'")
        print("2 - Проанализировать 'a'")
        print("3 - Найти подстроки в 'xxabxab'")
        print("4 - Показать таблицу переходов")
        print("5 - Выйти")
        choice = input("Ваш выбор: ").strip()
        if choice == "1" or choice == "2":
            _, s = options[choice]
            run_pda(pda, s, verbose=True)
        elif choice == "3":
            _, s = options["3"]
            pda_find_substring(pda, s, verbose=True)
        elif choice == "4":
            print("\nТаблица переходов PDA:")
            for (st, inp, top), lst in pda.transitions.items():
                for nst, push in lst:
                    inp_str = "ε" if inp is None else inp
                    push_str = "ε" if push == "" else push
                    print(f"δ({st},{inp_str},{top}) -> ({nst},'{push_str}')")
        elif choice == "5":
            break
        else:
            print("Неверно. Попробуйте снова.")


# 8. Визуализация (по желанию)
def visualize_pda(pda: PDA, filename="pda"):
    dot = Digraph()
    dot.attr(rankdir='LR', size='8,5')
    for state in pda.states:
        if state == pda.accept_state:
            dot.node(state, shape='doublecircle', style='filled', color='lightgreen')
        elif state == pda.start_state:
            dot.node(state, shape='circle', style='filled', color='lightblue')
        else:
            dot.node(state, shape='circle')
    for (st, inp, top), lst in pda.transitions.items():
        for nst, push in lst:
            label = f"{inp if inp is not None else 'ε'}; {top} → {push if push != '' else 'ε'}"
            dot.edge(st, nst, label=label)
    dot.render(filename, format='png', cleanup=True)
    print(f"Граф сохранён: {filename}.png")


# 9. Экспорт переходов в CSV
def export_pda_csv(pda: PDA, filename="pda_transitions.csv"):
    with open(filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["state", "input", "stack_top", "next_state", "push"])
        for (state, inp, top), lst in pda.transitions.items():
            for next_state, push in lst:
                inp_str = "ε" if inp is None else inp
                push_str = "ε" if push == "" else push
                writer.writerow([state, inp_str, top, next_state, push_str])
    print(f"Экспорт завершён: {filename}")


# 10. Главное меню
def main():
    print("=" * 60)
    print("ИНТЕРПРЕТАТОР НФХ-ГРАММАТИК И PDA")
    print("=" * 60)
    while True:
        print("\nМеню:")
        print("1 - Запустить тесты")
        print("2 - Демонстрационный режим")
        print("3 - Визуализировать демонстрационный PDA")
        print("4 - Экспорт переходов демонстрационного PDA в CSV")
        print("5 - Выход")
        choice = input("Выберите пункт: ").strip()
        if choice == "1":
            run_tests()
        elif choice == "2":
            demonstration_mode()
        elif choice == "3":
            grammar = Grammar(start="S", productions={"S": [("A", "B")], "A": [("a",)], "B": [("b",)]})
            pda = grammar_to_pda(grammar)
            visualize_pda(pda, "pda_demo")
        elif choice == "4":
            grammar = Grammar(start="S", productions={"S": [("A", "B")], "A": [("a",)], "B": [("b",)]})
            pda = grammar_to_pda(grammar)
            export_pda_csv(pda, "pda_demo_transitions.csv")
        elif choice == "5":
            print("Выход.")
            break
        else:
            print("Неверный пункт. Попробуйте снова.")


if __name__ == "__main__":
    main()



# import csv
# from dataclasses import dataclass
# from typing import List, Tuple, Dict, Optional, Set
# from graphviz import Digraph
#
#
# # 1. ГРАММАТИКА В НОРМАЛЬНОЙ ФОРМЕ ХОМСКОГО
#
# @dataclass
# class Grammar:
#     start: str
#     productions: Dict[str, List[Tuple[str, ...]]]
#
#
# # 2. КОРРЕКТНАЯ ПРОЕКЦИЯ ГРАММАТИКИ НА PDA
#
# @dataclass
# class PDA:
#     states: Set[str]
#     start_state: str
#     accept_state: str
#     transitions: Dict[Tuple[str, Optional[str], str], List[Tuple[str, str]]]
#
#
# def grammar_to_pda(g: Grammar) -> PDA:
#     states = {"q0", "q1", "q2"}
#     start_state = "q0"
#     accept_state = "q2"
#
#     transitions = {}
#
#     def add_transition(state, inp, top, next_state, to_push):
#         key = (state, inp, top)
#         if key not in transitions:
#             transitions[key] = []
#         transitions[key].append((next_state, to_push))
#
#     # 1. Переход из начального состояния: кладем S и маркер дна Z в стек
#     # Z - символ дна стека. g.start - стартовый нетерминал.
#     # q0 - начальное состояние, q1 - рабочее.
#     add_transition("q0", None, "Z", "q1", g.start + "Z")
#
#     # Собираем все терминалы из грамматики
#     terminals = set()
#     for A, prods in g.productions.items():
#         for prod in prods:
#             if len(prod) == 1 and prod[0].islower(): # Предполагаем, что терминалы - строчные буквы
#                 terminals.add(prod[0])
#             elif len(prod) == 2 and not prod[0].isupper(): # Если в A -> aB или A -> Ba, что не НФХ, но для общего случая
#                 terminals.add(prod[0])
#             elif len(prod) == 2 and not prod[1].isupper():
#                 terminals.add(prod[1])
#
#     # 2. Добавляем правила для сопоставления терминалов
#     # (q1, a, a) -> (q1, ε)
#     for terminal in terminals:
#         add_transition("q1", terminal, terminal, "q1", "") # "" означает POP, т.е. ε на стеке
#
#     # 3. Для каждого правила A → BC или A → a добавляем ε-переход
#     for A, prods in g.productions.items():
#         for prod in prods:
#             if len(prod) == 2:  # Правило вида A → BC
#                 B, C = prod
#                 # (q1, ε, A) -> (q1, CB) - POP A, PUSH C, PUSH B (B будет сверху)
#                 add_transition("q1", None, A, "q1", C + B)
#             elif len(prod) == 1:  # Правило вида A → a
#                 a = prod[0]
#                 # (q1, ε, A) -> (q1, a) - POP A, PUSH a
#                 # Это правило помещает терминал 'a' на стек, где он затем будет сопоставлен
#                 # соответствующим правилом (q1, a, a) -> (q1, ε).
#                 add_transition("q1", None, A, "q1", a)
#
#     # 4. Переход в принимающее состояние
#     # (q1, ε, Z) -> (q2, ε) - если вход пуст и стек содержит только Z (дно стека)
#     # Здесь Z удаляется со стека.
#     add_transition("q1", None, "Z", "q2", "") # Принимаем по пустому стеку (опустошенному до Z0) и концу входа
#
#     return PDA(states, start_state, accept_state, transitions)
#
#
# # 3. КОРРЕКТНЫЙ СИМУЛЯТОР PDA
#
#
# def run_pda(pda: PDA, input_string: str, verbose: bool = False) -> Tuple[bool, List[str]]:
#     history = []
#
#     def log(msg):
#         if verbose:
#             print(msg)
#         history.append(msg)
#
#     log(f"Начинаем анализ строки: '{input_string}'")
#     log("=" * 50)
#
#     # Конфигурация: (состояние, позиция_входа, строка_стека)
#     # Используем set для configs для автоматического удаления дубликатов и быстрого поиска
#     # Стек должен быть хешируемым, поэтому string - это хорошо.
#     active_configs: Set[Tuple[str, int, str]] = set()
#     # Начальная конфигурация: q0, позиция 0, Z (дно стека)
#     active_configs.add(("q0", 0, "Z"))
#
#     # Для предотвращения зацикливания на ε-переходах:
#     # Множество всех конфигураций, которые были посещены на данном шаге
#     # (state, pos, stack)
#     visited_in_step: Set[Tuple[str, int, str]] = set()
#
#     step = 0
#     max_steps = 2 * len(input_string) + 100 # Увеличим лимит шагов
#
#     while active_configs and step < max_steps:
#         step += 1
#         log(f"\nШаг {step}:")
#
#         # Набор для конфигураций следующего шага
#         # (в него добавляются все новые конфигурации после обработки текущих)
#         next_configs_from_input_read = set()
#         next_configs_from_epsilon = set() # Отдельно для ε-переходов, чтобы обрабатывать их итеративно
#
#         processed_this_iteration = set() # Чтобы не обрабатывать одну и ту же конфиг. несколько раз на одном шаге
#
#         # Сначала обрабатываем все возможные ε-переходы для текущего набора configs
#         # пока не появятся новые ε-переходы
#         current_epsilon_round_configs = set(active_configs) # Начинаем с текущих
#         while current_epsilon_round_configs:
#             epsilon_configs_to_process = set(current_epsilon_round_configs)
#             current_epsilon_round_configs.clear() # Очищаем для следующей итерации ε-переходов
#
#             for state, pos, stack in epsilon_configs_to_process:
#                 # Если эта конфигурация уже была полностью обработана в этом шаге, пропускаем
#                 if (state, pos, stack) in processed_this_iteration:
#                     continue
#                 processed_this_iteration.add((state, pos, stack))
#
#                 remaining = input_string[pos:] if pos < len(input_string) else "ε"
#                 log(f"  Обработка ε-конфигурации: ({state}, '{remaining}', '{stack}')")
#
#                 top = stack[-1] if stack else "" # Вершина стека или пустая строка если стек пуст
#
#                 # Пробуем ε-переходы (без чтения входного символа)
#                 ε_key = (state, None, top)
#                 if ε_key in pda.transitions:
#                     for next_state, push in pda.transitions[ε_key]:
#                         # Формируем новый стек (строка)
#                         if push == "": # POP
#                             new_stack = stack[:-1]
#                         else: # POP и PUSH
#                             # push[::-1] - это уже правильный порядок, так как мы хотим, чтобы первый символ
#                             # из 'push' оказался на вершине стека после POP.
#                             # Если push == "CB", то stack[:-1] + "BC" будет означать PUSH C, PUSH B (B сверху).
#                             new_stack = stack[:-1] + push[::-1]
#
#                         new_conf = (next_state, pos, new_stack)
#                         if new_conf not in active_configs and new_conf not in next_configs_from_input_read and new_conf not in next_configs_from_epsilon:
#                             current_epsilon_round_configs.add(new_conf) # Добавляем для дальнейшей обработки ε-переходов
#                             next_configs_from_epsilon.add(new_conf) # Добавляем в общий список для следующего шага
#                             log(f"    ε-переход: δ({state}, ε, {top}) → ({next_state}, {push}) -> {new_conf}")
#                 else:
#                     # Если ε-переходов нет, эта конфигурация готова для обработки входного символа
#                     next_configs_from_input_read.add((state, pos, stack))
#
#
#         # Теперь обрабатываем все конфигурации, которые могут потреблять входной символ
#         for state, pos, stack in next_configs_from_input_read:
#             remaining = input_string[pos:] if pos < len(input_string) else "ε"
#             log(f"  Обработка конфигурации с чтением: ({state}, '{remaining}', '{stack}')")
#
#             # Получаем вершину стека
#             top = stack[-1] if stack else ""
#
#             # Пробуем переходы по входному символу
#             if pos < len(input_string):
#                 current_char = input_string[pos]
#                 char_key = (state, current_char, top)
#                 if char_key in pda.transitions:
#                     for next_state, push in pda.transitions[char_key]:
#                         if push == "":
#                             new_stack = stack[:-1]
#                         else:
#                             new_stack = stack[:-1] + push[::-1] # POP и PUSH
#                         new_configs = (next_state, pos + 1, new_stack)
#                         if new_configs not in next_configs_from_epsilon and new_configs not in active_configs:
#                             next_configs_from_epsilon.add(new_configs) # Добавляем в набор для следующего шага
#                             log(f"    Переход: δ({state}, '{current_char}', {top}) → ({next_state}, {push}) -> {new_configs}")
#
#
#         # Объединяем все конфигурации для следующего шага
#         active_configs.clear()
#         active_configs.update(next_configs_from_epsilon)
#         # Если в next_configs_from_input_read были конфиги, которые не совершили переходов,
#         # они "умирают", т.к. не нашли продолжения.
#
#     # После завершения цикла (нет больше активных конфигураций или превышен лимит шагов)
#     # проверяем, есть ли хоть одна допускающая конфигурация.
#     log(f"\n  Завершение симуляции. Проверка допуска.")
#     for state, pos, stack in active_configs:
#         log(f"  Финал. конфигурация: ({state}, '{input_string[pos:] if pos < len(input_string) else 'ε'}', '{stack}')")
#         # Условие допуска: достигнуто принимающее состояние (q2), вся строка прочитана,
#         # и стек пуст (символ дна стека Z удален, т.е. stack == "")
#         if state == pda.accept_state and pos == len(input_string) and stack == "":
#             log(f"  ✓ Строка '{input_string}' ПРИНЯТА!")
#             return True, history
#
#     log(f"\n  ✗ Строка '{input_string}' ОТВЕРГНУТА")
#     return False, history
#
#
#
# # 4. ПОИСК ПОДСТРОК
#
# def pda_find_substring(pda: PDA, text: str, verbose: bool = False) -> List[int]:
#     """
#     Находит все позиции в тексте, с которых начинаются подстроки,
#     принимаемые PDA.
#     """
#     positions = []
#
#     if verbose:
#         print(f"\nПоиск подстрок в тексте: '{text}'")
#         print("=" * 60)
#
#     for i in range(len(text)):
#         substring = text[i:]
#         accepted, history = run_pda(pda, substring, verbose=False)
#
#         if accepted:
#             positions.append(i)
#             if verbose:
#                 print(f"  ✓ Позиция {i}: '{substring}' - ПРИНЯТА")
#         elif verbose:
#             print(f"  ✗ Позиция {i}: '{substring}' - отвергнута")
#
#     if verbose:
#         print(f"\nИтого найдено: {len(positions)} подстрок")
#         if positions:
#             print("Позиции:", positions)
#             for pos in positions:
#                 end = min(pos + 10, len(text))
#                 print(f"  [{pos}]: '{text[pos:end]}'")
#
#     return positions
#
#
# # 5. ТЕСТЫ
#
# def run_tests():
#     """Корректные тесты"""
#     print("ЗАПУСК ТЕСТОВ")
#     print("=" * 60)
#
#     # Тест 1: Простая грамматика S → AB, A → a, B → b
#     print("\n1. Тест простой грамматики (S → AB, A → a, B → b):")
#     grammar1 = Grammar(
#         start="S",
#         productions={
#             "S": [("A", "B")],
#             "A": [("a",)],
#             "B": [("b",)]
#         }
#     )
#
#     pda1 = grammar_to_pda(grammar1)
#
#     # Тестируем с детальным выводом для отладки
#     print("\n   Тестируем строку 'ab':")
#     result1, _ = run_pda(pda1, "ab", verbose=True)
#     print(f"   Результат: {'ПРИНЯТО' if result1 else 'ОТВЕРГНУТО'}")
#
#     print("\n   Тестируем строку 'a':")
#     result2, _ = run_pda(pda1, "a", verbose=True)
#     print(f"   Результат: {'ПРИНЯТО' if result2 else 'ОТВЕРГНУТО'}")
#
#     # Быстрые тесты
#     test_cases = [
#         ("ab", True, "Корректная строка 'ab'"),
#         ("a", False, "Только 'a' - неполная строка"),
#         ("b", False, "Только 'b' - неполная строка"),
#         ("", False, "Пустая строка"),
#         ("aba", False, "Лишний 'a' в конце"),
#     ]
#
#     all_passed = True
#     for test_str, expected, description in test_cases:
#         result = run_pda(pda1, test_str, verbose=False)[0]
#         if result == expected:
#             print(f"  ✓ '{test_str}': {description}")
#         else:
#             print(f"  ✗ '{test_str}': {description}")
#             print(f"    Ожидалось: {'ПРИНЯТО' if expected else 'ОТВЕРГНУТО'}")
#             print(f"    Получено: {'ПРИНЯТО' if result else 'ОТВЕРГНУТО'}")
#             all_passed = False
#
#     # Тест поиска подстрок
#     print("\n2. Тест поиска подстрок в 'xxabxabxxaba':")
#     positions = pda_find_substring(pda1, "xxabxabxxaba", verbose=True)
#
#     # Должны найти "ab" на позициях 2 и 5
#     expected_positions = [2, 5]
#
#     if positions == expected_positions:
#         print(f"  ✓ Поиск подстрок пройден: найдены позиции {positions}")
#     else:
#         print(f"  ✗ Поиск подстрок не пройден")
#         print(f"    Ожидалось: {expected_positions}")
#         print(f"    Получено: {positions}")
#         all_passed = False
#
#     # Тест 2: Грамматика для a^n b^n
#     print("\n3. Тест грамматики aⁿbⁿ (для n=1,2):")
#     grammar2 = Grammar(
#         start="S",
#         productions={
#             "S": [("A", "B")],
#             "A": [("a", "S"), ("a",)],
#             "B": [("b",)]
#         }
#     )
#
#     pda2 = grammar_to_pda(grammar2)
#
#     test_cases2 = [
#         ("ab", True, "a¹b¹"),
#         ("aabb", True, "a²b²"),
#         ("a", False, "Только 'a'"),
#         ("abb", False, "Не хватает 'a'"),
#     ]
#
#     for test_str, expected, description in test_cases2:
#         result = run_pda(pda2, test_str, verbose=False)[0]
#         if result == expected:
#             print(f"  ✓ '{test_str}': {description}")
#         else:
#             print(f"  ✗ '{test_str}': {description}")
#             all_passed = False
#
#     # Тест 3: Грамматика для языка "ab" или "cd"
#     print("\n4. Тест грамматики 'ab' или 'cd':")
#     grammar3 = Grammar(
#         start="S",
#         productions={
#             "S": [("A", "B"), ("C", "D")],
#             "A": [("a",)],
#             "B": [("b",)],
#             "C": [("c",)],
#             "D": [("d",)]
#         }
#     )
#
#     pda3 = grammar_to_pda(grammar3)
#
#     test_cases3 = [
#         ("ab", True, "Строка 'ab'"),
#         ("cd", True, "Строка 'cd'"),
#         ("a", False, "Только 'a'"),
#     ]
#
#     for test_str, expected, description in test_cases3:
#         result = run_pda(pda3, test_str, verbose=False)[0]
#         if result == expected:
#             print(f"  ✓ '{test_str}': {description}")
#         else:
#             print(f"  ✗ '{test_str}': {description}")
#             all_passed = False
#
#     print("\n" + "=" * 60)
#     if all_passed:
#         print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
#     else:
#         print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
#
#     return all_passed
#
#
# # 6. ДЕМОНСТРАЦИОННЫЙ РЕЖИМ
#
# def demonstration_mode():
#     """Демонстрация работы PDA с пошаговым выводом"""
#     print("\n" + "=" * 60)
#     print("ДЕМОНСТРАЦИОННЫЙ РЕЖИМ")
#     print("=" * 60)
#
#     print("\n1. Создаем грамматику S → AB, A → a, B → b")
#     print("   Эта грамматика порождает только строку 'ab'")
#
#     grammar = Grammar(
#         start="S",
#         productions={
#             "S": [("A", "B")],
#             "A": [("a",)],
#             "B": [("b",)]
#         }
#     )
#
#     pda = grammar_to_pda(grammar)
#
#     while True:
#         print("\n" + "-" * 60)
#         print("Выберите демонстрацию:")
#         print("1. Проанализировать строку 'ab' (ожидается: ПРИНЯТО)")
#         print("2. Проанализировать строку 'a' (ожидается: ОТВЕРГНУТО)")
#         print("3. Проанализировать строку 'ba' (ожидается: ОТВЕРГНУТО)")
#         print("4. Найти подстроки в тексте 'xxabxab'")
#         print("5. Показать таблицу переходов PDA")
#         print("6. Вернуться в главное меню")
#
#         choice = input("\nВаш выбор (1-6): ").strip()
#
#         if choice == "1":
#             print("\n" + "=" * 60)
#             print("АНАЛИЗ СТРОКИ 'ab' (ожидается: ПРИНЯТО)")
#             print("=" * 60)
#             result, history = run_pda(pda, "ab", verbose=True)
#
#         elif choice == "2":
#             print("\n" + "=" * 60)
#             print("АНАЛИЗ СТРОКИ 'a' (ожидается: ОТВЕРГНУТО)")
#             print("=" * 60)
#             result, history = run_pda(pda, "a", verbose=True)
#
#         elif choice == "3":
#             print("\n" + "=" * 60)
#             print("АНАЛИЗ СТРОКИ 'ba' (ожидается: ОТВЕРГНУТО)")
#             print("=" * 60)
#             result, history = run_pda(pda, "ba", verbose=True)
#
#         elif choice == "4":
#             print("\n" + "=" * 60)
#             print("ПОИСК ПОДСТРОК В ТЕКСТЕ 'xxabxab'")
#             print("=" * 60)
#             print("Ожидаем найти подстроки 'ab' на позициях 2 и 5")
#             positions = pda_find_substring(pda, "xxabxab", verbose=True)
#
#         elif choice == "5":
#             print("\nТАБЛИЦА ПЕРЕХОДОВ PDA:")
#             print("=" * 60)
#             for (state, inp, top), lst in pda.transitions.items():
#                 for next_state, push in lst:
#                     inp_str = "ε" if inp is None else inp
#                     print(f"δ({state}, {inp_str}, {top}) → ({next_state}, '{push}')")
#
#         elif choice == "6":
#             break
#
#         else:
#             print("Неверный выбор, попробуйте снова")
#
#
# # 7. СОЗДАНИЕ ГРАММАТИКИ ПОЛЬЗОВАТЕЛЕМ
#
# def create_grammar_mode():
#     """Режим создания собственной грамматики"""
#     print("\n" + "=" * 60)
#     print("СОЗДАНИЕ СОБСТВЕННОЙ ГРАММАТИКИ")
#     print("=" * 60)
#
#     print("\nПример грамматики в НФХ:")
#     print("  S → AB    (два нетерминала)")
#     print("  A → a     (один терминал)")
#     print("  B → b     (один терминал)")
#
#     productions = {}
#
#     print("\nВведите стартовый символ (например, 'S'):")
#     start = input().strip()
#
#     print("\nВводите правила построчно. Формат: 'A → BC' или 'A → a'")
#     print("Для завершения введите 'готово'")
#
#     while True:
#         rule = input("\nПравило: ").strip()
#
#         if rule.lower() == 'готово':
#             break
#
#         try:
#             if '→' in rule:
#                 left, right = rule.split('→')
#             elif '->' in rule:
#                 left, right = rule.split('->')
#             else:
#                 print("Ошибка: используйте '→' или '->'")
#                 continue
#
#             left = left.strip()
#             right = right.strip()
#
#             if not left.isupper():
#                 print("Ошибка: левая часть должна быть заглавной буквой")
#                 continue
#
#             if len(right) == 2 and right[0].isupper() and right[1].isupper():
#                 # Два нетерминала
#                 if left not in productions:
#                     productions[left] = []
#                 productions[left].append((right[0], right[1]))
#                 print(f"Добавлено правило: {left} → {right[0]}{right[1]}")
#             elif len(right) == 1 and right.islower():
#                 # Один терминал
#                 if left not in productions:
#                     productions[left] = []
#                 productions[left].append((right,))
#                 print(f"Добавлено правило: {left} → {right}")
#             else:
#                 print("Ошибка: правая часть должна быть либо 2 заглавные буквы, либо 1 строчная")
#                 continue
#
#         except Exception as e:
#             print(f"Ошибка при разборе правила: {e}")
#
#     if not productions:
#         print("\nИспользуем демонстрационную грамматику")
#         grammar = Grammar(
#             start="S",
#             productions={
#                 "S": [("A", "B")],
#                 "A": [("a",)],
#                 "B": [("b",)]
#             }
#         )
#     else:
#         grammar = Grammar(start=start, productions=productions)
#
#     pda = grammar_to_pda(grammar)
#
#     print("\n" + "=" * 60)
#     print("СОЗДАНА ГРАММАТИКА:")
#     for nt, prods in grammar.productions.items():
#         prod_str = " | ".join(["".join(p) for p in prods])
#         print(f"  {nt} → {prod_str}")
#
#     while True:
#         print("\n" + "-" * 60)
#         print("МЕНЮ ГРАММАТИКИ:")
#         print("1. Протестировать строку")
#         print("2. Найти подстроки в тексте")
#         print("3. Показать таблицу переходов PDA")
#         print("4. Вернуться в главное меню")
#
#         choice = input("\nВаш выбор (1-4): ").strip()
#
#         if choice == "1":
#             test_str = input("Введите строку для тестирования: ").strip()
#             print(f"\nТестируем строку: '{test_str}'")
#             result, history = run_pda(pda, test_str, verbose=True)
#
#         elif choice == "2":
#             text = input("Введите текст для поиска подстрок: ").strip()
#             print(f"\nИщем подстроки в тексте: '{text}'")
#             positions = pda_find_substring(pda, text, verbose=True)
#             print(f"\nНайдено {len(positions)} подходящих подстрок")
#
#         elif choice == "3":
#             print("\nТАБЛИЦА ПЕРЕХОДОВ PDA:")
#             print("=" * 60)
#             for (state, inp, top), lst in pda.transitions.items():
#                 for next_state, push in lst:
#                     inp_str = "ε" if inp is None else inp
#                     print(f"δ({state}, {inp_str}, {top}) → ({next_state}, '{push}')")
#
#         elif choice == "4":
#             break
#
#         else:
#             print("Неверный выбор, попробуйте снова")
#
#
# # 8. ГРАФИЧЕСКАЯ ВИЗУАЛИЗАЦИЯ
#
# def visualize_pda(pda: PDA, filename="pda"):
#     """Создает графическое представление PDA"""
#     dot = Digraph()
#     dot.attr(rankdir='LR', size='8,5')
#
#     # Добавляем состояния
#     for state in pda.states:
#         if state == pda.accept_state:
#             dot.node(state, shape='doublecircle', style='filled', color='lightgreen')
#         elif state == pda.start_state:
#             dot.node(state, shape='circle', style='filled', color='lightblue')
#         else:
#             dot.node(state, shape='circle')
#
#     # Добавляем переходы
#     for (st, inp, top), lst in pda.transitions.items():
#         for nst, push in lst:
#             label = f"{inp if inp else 'ε'}; {top}"
#             label += f" → {push if push else 'ε'}"
#             dot.edge(st, nst, label=label)
#
#     dot.render(filename, format='png', cleanup=True)
#     print(f"\nГрафик PDA сохранен как {filename}.png")
#
#
# # 9. ЭКСПОРТ В CSV
#
# def export_pda_csv(pda: PDA, filename="pda.csv"):
#     """Экспорт переходов PDA в CSV файл"""
#     with open(filename, "w", newline='', encoding="utf-8") as f:
#         writer = csv.writer(f)
#         writer.writerow(["state", "input", "stack_top", "next_state", "push"])
#
#         for (state, inp, top), lst in pda.transitions.items():
#             for next_state, push in lst:
#                 inp_str = "ε" if inp is None else inp
#                 push_str = "ε" if push == "" else push
#                 writer.writerow([state, inp_str, top, next_state, push_str])
#
#     print(f"\nЭкспорт завершен. Файл '{filename}' создан.")
#
#
# # 10. ГЛАВНОЕ МЕНЮ
#
# def main():
#     """Главная функция программы"""
#     print("=" * 60)
#     print("ИНТЕРПРЕТАТОР НФХ-ГРАММАТИК И МАГАЗИННЫХ АВТОМАТОВ")
#     print("=" * 60)
#
#     while True:
#         print("\n" + "=" * 60)
#         print("ГЛАВНОЕ МЕНЮ:")
#         print("1. Запустить тесты")
#         print("2. Демонстрационный режим")
#         print("3. Создать свою грамматику")
#         print("4. Визуализировать PDA (демо)")
#         print("5. Экспорт PDA в CSV (демо)")
#         print("6. Выход")
#
#         choice = input("\nВаш выбор (1-6): ").strip()
#
#         if choice == "1":
#             run_tests()
#
#         elif choice == "2":
#             demonstration_mode()
#
#         elif choice == "3":
#             create_grammar_mode()
#
#         elif choice == "4":
#             print("\nСоздаем визуализацию для демонстрационной грамматики...")
#             grammar = Grammar(
#                 start="S",
#                 productions={
#                     "S": [("A", "B")],
#                     "A": [("a",)],
#                     "B": [("b",)]
#                 }
#             )
#             pda = grammar_to_pda(grammar)
#             visualize_pda(pda, "pda_visualization")
#
#         elif choice == "5":
#             print("\nЭкспорт переходов PDA в CSV...")
#             grammar = Grammar(
#                 start="S",
#                 productions={
#                     "S": [("A", "B")],
#                     "A": [("a",)],
#                     "B": [("b",)]
#                 }
#             )
#             pda = grammar_to_pda(grammar)
#             export_pda_csv(pda, "pda_transitions.csv")
#
#         elif choice == "6":
#             print("\nВыход из программы. До свидания!")
#             break
#
#         else:
#             print("Неверный выбор, попробуйте снова")
#
#
# # 11. ЗАПУСК ПРОГРАММЫ
#
# if __name__ == "__main__":
#     main()