# gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from loader import load_transitions
from machine import TuringMachine


class TuringGUI:
    def __init__(self, csv_file="machine.csv"):
        try:
            self.transitions = load_transitions(csv_file)
        except FileNotFoundError:
            messagebox.showerror("Ошибка", f"Файл {csv_file} не найден!")
            self.transitions = {}

        self.root = tk.Tk()
        self.root.title("Машина Тьюринга - Симулятор")
        self.root.geometry("900x600")

        # Панель управления
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(control_frame, text="Входная лента:").pack(side="left")
        self.input_entry = ttk.Entry(control_frame, width=50)
        self.input_entry.pack(side="left", padx=5)
        self.input_entry.insert(0, "1010")  # Пример начальной ленты

        ttk.Button(control_frame, text="Старт", command=self.start).pack(side="left", padx=2)
        ttk.Button(control_frame, text="Пауза", command=self.pause).pack(side="left", padx=2)
        ttk.Button(control_frame, text="Шаг", command=self.step).pack(side="left", padx=2)
        ttk.Button(control_frame, text="Сброс", command=self.reset).pack(side="left", padx=2)

        # Информационная панель
        info_frame = ttk.Frame(self.root)
        info_frame.pack(fill="x", padx=10, pady=5)

        self.state_label = ttk.Label(info_frame, text="Состояние: --")
        self.state_label.pack(side="left", padx=10)

        self.step_label = ttk.Label(info_frame, text="Шаг: 0")
        self.step_label.pack(side="left", padx=10)

        self.position_label = ttk.Label(info_frame, text="Позиция: 0")
        self.position_label.pack(side="left", padx=10)

        # Панель скорости
        speed_frame = ttk.Frame(self.root)
        speed_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(speed_frame, text="Скорость:").pack(side="left")
        self.speed = tk.DoubleVar(value=0.5)
        self.speed_scale = ttk.Scale(
            speed_frame, from_=0.05, to=2.0,
            orient="horizontal", variable=self.speed,
            length=300
        )
        self.speed_scale.pack(side="left", padx=10)
        self.speed_value_label = ttk.Label(speed_frame, text="0.5 сек")
        self.speed_value_label.pack(side="left")
        self.speed.trace("w", self.update_speed_label)

        # Холст для ленты
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=1, highlightbackground="gray")
        self.canvas.pack(fill="both", expand=True)

        # Панель результатов
        result_frame = ttk.Frame(self.root)
        result_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(result_frame, text="Результат:").pack(side="left")
        self.result_var = tk.StringVar()
        ttk.Label(result_frame, textvariable=self.result_var, font=("Arial", 12, "bold")).pack(side="left", padx=10)

        # Инициализация машины
        self.machine = None
        self.running = False
        self.animation_id = None

        # Запускаем обновление интерфейса
        self.update_speed_label()

        # Привязка клавиш
        self.root.bind("<space>", lambda e: self.start() if not self.running else self.pause())
        self.root.bind("<Right>", lambda e: self.step())

    def update_speed_label(self, *args):
        speed_val = self.speed.get()
        self.speed_value_label.config(text=f"{speed_val:.2f} сек")

    def start(self):
        if self.running:
            return

        tape = self.input_entry.get().strip()
        if not tape:
            messagebox.showwarning("Внимание", "Введите ленту!")
            return

        self.machine = TuringMachine(self.transitions, tape)
        self.running = True
        self.animate()

    def pause(self):
        self.running = False
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

    def step(self):
        if not self.machine:
            tape = self.input_entry.get().strip()
            if not tape:
                return
            self.machine = TuringMachine(self.transitions, tape)

        if self.machine.state != "halt":
            self.machine.step()
            self.update_display()

    def reset(self):
        self.pause()
        self.machine = None
        self.state_label.config(text="Состояние: --")
        self.step_label.config(text="Шаг: 0")
        self.position_label.config(text="Позиция: 0")
        self.result_var.set("")
        self.draw_tape()

    def update_display(self):
        if self.machine:
            self.state_label.config(text=f"Состояние: {self.machine.state}")
            self.step_label.config(text=f"Шаг: {self.machine.steps}")
            self.position_label.config(text=f"Позиция: {self.machine.position}")
            self.result_var.set("".join(self.machine.tape).rstrip("_"))
            self.draw_tape()

    def draw_tape(self):
        self.canvas.delete("all")

        if not self.machine:
            return

        tape = self.machine.tape
        position = self.machine.position

        # Настройки отрисовки
        cell_width = 60
        cell_height = 60
        start_x = 50
        start_y = 50

        # Определяем видимый диапазон ячеек
        visible_cells = 15
        start_idx = max(0, position - visible_cells // 2)
        end_idx = min(len(tape), start_idx + visible_cells)

        # Рисуем ячейки
        for i in range(start_idx, end_idx):
            idx = i - start_idx
            x1 = start_x + idx * cell_width
            y1 = start_y
            x2 = x1 + cell_width
            y2 = y1 + cell_height

            # Цвет текущей ячейки
            if i == position:
                fill_color = "#90EE90"  # Светло-зеленый для текущей позиции
                border_color = "red"
                border_width = 3
            else:
                fill_color = "white"
                border_color = "black"
                border_width = 1

            # Рисуем ячейку
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                         fill=fill_color,
                                         outline=border_color,
                                         width=border_width)

            # Символ в ячейке
            symbol = tape[i] if i < len(tape) else "_"
            self.canvas.create_text(x1 + cell_width / 2, y1 + cell_height / 2,
                                    text=symbol, font=("Arial", 16, "bold"))

            # Номер ячейки
            self.canvas.create_text(x1 + cell_width / 2, y1 - 15,
                                    text=str(i), font=("Arial", 10))

        # Информация о машине
        info_text = f"Состояние: {self.machine.state} | Шаг: {self.machine.steps}"
        self.canvas.create_text(start_x, start_y + cell_height + 30,
                                text=info_text, font=("Arial", 12),
                                anchor="w")

    def animate(self):
        if not self.running or not self.machine:
            return

        self.update_display()

        if self.machine.state == "halt":
            self.running = False
            messagebox.showinfo("Завершено",
                                f"Машина остановлена.\nРезультат: {''.join(self.machine.tape).rstrip('_')}")
            return

        # Выполняем шаг
        self.machine.step()

        # Запланировать следующий кадр
        delay = int(1000 * float(self.speed.get()))
        self.animation_id = self.root.after(delay, self.animate)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    gui = TuringGUI("../machine.csv")
    gui.run()