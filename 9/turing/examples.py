# examples.py
import csv


def create_example_machine(filename="machine.csv"):

    transitions = [
        ["state", "read", "write", "move", "next_state"],
        ["q0", "0", "1", "R", "q0"],
        ["q0", "1", "0", "R", "q0"],
        ["q0", "_", "_", "S", "halt"],
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(transitions)

    print(f"Файл {filename} создан успешно!")


def create_counter_machine(filename="counter.csv"):
    """Создает машину-счетчик (увеличивает двоичное число на 1)."""
    transitions = [
        ["state", "read", "write", "move", "next_state"],
        ["q0", "0", "0", "R", "q0"],
        ["q0", "1", "1", "R", "q0"],
        ["q0", "_", "_", "L", "q1"],
        ["q1", "0", "1", "L", "q2"],
        ["q1", "1", "0", "L", "q1"],
        ["q1", "_", "1", "S", "halt"],
        ["q2", "0", "0", "L", "q2"],
        ["q2", "1", "1", "L", "q2"],
        ["q2", "_", "_", "R", "halt"],
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(transitions)

    print(f"Файл {filename} создан успешно!")


if __name__ == "__main__":
    create_example_machine()