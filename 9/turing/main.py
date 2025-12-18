# main.py
import sys
import os


# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from gui import TuringGUI
from examples import create_example_machine

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import csv


class MachineSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Выбор машины Тьюринга")
        self.root.geometry("400x300")

        ttk.Label(self.root, text="Выберите тип машины Тьюринга:",
                  font=("Arial", 12)).pack(pady=10)

        # Кнопки выбора
        ttk.Button(self.root, text="1. Инвертор битов (0→1, 1→0)",
                   command=lambda: self.select_machine("inverter")).pack(pady=5, padx=20, fill="x")

        ttk.Button(self.root, text="2. Удвоитель строки",
                   command=lambda: self.select_machine("copier")).pack(pady=5, padx=20, fill="x")

        ttk.Button(self.root, text="3. Проверка палиндрома",
                   command=lambda: self.select_machine("palindrome")).pack(pady=5, padx=20, fill="x")

        ttk.Button(self.root, text="4. Двоичное сложение",
                   command=lambda: self.select_machine("adder")).pack(pady=5, padx=20, fill="x")

        ttk.Button(self.root, text="5. Загрузить из CSV",
                   command=self.load_custom).pack(pady=5, padx=20, fill="x")

        self.selected_machine = None

    def select_machine(self, machine_type):
        self.selected_machine = machine_type
        self.root.destroy()

    def load_custom(self):
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Выберите CSV файл",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.selected_machine = filename
            self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.selected_machine


