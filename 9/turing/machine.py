# machine.py
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional


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
            start_state: str = "q0"
    ):
        self.transitions = transitions
        self.tape = list(tape) if tape else ["_"]
        self.state = start_state
        self.position = 0
        self.steps = 0
        self.history = []

    def step(self) -> bool:

        prev_state = self.state
        prev_pos = self.position

        if 0 <= self.position < len(self.tape):
            symbol = self.tape[self.position]
        else:
            symbol = "_"

        key = (self.state, symbol)

        if key not in self.transitions:
            self.state = "halt"
            return False

        t = self.transitions[key]


        if 0 <= self.position < len(self.tape):
            self.tape[self.position] = t.write
        else:
            self.tape.append(t.write)


        if t.move == "R":
            self.position += 1
        elif t.move == "L":
            self.position -= 1

        if self.position < 0:
            self.tape.insert(0, "_")
            self.position = 0
        elif self.position >= len(self.tape):
            self.tape.append("_")


        self.state = t.next_state
        self.steps += 1

        self.history.append({
            'step': self.steps,
            'old_state': prev_state,
            'new_state': self.state,
            'position': prev_pos,
            'read': symbol,
            'write': t.write,
            'move': t.move
        })

        return self.state != "halt"

    def run(self, max_steps: int = 10000) -> str:

        while self.state != "halt" and self.steps < max_steps:
            self.step()
        return "".join(self.tape).rstrip("_")

    def get_current_info(self) -> dict:

        return {
            'state': self.state,
            'position': self.position,
            'steps': self.steps,
            'tape': "".join(self.tape),
            'current_symbol': self.tape[self.position] if 0 <= self.position < len(self.tape) else "_"
        }