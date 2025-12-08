import graphviz as gv
from collections import defaultdict, deque
import os
import glob
from PIL import Image
from typing import Dict, List, Tuple, Set


class RegexEngine:

    def __init__(self, regex):
        self.regex = self._tokenize("(" + regex + ")")
        self.text = None
        self.metacharacters = "( ) | ? * + [ ] { }".split()

        # get formatting states/edges
        self.gv_states, self.gv_edges = self._get_formatting_states()

        # match transition edges
        self.match_transitions = self._get_match_transitions()

        # epsilon transition edges
        self.epsilon_transitions, \
            self.star_dict, \
            self.plus_dict, \
            self.closure_dict, \
            self.question_dict, \
            self.next_transition_dict = \
            self._get_epsilon_transitions()

    @staticmethod
    def _tokenize(regex):
        regex_symbols = deque(regex)
        regex_tokens = []

        # splits square bracket into three tokens: left brace, middle text, right brace
        def process_sq_bracket():
            regex_tokens.append(symbol)
            next_symbol = regex_symbols.popleft()
            bracket_text = []
            while next_symbol != "]":
                bracket_text.append(next_symbol)
                next_symbol = regex_symbols.popleft()
            bracket_text = "".join(bracket_text)
            regex_tokens.append(bracket_text)
            regex_tokens.append(next_symbol)

        # converts repetition counter to series of ? operators
        def process_curl_bracket():
            repeat_token = regex_tokens[-1]

            if repeat_token == "]":
                repeat_token = ["[", regex_tokens[-2], "]"]
            elif repeat_token == ")":
                match_group = deque()
                for token in reversed(regex_tokens):
                    if token == "(":
                        match_group.appendleft(token)
                        break
                    match_group.appendleft(token)
                repeat_token = list(match_group)
            else:
                repeat_token = [repeat_token]

            min_reps = int(regex_symbols.popleft())
            regex_symbols.popleft()  # pop comma
            regex_symbols.popleft()  # pop space
            max_reps = int(regex_symbols.popleft())

            [regex_tokens.extend(repeat_token) for _ in range(min_reps - 1)]
            [regex_tokens.extend(repeat_token + ["?"]) for _ in range(max_reps - min_reps)]
            regex_symbols.popleft()  # remove right curly bracket

        while regex_symbols:
            symbol = regex_symbols.popleft()
            if symbol == "{":
                process_curl_bracket()
            elif symbol == "[":
                process_sq_bracket()
            else:
                regex_tokens.append(symbol)

        return regex_tokens

    @staticmethod
    def _text_range(start, stop):
        return "".join([chr(num) for num in range(ord(start), ord(stop) + 1)])

    def _get_formatting_states(self):
        states_list = []
        invisible_transitions = []

        for i, unit in enumerate(self.regex):
            states_list.append((i, unit))
            if i > 0:
                invisible_transitions.append((i - 1, i))

        # add final accepting state
        states_list.append((len(self.regex), ""))
        invisible_transitions.append((len(self.regex) - 1, len(self.regex)))

        return states_list, invisible_transitions

    def _get_match_transitions(self):
        match_transitions = {}
        for i, unit in enumerate(self.regex):
            if i > 0 and self.regex[i - 1] not in self.metacharacters:
                match_transitions[i - 1] = i
        return match_transitions

    def _get_epsilon_transitions(self):
        star_dict = {"N": [], "S": []}
        question_dict = {"N": [], "S": []}
        closure_dict = {"(": [], "|": []}
        plus_dict = {"N": []}
        next_transition_dict = {"next": []}

        operator_idx_stack = []
        for i, unit in enumerate(self.regex):
            left_paren_idx = i
            if unit == "(" or unit == "|":
                operator_idx_stack.append(i)
            elif unit == ")":
                or_idx_list = []
                while True:
                    op_idx = operator_idx_stack.pop(-1)
                    if self.regex[op_idx] == "|":
                        or_idx_list.append(op_idx)
                    elif self.regex[op_idx] == "(":
                        left_paren_idx = op_idx
                        [closure_dict["("].append((left_paren_idx, or_idx + 1)) for or_idx in or_idx_list]
                        [closure_dict["|"].append((or_idx, i)) for or_idx in or_idx_list]
                        break

            elif unit == "]":
                left_paren_idx = i - 2

            if (i < (len(self.regex) - 1)) and self.regex[i + 1] == "*":
                star_dict["N"].append((left_paren_idx, i + 1))
                star_dict["S"].append((i + 1, left_paren_idx))

            if (i < (len(self.regex) - 1)) and self.regex[i + 1] == "+":
                plus_dict["N"].append((i + 1, left_paren_idx))

            if (i < (len(self.regex) - 1)) and self.regex[i + 1] == "?":
                question_dict["N"].append((left_paren_idx, i + 2))

            if unit in self.metacharacters and i < len(self.regex):
                next_transition_dict["next"].append((i, i + 1))

        epsilon_transitions = self._combine_epsilon_edges(star_dict, plus_dict, closure_dict,
                                                          next_transition_dict, question_dict)

        return epsilon_transitions, star_dict, plus_dict, closure_dict, question_dict, next_transition_dict

    @staticmethod
    def _combine_epsilon_edges(*args):
        epsilon_transitions = defaultdict(list)
        for edge_dict in args:
            for coord_list in edge_dict.values():
                for tup in coord_list:
                    epsilon_transitions[tup[0]].append(tup[1])
        return epsilon_transitions

    def _draw_nfa(self, active_states, active_match_transitions, active_epsilon_transitions, letter_idx,
                  filename="nfa"):

        graph = gv.Digraph(filename=filename, format='png')

        if self.text:
            header_text = f'''<<table border="0" cellborder="1" cellspacing="0">
                              <tr>
                              <td colspan="{str(len(self.text) + 1)}"><FONT POINT-SIZE="16">Search Text</FONT></td>
                              </tr>
                              <tr>'''

            use_text = " " + self.text
            for i, letter in enumerate(use_text):
                color = "orange" if letter_idx == i else "white"
                letter = "   " if letter == " " else letter
                row_text = f'<td port="p{i}" bgcolor="{color}" colspan="1">{letter}</td>\n'
                header_text += row_text

            header_text += "</tr></table>>"

            graph.attr(ranksep=".25", rankdir="LR", labelloc="t", fontsize="22", shape="plain", label=header_text)
        else:
            graph.attr(ranksep=".25", rankdir="LR")

        # add states
        for idx, label in self.gv_states:
            if idx in active_states:
                graph.node(str(idx), str(label), color="green", style="filled", rank="sink")
            else:
                graph.node(str(idx), str(label))

        # add invisible edges for proper node ordering
        [graph.edge(str(tail), str(head), style="invis", weight="10") for tail, head in self.gv_edges]

        # add match transition edges
        for tail, head in self.match_transitions.items():
            if (tail, head) in active_match_transitions:
                graph.edge(str(tail) + ":e", str(head) + ":w", color="black", weight="10", style="bold",
                           arrowsize="1.33")
            else:
                graph.edge(str(tail) + ":e", str(head) + ":w", color="black", weight="10")

        # add next state epsilon transition edges
        for tail, head in self.next_transition_dict["next"]:
            if (tail, head) in active_epsilon_transitions:
                graph.edge(str(tail) + ":e", str(head) + ":w", color="red", weight="10", arrowsize="1.33", style="bold")
            else:
                graph.edge(str(tail) + ":e", str(head) + ":w", color="red", weight="10")

        # add * edges
        for tail, head in self.star_dict["N"]:
            if (tail, head) in active_epsilon_transitions:
                graph.edge(str(tail) + ":ne", str(head) + ":nw", color="red", arrowsize="1.33", style="bold")
            else:
                graph.edge(str(tail) + ":ne", str(head) + ":nw", color="red")

        for tail, head in self.star_dict["S"]:
            if (tail, head) in active_epsilon_transitions:
                graph.edge(str(tail) + ":sw", str(head) + ":se", color="red", arrowsize="1.33", style="bold")
            else:
                graph.edge(str(tail) + ":sw", str(head) + ":se", color="red")

        # add + edges
        for tail, head in self.plus_dict["N"]:
            if (tail, head) in active_epsilon_transitions:
                graph.edge(str(tail) + ":nw", str(head) + ":ne", color="red", arrowsize="1.33", style="bold")
            else:
                graph.edge(str(tail) + ":nw", str(head) + ":ne", color="red")

        # add ? edges
        for tail, head in self.question_dict["N"]:
            if (tail, head) in active_epsilon_transitions:
                graph.edge(str(tail), str(head), color="red", arrowsize="1.33", style="bold")
            else:
                graph.edge(str(tail), str(head), color="red")

        for tail, head in self.question_dict["S"]:
            if (tail, head) in active_epsilon_transitions:
                graph.edge(str(tail) + ":sw", str(head) + ":se", color="red", arrowsize="1.33", style="bold")
            else:
                graph.edge(str(tail) + ":sw", str(head) + ":se", color="red")

        # add | closure edges
        for tail, head in self.closure_dict["("]:
            if (tail, head) in active_epsilon_transitions:
                graph.edge(str(tail), str(head), color="red", arrowsize="1.33", style="bold")
            else:
                graph.edge(str(tail), str(head), color="red")

        for tail, head in self.closure_dict["|"]:
            if (tail, head) in active_epsilon_transitions:
                graph.edge(str(tail), str(head), color="red", arrowsize="1.33", style="bold")
            else:
                graph.edge(str(tail), str(head), color="red")

        # Save as PNG only (no intermediate DOT file)
        output_dir = "visualizations"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        graph.render(filename=output_path, format='png', cleanup=True)
        print(f"✓ Визуализация сохранена как {output_path}.png")

    @staticmethod
    def _digraph_dfs(graph, node, draw=False):
        reachable_states = []
        epsilon_arrows = []

        def find_states(graph, node):
            if node in reachable_states:
                return
            elif node not in graph.keys():
                reachable_states.append(node)
                return
            else:
                reachable_states.append(node)
                for state in graph[node]:
                    epsilon_arrows.append((node, state))
                    find_states(graph, state)

        find_states(graph, node)

        if draw:
            return epsilon_arrows
        else:
            return reachable_states

    def search(self, text, filename_prefix="nfa_state_"):
        self.text = text

        # get epsilon states before scanning first character
        epsilon_states = self._digraph_dfs(self.epsilon_transitions, 0)
        epsilon_arrows = self._digraph_dfs(self.epsilon_transitions, 0, draw=True)

        graph_state = 0
        self._draw_nfa(epsilon_states, (), epsilon_arrows, 0, f"{filename_prefix}{str(graph_state).zfill(3)}")
        graph_state += 1

        if len(self.regex) in epsilon_states:
            self._draw_nfa([len(self.regex)], (), (), 0, f"{filename_prefix}{str(graph_state).zfill(3)}")
            return True

        epsilon_chars = [self.regex[state] for state in epsilon_states]

        for i, letter in enumerate(text):
            self._draw_nfa(epsilon_states, (), epsilon_arrows, i + 1, f"{filename_prefix}{str(graph_state).zfill(3)}")
            graph_state += 1

            matched_states = []
            for state, char_group in zip(epsilon_states, epsilon_chars):
                if letter in char_group or "." in char_group:
                    matched_states.append(state)
                elif "-" in char_group:
                    ranges = ""
                    for idx, char in enumerate(char_group):
                        if char == "-":
                            ranges += self._text_range(char_group[idx - 1], char_group[idx + 1])
                    if letter in ranges:
                        matched_states.append(state)

            next_states = []
            [next_states.append(self.match_transitions[node]) for node in matched_states]

            match_arrows = list(zip(matched_states, next_states))
            self._draw_nfa(next_states, match_arrows, (), i + 1, f"{filename_prefix}{str(graph_state).zfill(3)}")
            graph_state += 1

            epsilon_states = []
            [epsilon_states.extend(self._digraph_dfs(self.epsilon_transitions, node)) for node in next_states]

            epsilon_arrows = []
            [epsilon_arrows.extend(self._digraph_dfs(self.epsilon_transitions, node, draw=True)) for node in
             next_states]

            self._draw_nfa(epsilon_states, (), epsilon_arrows, i + 1, f"{filename_prefix}{str(graph_state).zfill(3)}")
            graph_state += 1

            if len(self.regex) in epsilon_states:
                self._draw_nfa([len(self.regex)], (), (), i + 1, f"{filename_prefix}{str(graph_state).zfill(3)}")
                return True

            epsilon_chars = [self.regex[state] for state in epsilon_states]

        return False

    def draw_regex_nfa(self, filename="regex_nfa"):
        """Нарисовать только НКА без поиска"""
        self._draw_nfa((), (), (), 0, filename)


