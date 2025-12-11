import csv
import graphviz
import os
from collections import defaultdict, deque


class DFA:
    def __init__(self, states, alphabet, transitions, start, accept):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions
        self.start_state = start
        self.accept_states = set(accept)

    def reachable_states(self):
        reach = set()
        stack = [self.start_state]
        while stack:
            s = stack.pop()
            if s not in reach:
                reach.add(s)
                for sym in self.alphabet:
                    t = self.transitions[s][sym]
                    stack.append(t)
        return reach


def read_dfa_from_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    alphabet = rows[0][1:-1]
    states = set()
    transitions = {}
    start_state = None
    accept_states = set()

    for i, row in enumerate(rows[1:]):
        state = row[0].strip()
        states.add(state)
        if i == 0:
            start_state = state
        if row[-1].strip() == "*":
            accept_states.add(state)

        trans = {}
        for j, sym in enumerate(alphabet):
            tgt = row[j + 1].strip()
            trans[sym] = tgt if tgt else None
        transitions[state] = trans

    # Автодобавление ловушки
    if any(None in transitions[s].values() for s in states):
        trap = "trap"
        states.add(trap)
        transitions[trap] = {sym: trap for sym in alphabet}

        for s in transitions:
            for sym in alphabet:
                if transitions[s][sym] is None:
                    transitions[s][sym] = trap

    return DFA(states, alphabet, transitions, start_state, accept_states)


def minimize_table(dfa, log_steps=False):
    log = []
    P = [set(dfa.accept_states), dfa.states - set(dfa.accept_states)]
    P = [p for p in P if p]

    changed = True
    step = 1
    while changed:
        changed = False
        newP = []
        for group in P:
            if len(group) <= 1:
                newP.append(group)
                continue

            buckets = {}
            for st in group:
                signature = tuple(
                    next(i for i, blk in enumerate(P) if dfa.transitions[st][sym] in blk)
                    for sym in sorted(dfa.alphabet)
                )
                buckets.setdefault(signature, set()).add(st)

            if len(buckets) > 1:
                changed = True
                if log_steps:
                    log.append(f"Шаг {step}: блок {group} разделён → {list(buckets.values())}")
                step += 1

            newP.extend(buckets.values())
        P = newP

    return build_new_dfa(dfa, P), log


def minimize_hopcroft(dfa, log_steps=False):
    log = []
    P = [set(dfa.accept_states), dfa.states - set(dfa.accept_states)]
    P = [b for b in P if b]

    W = deque(P.copy())
    step = 1

    while W:
        A = W.popleft()
        for sym in dfa.alphabet:
            X = {s for s in dfa.states if dfa.transitions[s][sym] in A}

            newP = []
            for Y in P:
                inter = Y & X
                diff = Y - X
                if inter and diff:
                    if log_steps:
                        log.append(f"Шаг {step}: {Y} разделено на {inter} и {diff} по символу {sym}")
                    step += 1

                    newP.append(inter)
                    newP.append(diff)
                    if Y in W:
                        W.remove(Y)
                        W.append(inter)
                        W.append(diff)
                    else:
                        W.append(inter if len(inter) <= len(diff) else diff)
                else:
                    newP.append(Y)
            P = newP

    return build_new_dfa(dfa, P), log


def build_new_dfa(dfa, P):
    state_to_block = {}
    for i, block in enumerate(P):
        for s in block:
            state_to_block[s] = f"B{i}"

    new_states = set(state_to_block.values())
    new_trans = {ns: {} for ns in new_states}
    new_accept = set()
    new_start = state_to_block[dfa.start_state]

    for block in P:
        rep = next(iter(block))
        new_state = state_to_block[rep]
        if rep in dfa.accept_states:
            new_accept.add(new_state)
        for sym in dfa.alphabet:
            tgt = dfa.transitions[rep][sym]
            new_trans[new_state][sym] = state_to_block[tgt]

    # Убираем недостижимые
    new_dfa = DFA(new_states, dfa.alphabet, new_trans, new_start, new_accept)
    reach = new_dfa.reachable_states()
    new_dfa.states = reach
    new_dfa.transitions = {s: new_trans[s] for s in reach}
    new_dfa.accept_states = new_accept & reach

    return new_dfa


def visualize_dfa(dfa, filename, title):
    dot = graphviz.Digraph(title)
    dot.attr(rankdir="LR")

    dot.node("start", shape="point")

    for s in dfa.states:
        shape = "doublecircle" if s in dfa.accept_states else "circle"
        dot.node(s, s, shape=shape)

    dot.edge("start", dfa.start_state)

    for s in dfa.transitions:
        to_map = defaultdict(list)
        for sym, tgt in dfa.transitions[s].items():
            to_map[tgt].append(sym)
        for tgt, syms in to_map.items():
            dot.edge(s, tgt, label=", ".join(syms))

    dot.render(filename=filename, format="png", cleanup=True)
    return filename + ".png"


def visualize_both(dfa1, dfa2, filename):
    dot = graphviz.Digraph("Comparison")
    dot.attr(rankdir="LR")

    # Исходный
    with dot.subgraph(name="cluster1") as c:
        c.attr(label="Исходный DFA", color="blue")
        c.node("start1", shape="point")
        for s in dfa1.states:
            shape = "doublecircle" if s in dfa1.accept_states else "circle"
            c.node("o" + s, s, shape=shape)
        c.edge("start1", "o" + dfa1.start_state)
        for s in dfa1.states:
            for sym, tgt in dfa1.transitions[s].items():
                c.edge("o" + s, "o" + tgt, label=sym)

    # Минимизированный
    with dot.subgraph(name="cluster2") as c:
        c.attr(label="Минимизированный DFA", color="green")
        c.node("start2", shape="point")
        for s in dfa2.states:
            shape = "doublecircle" if s in dfa2.accept_states else "circle"
            c.node("m" + s, s, shape=shape)
        c.edge("start2", "m" + dfa2.start_state)
        for s in dfa2.states:
            for sym, tgt in dfa2.transitions[s].items():
                c.edge("m" + s, "m" + tgt, label=sym)

    dot.render(filename=filename, format="png", cleanup=True)
    return filename + ".png"
