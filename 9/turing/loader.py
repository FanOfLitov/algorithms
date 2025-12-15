import csv
from .machine import Transition


def load_transitions(path: str):
    transitions = {}
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            transitions[(row["state"], row["read"])] = Transition(
                write=row["write"],
                move=row["move"],
                next_state=row["next_state"],
            )
    return transitions