class DFAGraphVisualizer:
    """Класс для визуализации ДКА"""

    @staticmethod
    def visualize_dfa(dfa, filename="dfa_graph"):
        """Визуализация детерминированного конечного автомата"""
        graph = gv.Digraph(filename=filename, format='png')
        graph.attr(rankdir='LR', size='10,7')

        # Добавляем состояния
        for state in sorted(dfa.states):
            node_attrs = {}

            if state == dfa.start_state:
                node_attrs['style'] = 'filled'
                node_attrs['fillcolor'] = 'lightblue'

            if state in dfa.accept_states:
                node_attrs['shape'] = 'doublecircle'
            else:
                node_attrs['shape'] = 'circle'

            if state == -1:  # Ловушка
                node_attrs['style'] = 'filled'
                node_attrs['fillcolor'] = 'lightgray'
                node_attrs['label'] = 'q_trap'
            else:
                node_attrs['label'] = f'q{state}'

            graph.node(str(state), **node_attrs)

        # Добавляем начальную стрелку
        graph.node('start', shape='point')
        graph.edge('start', str(dfa.start_state))

        # Добавляем переходы
        for from_state, transitions in dfa.transitions.items():
            for symbol, to_state in transitions.items():
                graph.edge(str(from_state), str(to_state), label=symbol)

        # Сохраняем
        output_dir = "visualizations"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        graph.render(filename=output_path, format='png', cleanup=True)
        print(f"✓ Граф ДКА сохранен как {output_path}.png")


