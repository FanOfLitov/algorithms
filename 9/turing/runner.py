from .loader import load_transitions
from .machine import TuringMachine


def main():
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m turing.runner machine.csv tape")
        return

    transitions = load_transitions(sys.argv[1])
    tape = sys.argv[2]

    tm = TuringMachine(transitions, tape)
    result = tm.run()

    print("Result tape:", result)


if __name__ == "__main__":
    main()
