import tkinter as tk
from tkinter import ttk
from .loader import load_transitions
from .machine import TuringMachine


class TuringGUI:
    def __init__(self, csv_file):
        self.transitions = load_transitions(csv_file)

        self.root = tk.Tk()
        self.root.title("Машина Тьюринга")

        self.speed = tk.DoubleVar(value=0.5)  # скорость анимации

        ttk.Label(self.root, text="Лента:").pack()
        self.input_entry = ttk.Entry(self.root, width=50)
        self.input_entry.pack()

        ttk.Button(self.root, text="Старт", command=self.start).pack()

        self.canvas = tk.Canvas(self.root, width=800, height=100, bg="white")
        self.canvas.pack()

        ttk.Scale(
            self.root, from_=0.05, to=1.0,
            orient="horizontal", variable=self.speed
        ).pack()

        self.machine = None
        self.running = False

    def start(self):
        tape = self.input_entry.get()
        self.machine = TuringMachine(self.transitions, tape)
        self.running = True
        self.animate()

    def draw_tape(self):
        self.canvas.delete("all")
        x = 20
        for i, sym in enumerate(self.machine.tape):
            color = "yellow" if i == self.machine.position else "white"
            self.canvas.create_rectangle(x, 20, x + 40, 60, fill=color)
            self.canvas.create_text(x + 20, 40, text=sym)
            x += 45

    def animate(self):
        if not self.running:
            return

        self.draw_tape()

        if not self.machine.step():
            self.running = False
            return

        delay = int(1000 * float(self.speed.get()))
        self.root.after(delay, self.animate)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    gui = TuringGUI("machine.csv")
    gui.run()