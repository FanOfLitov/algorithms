from graphviz import Digraph
from loader import load_transitions


def visualize(csv_file: str, out_file="graph"):
    transitions = load_transitions(csv_file)
    dot = Digraph(comment="Turing Machine")

    for (state, read), t in transitions.items():
        label = f"{read} → {t.write}, {t.move}"
        dot.edge(state, t.next_state, label=label)

    dot.render(out_file, format="png", cleanup=True)
    return out_file + ".png"
