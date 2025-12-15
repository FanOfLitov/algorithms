import pytest
from turing.machine import TuringMachine, Transition


def test_simple_rewrite():
    transitions = {
        ("q0", "0"): Transition("1", "R", "halt")
    }
    tm = TuringMachine(transitions, "0")
    assert tm.run() == "1"


def test_left_expand():
    transitions = {
        ("q0", "1"): Transition("0", "L", "halt")
    }
    tm = TuringMachine(transitions, "1")
    tm.run()
    assert tm.tape[0] == "0"