def create_inverter(filename="machine.csv"):
    """Создает машину Тьюринга для инвертирования бинарной строки"""
    transitions = [
        ["state", "read", "write", "move", "next_state"],
        ["q0", "0", "1", "R", "q0"],
        ["q0", "1", "0", "R", "q0"],
        ["q0", "_", "_", "S", "halt"],
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(transitions)

    print(f"Создан инвертор битов в файле {filename}")
    return filename


def create_copier(filename="machine.csv"):
    """Создает машину Тьюринга для копирования строки"""
    transitions = [
        ["state", "read", "write", "move", "next_state"],
        ["q0", "0", "X", "R", "q1"],
        ["q0", "1", "Y", "R", "q2"],
        ["q0", "_", "_", "L", "q5"],
        ["q1", "0", "0", "R", "q1"],
        ["q1", "1", "1", "R", "q1"],
        ["q1", "_", "_", "R", "q3"],
        ["q2", "0", "0", "R", "q2"],
        ["q2", "1", "1", "R", "q2"],
        ["q2", "_", "_", "R", "q4"],
        ["q3", "_", "0", "L", "q3"],
        ["q3", "0", "0", "L", "q3"],
        ["q3", "1", "1", "L", "q3"],
        ["q3", "X", "0", "R", "q0"],
        ["q4", "_", "1", "L", "q4"],
        ["q4", "0", "0", "L", "q4"],
        ["q4", "1", "1", "L", "q4"],
        ["q4", "Y", "1", "R", "q0"],
        ["q5", "0", "0", "L", "q5"],
        ["q5", "1", "1", "L", "q5"],
        ["q5", "X", "0", "L", "q5"],
        ["q5", "Y", "1", "L", "q5"],
        ["q5", "_", "_", "R", "halt"],
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(transitions)

    print(f"Создан удвоитель строки в файле {filename}")
    return filename


def create_palindrome_checker(filename="machine.csv"):
    """Создает машину Тьюринга для проверки палиндрома"""
    transitions = [
        ["state", "read", "write", "move", "next_state"],
        ["q0", "0", "X", "R", "q1"],
        ["q0", "1", "Y", "R", "q2"],
        ["q0", "_", "_", "S", "q_accept"],
        ["q1", "0", "0", "R", "q1"],
        ["q1", "1", "1", "R", "q1"],
        ["q1", "_", "_", "L", "q3"],
        ["q2", "0", "0", "R", "q2"],
        ["q2", "1", "1", "R", "q2"],
        ["q2", "_", "_", "L", "q4"],
        ["q3", "X", "X", "R", "q5"],
        ["q3", "0", "X", "L", "q6"],
        ["q4", "Y", "Y", "R", "q5"],
        ["q4", "1", "Y", "L", "q7"],
        ["q5", "0", "0", "R", "q5"],
        ["q5", "1", "1", "R", "q5"],
        ["q5", "_", "_", "L", "q8"],
        ["q6", "0", "0", "L", "q6"],
        ["q6", "1", "1", "L", "q6"],
        ["q6", "X", "X", "R", "q0"],
        ["q7", "0", "0", "L", "q7"],
        ["q7", "1", "1", "L", "q7"],
        ["q7", "Y", "Y", "R", "q0"],
        ["q8", "X", "X", "S", "q_accept"],
        ["q8", "Y", "Y", "S", "q_accept"],
        ["q8", "0", "0", "S", "q_reject"],
        ["q8", "1", "1", "S", "q_reject"],
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(transitions)

    print(f"Создан проверщик палиндромов в файле {filename}")
    return filename


def create_binary_adder(filename="machine.csv"):

    # transitions = [
    #     ["state", "read", "write", "move", "next_state"],
    #     ["q0", "0", "0", "R", "q0"],
    #     ["q0", "1", "1", "R", "q0"],
    #     ["q0", "+", "+", "R", "q1"],
    #     ["q1", "0", "0", "R", "q1"],
    #     ["q1", "1", "1", "R", "q1"],
    #     ["q1", "_", "_", "L", "q2"],
    #     ["q2", "0", "_", "L", "q3"],
    #     ["q2", "1", "_", "L", "q4"],
    #     ["q3", "0", "0", "L", "q3"],
    #     ["q3", "1", "1", "L", "q3"],
    #     ["q3", "+", "+", "L", "q5"],
    #     ["q4", "0", "0", "L", "q4"],
    #     ["q4", "1", "1", "L", "q4"],
    #     ["q4", "+", "+", "L", "q6"],
    #     ["q5", "0", "1", "R", "q7"],
    #     ["q5", "1", "0", "L", "q5"],
    #     ["q5", "_", "1", "R", "q7"],
    #     ["q6", "0", "0", "L", "q6"],
    #     ["q6", "1", "1", "L", "q6"],
    #     ["q6", "_", "_", "R", "q8"],
    #     ["q7", "+", "+", "R", "q1"],
    #     ["q8", "0", "0", "R", "q8"],
    #     ["q8", "1", "1", "R", "q8"],
    #     ["q8", "+", "_", "R", "q9"],
    #     ["q9", "0", "0", "R", "q9"],
    #     ["q9", "1", "1", "R", "q9"],
    #     ["q9", "_", "_", "L", "halt"],
    # ]
    transitions = [
        ["state", "read", "write", "move", "next_state"],
        ["q0", "0", "0", "R", "q0"],
        ["q0", "1", "1", "R", "q0"],
        ["q0", "_", "_", "R", "q1"],
        ["q1", "0", "0", "R", "q1"],
        ["q1", "1", "1", "R", "q1"],
        ["q1", "_", "_", "L", "q2"],
        ["q2", "0", "_", "L", "q3"],
        ["q2", "1", "_", "L", "q4"],
        ["q3", "0", "0", "L", "q3"],
        ["q3", "1", "1", "L", "q3"],
        ["q3", "_", "_", "L", "q5"],
        ["q4", "0", "0", "L", "q4"],
        ["q4", "1", "1", "L", "q4"],
        ["q4", "_", "_", "L", "q6"],
        ["q5", "0", "1", "R", "q7"],
        ["q5", "1", "0", "L", "q5"],
        ["q5", "_", "1", "R", "q7"],
        ["q6", "0", "0", "L", "q6"],
        ["q6", "1", "1", "L", "q6"],
        ["q6", "_", "_", "R", "q8"],
        ["q7", "_", "_", "R", "q1"],
        ["q8", "0", "0", "R", "q8"],
        ["q8", "1", "1", "R", "q8"],
        ["q8", "_", "_", "R", "q9"],
        ["q9", "0", "0", "R", "q9"],
        ["q9", "1", "1", "R", "q9"],
        ["q9", "_", "_", "L", "q_cleanup"],

        ["q_cleanup", "0", "0", "L", "q_cleanup"],
        ["q_cleanup", "1", "1", "L", "q_cleanup"],
        ["q_cleanup", "_", "_", "S", "halt"],
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(transitions)

    print(f"Создан сумматор двоичных чисел в файле {filename}")
    return filename


def main():

    selector = MachineSelector()
    machine_type = selector.run()

    if not machine_type:
        return


    if machine_type == "inverter":
        machine_file = create_inverter()
        example_input = "1010"  # Станет "0101"
        description = "Инвертор битов: меняет 0 на 1 и 1 на 0"

    elif machine_type == "copier":
        machine_file = create_copier()
        example_input = "101"  # Станет "101101"
        description = "Удвоитель строки: копирует входную строку"

    elif machine_type == "palindrome":
        machine_file = create_palindrome_checker()
        example_input = "1001"  # Палиндром
        description = "Проверка палиндрома: принимает/отклоняет"

    elif machine_type == "adder":
        machine_file = create_binary_adder()
        example_input = "101_110"  # 5 + 6 = 11 (1011)
        description = "Сумматор: складывает два двоичных числа"

    else:
        machine_file = machine_type
        example_input = "1010"
        description = f"Пользовательская машина из {machine_file}"


    from gui import TuringGUI
    gui = TuringGUI(machine_file)


    gui.input_entry.delete(0, tk.END)
    gui.input_entry.insert(0, example_input)


    messagebox.showinfo("Информация", f"{description}\n\nПример ввода: {example_input}")

    gui.run()


if __name__ == "__main__":
    main()