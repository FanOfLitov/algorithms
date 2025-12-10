import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout,
    QHBoxLayout, QComboBox, QTextEdit, QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import dfa_core as core


class DFAGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DFA Minimizer — PyQt5")
        self.resize(1400, 800)

        self.dfa_original = None
        self.dfa_minimized = None

        self.btn_load = QPushButton("Загрузить CSV")
        self.btn_load.clicked.connect(self.load_csv)

        self.combo_algo = QComboBox()
        self.combo_algo.addItems(["Алгоритм таблицы различий", "Алгоритм Хопкрофта"])

        self.btn_minimize = QPushButton("Минимизировать")
        self.btn_minimize.clicked.connect(self.minimize)

        self.btn_compare = QPushButton("Проверить эквивалентность")
        self.btn_compare.clicked.connect(self.check_equivalence)

        self.btn_save = QPushButton("Сохранить минимизированный DFA")
        self.btn_save.clicked.connect(self.save_minimized)

        self.btn_step = QPushButton("Пошаговая визуализация минимизации")
        self.btn_step.clicked.connect(self.step_visualization)

        # окна для графов
        self.label_original = QLabel("Исходный DFA")
        self.label_original.setAlignment(Qt.AlignCenter)

        self.label_minimized = QLabel("Минимизированный DFA")
        self.label_minimized.setAlignment(Qt.AlignCenter)

        # лог
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)

        # --- ВЕРСТКА ---
        top = QHBoxLayout()
        top.addWidget(self.btn_load)
        top.addWidget(self.combo_algo)
        top.addWidget(self.btn_minimize)
        top.addWidget(self.btn_compare)
        top.addWidget(self.btn_step)
        top.addWidget(self.btn_save)

        mids = QHBoxLayout()
        mids.addWidget(self.label_original)
        mids.addWidget(self.label_minimized)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addLayout(mids)
        layout.addWidget(self.text_log)

        self.setLayout(layout)

    # -------------------------------------------------------------
    # ЗАГРУЗКА CSV
    # -------------------------------------------------------------
    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите CSV DFA", "", "CSV Files (*.csv)")
        if not path:
            return

        try:
            self.dfa_original = core.read_dfa_from_csv(path)
            self.text_log.append(f"[INFO] Загружен файл: {path}")

            # визуализация исходного DFA
            png = core.visualize_dfa(self.dfa_original, "original_graph", "Исходный DFA")
            self.set_image(self.label_original, png)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить DFA:\n{e}")

    # -------------------------------------------------------------
    # МИНИМИЗАЦИЯ
    # -------------------------------------------------------------
    def minimize(self):
        if not self.dfa_original:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите CSV!")
            return

        algo = self.combo_algo.currentIndex()

        try:
            if algo == 0:
                self.dfa_minimized, _ = core.minimize_table(self.dfa_original, log_steps=False)
                self.text_log.append("[INFO] Минимизация таблицей различий выполнена.")
            else:
                self.dfa_minimized, _ = core.minimize_hopcroft(self.dfa_original, log_steps=False)
                self.text_log.append("[INFO] Минимизация Хопкрофта выполнена.")

            # визуализация минимизированного DFA
            png = core.visualize_dfa(self.dfa_minimized, "minimized_graph", "Минимизированный DFA")
            self.set_image(self.label_minimized, png)

            # визуализация сравнения
            both = core.visualize_both(self.dfa_original, self.dfa_minimized, "comparison")
            self.text_log.append("[INFO] Сравнительный граф создан (comparison.png).")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка минимизации:\n{e}")

    # -------------------------------------------------------------
    # ШАГИ МИНИМИЗАЦИИ
    # -------------------------------------------------------------
    def step_visualization(self):
        if not self.dfa_original:
            QMessageBox.warning(self, "Ошибка", "Загрузите DFA!")
            return

        algo = self.combo_algo.currentIndex()
        try:
            if algo == 0:
                _, log = core.minimize_table(self.dfa_original, log_steps=True)
            else:
                _, log = core.minimize_hopcroft(self.dfa_original, log_steps=True)

            self.text_log.append("\n===== ПОШАГОВАЯ ВИЗУАЛИЗАЦИЯ =====")
            for line in log:
                self.text_log.append(line)

            self.text_log.append("===== КОНЕЦ =====\n")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка пошаговой визуализации:\n{e}")

    # -------------------------------------------------------------
    # ПРОВЕРКА ЭКВИВАЛЕНТНОСТИ
    # -------------------------------------------------------------
    def check_equivalence(self):
        if not self.dfa_original or not self.dfa_minimized:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите и минимизируйте DFA!")
            return

        # Простая проверка: сравнение поведения по тестовым строкам
        tests = ["", "a", "b", "aa", "ab", "ba", "bb", "aaa", "aba"]
        mismatch = None

        for s in tests:
            o = follow(self.dfa_original, s)
            m = follow(self.dfa_minimized, s)
            if o != m:
                mismatch = (s, o, m)
                break

        if mismatch:
            QMessageBox.warning(self, "Не эквивалентны",
                                f"Строка '{mismatch[0]}' различает автоматы:\n"
                                f"Исходный = {mismatch[1]}\nМинимизированный = {mismatch[2]}")
        else:
            QMessageBox.information(self, "Эквивалентны",
                                    "Минимизированный автомат эквивалентен исходному.")

    # -------------------------------------------------------------
    # СОХРАНИТЬ DFA
    # -------------------------------------------------------------
    def save_minimized(self):
        if not self.dfa_minimized:
            QMessageBox.warning(self, "Ошибка", "Нет минимизированного DFA!")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        try:
            self.write_dfa_to_csv(self.dfa_minimized, path)
            QMessageBox.information(self, "OK", "Сохранено!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")

    def write_dfa_to_csv(self, dfa, path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            import csv
            w = csv.writer(f)
            w.writerow(["state"] + sorted(dfa.alphabet) + ["accept"])
            for st in sorted(dfa.states):
                row = [st] + [dfa.transitions[st][sym] for sym in sorted(dfa.alphabet)]
                row.append("*" if st in dfa.accept_states else "")
                w.writerow(row)

    # -------------------------------------------------------------
    # ВЫВОД PNG В QLabel
    # -------------------------------------------------------------
    def set_image(self, label, path):
        if os.path.exists(path):
            pixmap = QPixmap(path).scaled(
                label.width(), label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            label.setPixmap(pixmap)
        else:
            label.setText("PNG не найден")


# -----------------------------------------------------------------------------

def follow(dfa, string):
    st = dfa.start_state
    for ch in string:
        st = dfa.transitions[st][ch]
    return st in dfa.accept_states


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = DFAGUI()
    gui.show()
    sys.exit(app.exec_())