class NFAGraphVisualizer:
    """Класс для визуализации НКА"""

    @staticmethod
    def _collect_nfa_states(start_state, visited=None):
        """Сбор всех состояний НКА"""
        if visited is None:
            visited = set()

        if start_state in visited:
            return visited

        visited.add(start_state)

        for symbol, states in start_state.transitions.items():
            for state in states:
                NFAGraphVisualizer._collect_nfa_states(state, visited)

        for state in start_state.epsilon_transitions:
            NFAGraphVisualizer._collect_nfa_states(state, visited)

        return visited

    @staticmethod
    def visualize_nfa(nfa, filename="nfa_graph"):
        """Визуализация недетерминированного конечного автомата"""
        graph = gv.Digraph(filename=filename, format='png')
        graph.attr(rankdir='LR', size='10,7')

        # Собираем все состояния
        all_states = NFAGraphVisualizer._collect_nfa_states(nfa.start)

        # Добавляем состояния
        for state in all_states:
            node_attrs = {}

            if state == nfa.start:
                node_attrs['style'] = 'filled'
                node_attrs['fillcolor'] = 'lightblue'

            if state.is_final:
                node_attrs['shape'] = 'doublecircle'
            else:
                node_attrs['shape'] = 'circle'

            graph.node(str(state.id), label=f"q{state.id}", **node_attrs)

        # Добавляем начальную стрелку
        graph.node('start', shape='point')
        graph.edge('start', str(nfa.start.id))

        # Добавляем переходы
        for state in all_states:
            for symbol, target_states in state.transitions.items():
                for target in target_states:
                    graph.edge(str(state.id), str(target.id), label=symbol)

            for target in state.epsilon_transitions:
                graph.edge(str(state.id), str(target.id), label='ε')

        # Сохраняем
        output_dir = "visualizations"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        graph.render(filename=output_path, format='png', cleanup=True)
        print(f"✓ Граф НКА сохранен как {output_path}.png")


