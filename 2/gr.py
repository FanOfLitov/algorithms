import networkx as nx
import matplotlib.pyplot as plt


def draw_nfa_networkx(transitions_data, start_state, final_states, filename="nfa_diagram_nx.png"):
    G = nx.MultiDiGraph()

    # Добавляем узлы
    all_states = set(transitions_data.keys())
    for transitions in transitions_data.values():
        for targets in transitions.values():
            for target in targets:
                if target:
                    all_states.add(target)

    G.add_nodes_from(all_states)

    # Добавляем ребра
    edge_labels = {}
    for source_state, transitions in transitions_data.items():
        for symbol, target_states in transitions.items():
            for target_state in target_states:
                if target_state:
                    edge = (source_state, target_state)
                    if edge not in edge_labels:
                        edge_labels[edge] = []
                    edge_labels[edge].append(symbol)
                    G.add_edge(source_state, target_state, label=symbol)


    pos = nx.spring_layout(G, k=0.5, iterations=50)  # k - расстояние между узлами

    plt.figure(figsize=(8, 6))

    # Рисуем узлы
    nx.draw_networkx_nodes(G, pos, nodelist=list(all_states - set(final_states)), node_color='lightblue',
                           node_shape='o', node_size=2000)
    nx.draw_networkx_nodes(G, pos, nodelist=final_states, node_color='lightgreen', node_shape='o',
                           node_size=2500)  # Конечное состояние
    nx.draw_networkx_labels(G, pos, font_size=10)


    nx.draw_networkx_edges(G, pos, edgelist=G.edges, arrowstyle='->', arrowsize=20, edge_color='gray')

    for (u, v), labels in edge_labels.items():
        label = ", ".join(labels)
        # Чтобы метки не накладывались, можно сдвигать их
        x, y = (pos[u][0] + pos[v][0]) / 2, (pos[u][1] + pos[v][1]) / 2
        # Дополнительный сдвиг для петель (q3 -> q3)
        if u == v:
            x_offset = 0.1
            y_offset = 0.1
            plt.text(x + x_offset, y + y_offset, label, fontsize=10, color='red', ha='center', va='center')
        else:
            plt.text(x, y, label, fontsize=10, color='red', ha='center', va='center')


    x, y = pos[start_state]
    plt.text(x - 0.2, y + 0.1, "Start", fontsize=10, color='blue', ha='right', va='center')

    plt.title("NFA Diagram (NetworkX)")
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(filename)
    plt.show()
    print(f"Диаграмма сохранена как {filename}")


nfa_transitions = {
    'q0': {'a': ['q1'], 'b': ['q2'], 'ε': []},
    'q1': {'a': [], 'b': ['q3'], 'ε': []},
    'q2': {'a': ['q3'], 'b': [], 'ε': []},
    'q3': {'a': ['q3'], 'b': ['q3'], 'ε': []}
}

start_state = 'q0'
final_states = ['q3']


