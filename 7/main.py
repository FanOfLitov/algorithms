import csv
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Set
from graphviz import Digraph


# ============================================================
# 1. ГРАММАТИКА В НОРМАЛЬНОЙ ФОРМЕ ХОМСКОГО
# ============================================================

@dataclass
class Grammar:
    start: str
    productions: Dict[str, List[Tuple[str, ...]]]


# ============================================================
# 2. ПРОЕЦИЯ ГРАММАТИКИ НА МАГАЗИННЫЙ АВТОМАТ
# ============================================================

@dataclass
class PDA:
    states: Set[str]
    start_state: str
    accept_state: str
    transitions: Dict[Tuple[str, Optional[str], str], List[Tuple[str, str]]]


def grammar_to_pda(g: Grammar) -> PDA:
    """
    Превращает НФХ-грамматику в магазинный автомат по классической конструкции.
    """

    states = {"q", "accept"}
    start = "q"
    accept = "accept"

    transitions = {}

    def add_transition(state, inp, top, next_state, to_push):
        key = (state, inp, top)
        transitions.setdefault(key, []).append((next_state, to_push))

    # 1) Начальная конфигурация: кладём стартовый символ
    add_transition("q", None, None, "q", g.start)

    # 2) Продукции A → BC и A → a
    for A, prods in g.productions.items():
        for p in prods:

            # A → BC (два нетерминала)
            if len(p) == 2 and p[0].isupper() and p[1].isupper():
                B, C = p
                add_transition("q", None, A, "q", B + C)

            # A → a (терминал)
            elif len(p) == 1 and p[0].islower():
                a = p[0]
                add_transition("q", a, A, "q", "")  # заменяем A на ε, читаем терминал

    # 3) Завершение (когда стек пуст)
    add_transition("q", None, "", "accept", "")

    return PDA(states, start, accept, transitions)


# ============================================================
# 3. СИМУЛЯТОР PDA
# ============================================================

def run_pda(pda: PDA, input_string: str) -> bool:
    """
    Нерекурсивный симулятор PDA через множество конфигураций.
    Конфигурация: (state, pos, stack)
    """

    start_config = (pda.start_state, 0, pda.start_state)  # условный стек = стартовый символ
    configs = {start_config}

    for step in range(2000):  # ограничение по числу шагов
        new_configs = set()

        for state, pos, stack in configs:
            top = stack[-1] if stack else ""

            # Чтение символа + замена вершины стека
            key = (state, input_string[pos] if pos < len(input_string) else None, top)
            if key in pda.transitions:
                for next_state, push in pda.transitions[key]:
                    new_stack = stack[:-1] + push
                    new_pos = pos + (1 if key[1] is not None else 0)
                    new_configs.add((next_state, new_pos, new_stack))

            # ε-переходы
            key = (state, None, top)
            if key in pda.transitions:
                for next_state, push in pda.transitions[key]:
                    new_stack = stack[:-1] + push
                    new_configs.add((next_state, pos, new_stack))

        configs = new_configs

        # Проверка на приём
        for state, pos, stack in configs:
            if state == pda.accept_state and pos == len(input_string):
                return True

        if not configs:
            return False

    return False


# ============================================================
# 4. ПОИСК ПОДСТРОКИ С ПОМОЩЬЮ PDA
# ============================================================

def pda_find_substring(pda: PDA, text: str) -> List[int]:
    """
    Пытается применить PDA ко всем позициям строки.
    Возвращает список индексов, где произошёл успешный разбор.
    """
    positions = []
    for i in range(len(text)):
        if run_pda(pda, text[i:]):
            positions.append(i)
    return positions


# ============================================================
# 5. CSV ВЫГРУЗКА ПЕРЕХОДОВ
# ============================================================

def save_pda_csv(pda: PDA, filename="pda.csv"):
    with open(filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["state", "input", "stack_top", "next_state", "push"])
        for (state, inp, top), lst in pda.transitions.items():
            for next_state, push in lst:
                writer.writerow([state, inp, top, next_state, push])
    print(f"CSV сохранён: {filename}")


# ============================================================
# 6. ВИЗУАЛИЗАЦИЯ PDA (Graphviz)
# ============================================================

def visualize_pda(pda: PDA, filename="pda"):
    dot = Digraph()

    for s in pda.states:
        dot.node(s, shape="doublecircle" if s == pda.accept_state else "circle")

    for (st, inp, top), lst in pda.transitions.items():
        label = f"{inp if inp else 'ε'} ; {top}"
        for nst, push in lst:
            dot.edge(st, nst, label=f"{label} → {push if push else 'ε'}")

    dot.render(filename, format="png", cleanup=True)
    print(f"PDA визуализирован: {filename}.png")


# ============================================================
# 7. ТЕСТЫ
# ============================================================

def run_tests():
    grammar = Grammar(
        start="S",
        productions={
            "S": [("A", "B")],
            "A": ("a",),
            "B": ("b",)
        }
    )

    pda = grammar_to_pda(grammar)

    assert run_pda(pda, "ab") == True
    assert run_pda(pda, "a") == False
    assert run_pda(pda, "b") == False
    assert run_pda(pda, "aba") == True  # найдено с позиции 0
    assert run_pda(pda, "cabxyzab") == True

    pos = pda_find_substring(pda, "xxabxab")
    assert pos == [2, 5]

    print("Все тесты пройдены!")


# ============================================================
# 8. ПРИМЕР ЗАПУСКА
# ============================================================

if __name__ == "__main__":
    grammar = Grammar(
        start="S",
        productions={
            "S": [("A", "B")],
            "A": [("a",)],
            "B": [("b",)]
        }
    )

    pda = grammar_to_pda(grammar)

    # Визуализация
    visualize_pda(pda)

    # CSV
    save_pda_csv(pda, "pda.csv")

    # Запуск тестов
    run_tests()

    # Проверка поиска подстроки
    text = "xxabxab"
    print("Позиции подстроки:", pda_find_substring(pda, text))