def create_gif_from_visualizations():
    """Создать GIF из всех визуализаций в папке"""
    frames = []
    imgs = glob.glob("visualizations/*.png")
    if not imgs:
        print("⚠ Нет изображений для создания GIF")
        return

    for img_path in sorted(imgs):
        frames.append(Image.open(img_path))

    gif_path = "visualizations/automata_process.gif"
    frames[0].save(gif_path, format='GIF',
                   append_images=frames[1:],
                   save_all=True,
                   duration=1000, loop=0)
    print(f"✓ GIF создан: {gif_path}")


def visualize_regex_processing(regex, test_string=None):
    """Полная визуализация процесса от регулярного выражения до ДКА"""
    from main import RegexInterpreter

    interpreter = RegexInterpreter()

    try:
        # 1. Преобразование в обратную польскую запись
        postfix = interpreter.to_postfix(regex)
        print(f"✓ Обратная польская запись: {postfix}")

        # 2. Построение НКА
        print("Строим НКА...")
        nfa = interpreter.build_nfa_from_postfix(postfix)
        NFAGraphVisualizer.visualize_nfa(nfa, "nfa_graph")

        # 3. Преобразование в ДКА
        print("Преобразуем НКА в ДКА...")
        dfa = interpreter.nfa_to_dfa(nfa, regex)
        DFAGraphVisualizer.visualize_dfa(dfa, "dfa_graph")

        # 4. Тестирование строки (если указана)
        if test_string:
            print(f"\nТестируем строку: '{test_string}'")
            result = dfa.process_input(test_string)
            print(f"Результат: {'✓ ПРИНЯТА' if result else '✗ ОТВЕРГНУТА'}")

            # Визуализация пути
            if result:
                accepted, path = dfa.process_input_with_trace(test_string)
                print(f"Путь состояний: {' → '.join([f'q{s}' for s in path])}")

        create_gif_from_visualizations()

    except Exception as e:
        print(f"✗ Ошибка: {e}")


