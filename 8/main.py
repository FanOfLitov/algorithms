import csv
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional


#   Структура узла дерева

@dataclass
class Node:
    value: str
    children: List["Node"] = field(default_factory=list)

    def add(self, child: "Node"):
        self.children.append(child)

#   КС-грамматика
grammar = {
    "E": [["E", "+", "T"], ["T"]],
    "T": [["T", "*", "F"], ["F"]],
    "F": [["(", "E", ")"], ["id"]]
}



#   Рекурсивный нисходящий разбор

class Parser:
    def __init__(self, tokens: List[str]):
        self.tokens = deque(tokens)

    def match(self, token: str) -> Optional[Node]:
        if self.tokens and self.tokens[0] == token:
            self.tokens.popleft()
            return Node(token)
        return None

    def parse_F(self) -> Optional[Node]:
        if (node := self.match("(")) is not None:
            E_node = self.parse_E()
            if E_node and (node2 := self.match(")")):
                root = Node("F", [Node("("), E_node, Node(")")])
                return root
            return None

        if (id_node := self.match("id")) is not None:
            return Node("F", [Node("id")])

        return None

    def parse_T(self) -> Optional[Node]:
        F_node = self.parse_F()
        if not F_node:
            return None

        root = Node("T", [F_node])

        while True:
            saved = list(self.tokens)
            if (op := self.match("*")):
                F2 = self.parse_F()
                if F2:
                    root = Node("T", [root, Node("*"), F2])
                else:
                    self.tokens = deque(saved)
                    break
            else:
                break

        return root

    def parse_E(self) -> Optional[Node]:
        T_node = self.parse_T()
        if not T_node:
            return None

        root = Node("E", [T_node])

        while True:
            saved = list(self.tokens)
            if (op := self.match("+")):
                T2 = self.parse_T()
                if T2:
                    root = Node("E", [root, Node("+"), T2])
                else:
                    self.tokens = deque(saved)
                    break
            else:
                break

        return root

    def parse(self) -> Optional[Node]:
        root = self.parse_E()
        if root and not self.tokens:
            return root
        return None



# ASCII-визуализация дерева

def print_tree(node: Node, indent: str = "", last=True):
    connector = "└─ " if last else "├─ "
    print(indent + connector + node.value)
    indent += "   " if last else "│  "
    for i, child in enumerate(node.children):
        print_tree(child, indent, i == len(node.children) - 1)



# Сохранение в CSV (parent, child)

def save_tree_csv(node: Node, filename="tree.csv"):
    rows = []

    def traverse(n: Node):
        for child in n.children:
            rows.append((n.value, child.value))
            traverse(child)

    traverse(node)

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["parent", "child"])
        writer.writerows(rows)

    print(f"CSV сохранён как {filename}")



#  визуализация

def export_graphviz(node: Node, filename="tree.gv"):
    from graphviz import Digraph
    dot = Digraph()

    def add(n: Node):
        dot.node(str(id(n)), n.value)
        for child in n.children:
            dot.edge(str(id(n)), str(id(child)))
            add(child)

    add(node)
    dot.render(filename, format="png", cleanup=True)
    print(f"Визуализация сохранена как {filename}.png")



# Тесты

def run_tests():
    examples = [
        ["id"],
        ["id", "+", "id"],
        ["id", "*", "id", "+", "id"],
        ["(", "id", ")", "*", "id"],
    ]

    for tokens in examples:
        print("\nТест:", tokens)
        parser = Parser(tokens)
        tree = parser.parse()
        if tree:
            print("Дерево построено:")
            print_tree(tree)
        else:
            print("Ошибка разбора!")





if __name__ == "__main__":
    tokens = ["id", "+", "id", "*", "id"]
    parser = Parser(tokens)
    tree = parser.parse()

    if tree:
        print("\nДЕРЕВО РАЗБОРА:\n")
        print_tree(tree)

        save_tree_csv(tree, "parse_tree.csv")
        export_graphviz(tree, "parse_tree")

        print("\n Тесты щаз будут")
        run_tests()
    else:
        print("Ошибка разбора!")
