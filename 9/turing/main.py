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
    transitions = [
        ["state", "read", "write", "move", "next_state"],
        # Начало: идем к концу первого числа
        ["q0", "0", "0", "R", "q0"],
        ["q0", "1", "1", "R", "q0"],
        ["q0", "+", "+", "R", "q1"],

        # Идем к концу второго числа
        ["q1", "0", "0", "R", "q1"],
        ["q1", "1", "1", "R", "q1"],
        ["q1", "_", "_", "L", "q2"],  # Дошли до конца

        # Начинаем сложение с младших разрядов
        ["q2", "0", "_", "L", "q3"],  # Берем 0 из второго числа
        ["q2", "1", "_", "L", "q4"],  # Берем 1 из второго числа
        ["q2", "+", "_", "L", "q10"],  # Второе число кончилось

        # q3: взяли 0 из второго числа, идем к первому числу
        ["q3", "0", "0", "L", "q3"],
        ["q3", "1", "1", "L", "q3"],
        ["q3", "+", "+", "L", "q5"],

        # q4: взяли 1 из второго числа, идем к первому числу
        ["q4", "0", "0", "L", "q4"],
        ["q4", "1", "1", "L", "q4"],
        ["q4", "+", "+", "L", "q6"],

        # q5: прибавляем 0 к первому числу
        ["q5", "0", "0", "R", "q7"],  # 0 + 0 = 0, без переноса
        ["q5", "1", "1", "R", "q7"],  # 1 + 0 = 1, без переноса
        ["q5", "_", "0", "R", "q7"],  # Число кончилось, добавляем 0

        # q6: прибавляем 1 к первому числу
        ["q6", "0", "1", "R", "q7"],  # 0 + 1 = 1, без переноса
        ["q6", "1", "0", "L", "q6"],  # 1 + 1 = 0, есть перенос
        ["q6", "_", "1", "R", "q7"],  # Число кончилось, добавляем 1

        # q7: идем обратно ко второму числу
        ["q7", "+", "+", "R", "q8"],
        ["q8", "_", "_", "L", "q2"],

        # q9: обработка переноса (для q6)
        ["q9", "0", "1", "R", "q7"],  # 0 + перенос = 1
        ["q9", "1", "0", "L", "q9"],  # 1 + перенос = 0, сохраняем перенос
        ["q9", "_", "1", "R", "q7"],  # Число кончилось, добавляем 1
        ["q9", "+", "+", "L", "q9"],

        # q10: второе число кончилось, возвращаемся к началу результата
        ["q10", "0", "0", "L", "q10"],
        ["q10", "1", "1", "L", "q10"],
        ["q10", "+", "_", "L", "q11"],  # Стираем +

        # q11: двигаем результат в начало ленты
        ["q11", "0", "_", "R", "q12"],
        ["q11", "1", "_", "R", "q13"],
        ["q11", "_", "_", "R", "q15"],  # Дошли до начала

        # q12: записываем 0 в начало
        ["q12", "_", "0", "L", "q14"],

        # q13: записываем 1 в начало
        ["q13", "_", "1", "L", "q14"],

        # q14: возвращаемся за следующим символом
        ["q14", "0", "0", "R", "q11"],
        ["q14", "1", "1", "R", "q11"],
        ["q14", "_", "_", "R", "q15"],

        # q15: финальная очистка и остановка
        ["q15", "0", "_", "R", "q15"],
        ["q15", "1", "_", "R", "q15"],
        ["q15", "_", "_", "S", "halt"],
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(transitions)

    print(f"Создан сумматор двоичных чисел в файле {filename}")
    return filename
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
    #
    # with open(filename, "w", newline="", encoding="utf-8") as f:
    #     writer = csv.writer(f)
    #     writer.writerows(transitions)
    #
    # print(f"Создан сумматор двоичных чисел в файле {filename}")
    # return filename


def main():
    # Выбор машины
    selector = MachineSelector()
    machine_type = selector.run()

    if not machine_type:
        return

    # Создаем соответствующую машину
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
        example_input = "1001"  # Палиндром - примет
        description = "Проверка палиндрома: принимает/отклоняет"

    elif machine_type == "adder":
        machine_file = create_binary_adder()
        example_input = "101+110"  # 5 + 6 = 11 (1011)
        description = "Сумматор: складывает два двоичных числа"

    else:  # Пользовательский файл
        machine_file = machine_type
        example_input = "1010"
        description = f"Пользовательская машина из {machine_file}"

    # Запускаем GUI
    from gui import TuringGUI
    gui = TuringGUI(machine_file)

    # Устанавливаем пример в поле ввода
    gui.input_entry.delete(0, tk.END)
    gui.input_entry.insert(0, example_input)

    # Показываем описание
    messagebox.showinfo("Информация", f"{description}\n\nПример ввода: {example_input}")

    gui.run()


if __name__ == "__main__":
    main()