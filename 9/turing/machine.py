from dataclasses import dataclass
from typing import Dict, Tuple, List


@dataclass
class Transition:
    write: str
    move: str
    next_state: str


class TuringMachine:
    def __init__(
        self,
        transitions: Dict[Tuple[str, str], Transition],
        tape: str,
        start_state="q0"
    ):
        self.transitions = transitions
        self.tape = list(tape)
        self.state = start_state
        self.position = 0
        self.steps = 0

    def step(self) -> bool:
        """Выполняет один шаг. Возвращает False если машина остановилась."""
        symbol = self.tape[self.position] if 0 <= self.position < len(self.tape) else "_"
        key = (self.state, symbol)

        if key not in self.transitions:
            self.state = "halt"
            return False

        t = self.transitions[key]

        # запись
        if 0 <= self.position < len(self.tape):
            self.tape[self.position] = t.write
        else:
            self.tape.append(t.write)

        # движение
        if t.move == "R":
            self.position += 1
        elif t.move == "L":
            self.position -= 1

        # авторасширение
        if self.position < 0:
            self.tape.insert(0, "_")
            self.position = 0
        if self.position >= len(self.tape):
            self.tape.append("_")

        # новое состояние
        self.state = t.next_state
        self.steps += 1

        return self.state != "halt"

    def run(self, max_steps=10000):
        while self.state != "halt" and self.steps < max_steps:
            self.step()
        return "".join(self.tape)
