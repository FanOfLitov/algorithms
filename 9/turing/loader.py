import csv
from machine import Transition  # Изменили импорт


def load_transitions(path: str):
    transitions = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Обработка пустого символа (пустая строка -> "_")
            read_symbol = row["read"] if row["read"].strip() != "" else "_"
            state = row["state"]

            transitions[(state, read_symbol)] = Transition(
                write=row["write"] if row["write"].strip() != "" else "_",
                move=row["move"],
                next_state=row["next_state"],
            )
    return transitions