def interactive_visualization():
    """Интерактивный режим визуализации"""
    print("=" * 60)
    print("ВИЗУАЛИЗАТОР АВТОМАТОВ ДЛЯ РЕГУЛЯРНЫХ ВЫРАЖЕНИЙ")
    print("=" * 60)

    while True:
        print("\n" + "=" * 60)
        print("МЕНЮ ВИЗУАЛИЗАЦИИ:")
        print("1. Визуализировать регулярное выражение (НКА)")
        print("2. Построить и визуализировать НКА и ДКА")
        print("3. Анимированный поиск с помощью НКА")
        print("4. Создать GIF из всех визуализаций")
        print("5. Очистить папку визуализаций")
        print("6. Вернуться в главное меню")

        choice = input("\nВыберите действие (1-6): ").strip()

        if choice == '1':
            regex = input("Введите регулярное выражение: ").strip()
            if not regex:
                print("Ошибка: регулярное выражение не может быть пустым")
                continue

            try:
                engine = RegexEngine(regex)
                engine.draw_regex_nfa()
                print(f"✓ НКА для '{regex}' визуализирован")
            except Exception as e:
                print(f"✗ Ошибка: {e}")

        elif choice == '2':
            regex = input("Введите регулярное выражение: ").strip()
            if not regex:
                print("Ошибка: регулярное выражение не может быть пустым")
                continue

            test_string = input("Введите тестовую строку (или Enter для пропуска): ").strip()
            test_string = test_string if test_string else None

            visualize_regex_processing(regex, test_string)

        elif choice == '3':
            regex = input("Введите регулярное выражение для поиска: ").strip()
            if not regex:
                print("Ошибка: регулярное выражение не может быть пустым")
                continue

            text = input("Введите текст для поиска: ").strip()
            if not text:
                print("Ошибка: текст для поиска не может быть пустым")
                continue

            try:
                engine = RegexEngine(regex)
                print(f"\nПоиск '{regex}' в тексте: '{text}'")
                result = engine.search(text, filename_prefix="search_step_")
                print(f"Результат поиска: {'✓ НАЙДЕНО' if result else '✗ НЕ НАЙДЕНО'}")

                # Создать GIF из шагов поиска
                create_gif_from_visualizations()

            except Exception as e:
                print(f"✗ Ошибка: {e}")

        elif choice == '4':
            create_gif_from_visualizations()

        elif choice == '5':
            if os.path.exists("visualizations"):
                files = glob.glob("visualizations/*")
                for file in files:
                    try:
                        os.remove(file)
                    except:
                        pass
                print("✓ Папка визуализаций очищена")
            else:
                print("✓ Папка визуализаций не существует")

        elif choice == '6':
            print("Возврат в главное меню...")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")


def main():
    """Основная функция визуализатора"""
    interactive_visualization()


if __name__ == "__main__":
    main()