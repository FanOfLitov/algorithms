import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QFileDialog, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QTreeView, QMessageBox, QFileSystemModel, QStandardItemModel,
    QStandardItem
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from xml_parser import parse_xml_file, XMLNode
from xml_lexer import XMLLexerError, XMLToken
import graphviz


class XMLTreeModel(QStandardItemModel):
    def __init__(self, root_node: XMLNode):
        super().__init__()
        self.setHorizontalHeaderLabels(["XML DOM Tree"])
        root_item = self.create_item(root_node)
        self.invisibleRootItem().appendRow(root_item)

    def create_item(self, node: XMLNode):
        if node.kind == "element":
            text = f"<{node.name}>"
        elif node.kind == "text":
            text = f"TEXT: {node.text}"
        elif node.kind == "comment":
            text = f"COMMENT: {node.text}"
        elif node.kind == "cdata":
            text = f"CDATA: {node.text}"
        else:
            text = f"UNKNOWN"

        item = QStandardItem(text)

        if node.kind == "element":
            # attributes as subnodes
            for k, v in node.attrs.items():
                a = QStandardItem(f"@{k} = \"{v}\"")
                item.appendRow(a)

            # children
            for ch in node.children:
                item.appendRow(self.create_item(ch))

        return item


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("XML Parser & Visualizer — PyQt5")
        self.resize(1400, 800)

        # DOM tree
        self.tree = QTreeView()
        self.tree.setHeaderHidden(False)

        # AST image
        self.label_graph = QLabel("AST Graph will appear here")
        self.label_graph.setAlignment(Qt.AlignCenter)

        # Buttons
        self.btn_load = QPushButton("Load XML")
        self.btn_load.clicked.connect(self.load_xml)

        self.btn_parse = QPushButton("Parse XML")
        self.btn_parse.clicked.connect(self.parse_xml)

        self.btn_graph = QPushButton("Show AST Graph")
        self.btn_graph.clicked.connect(self.show_graph)

        self.xml_path = None
        self.dom_root = None

        # Layout
        left = QVBoxLayout()
        left.addWidget(self.tree)

        right = QVBoxLayout()
        right.addWidget(self.label_graph)

        h = QHBoxLayout()
        h.addLayout(left, 1)
        h.addLayout(right, 1)

        buttons = QHBoxLayout()
        buttons.addWidget(self.btn_load)
        buttons.addWidget(self.btn_parse)
        buttons.addWidget(self.btn_graph)

        main = QVBoxLayout()
        main.addLayout(h, 1)
        main.addLayout(buttons)

        self.setLayout(main)

    # ---------------------------------------------------------------
    # LOAD XML
    # ---------------------------------------------------------------
    def load_xml(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open XML", "", "XML files (*.xml)")
        if not path:
            return
        self.xml_path = path
        QMessageBox.information(self, "Loaded", f"Loaded file:\n{path}")

    # ---------------------------------------------------------------
    # PARSE XML
    # ---------------------------------------------------------------
    def parse_xml(self):
        if not self.xml_path:
            QMessageBox.warning(self, "Error", "Please load an XML file first.")
            return

        try:
            self.dom_root = parse_xml_file(self.xml_path)
        except Exception as e:
            QMessageBox.critical(self, "Parsing Error", str(e))
            return

        model = XMLTreeModel(self.dom_root)
        self.tree.setModel(model)
        QMessageBox.information(self, "Success", "XML parsed successfully.")

    # ---------------------------------------------------------------
    # SHOW AST GRAPH
    # ---------------------------------------------------------------
    def show_graph(self):
        if not self.dom_root:
            QMessageBox.warning(self, "Error", "Parse XML first.")
            return

        png_path = self.generate_graph(self.dom_root)
        pixmap = QPixmap(png_path).scaled(
            self.label_graph.width(),
            self.label_graph.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.label_graph.setPixmap(pixmap)

    # ---------------------------------------------------------------
    # GENERATE GRAPHVIZ AST
    # ---------------------------------------------------------------
    def generate_graph(self, root_node):
        dot = graphviz.Digraph("XML_AST")
        dot.attr(rankdir="TB", fontsize="12")

        def add(node, parent_id=None):
            nid = str(id(node))

            if node.kind == "element":
                label = f"<{node.name}>"
            elif node.kind == "text":
                label = f"TEXT: {node.text}"
            elif node.kind == "comment":
                label = f"COMMENT: {node.text}"
            elif node.kind == "cdata":
                label = f"CDATA: {node.text}"
            else:
                label = "UNKNOWN"

            dot.node(nid, label)

            if parent_id:
                dot.edge(parent_id, nid)

            # attributes as child nodes
            if node.kind == "element":
                for k, v in node.attrs.items():
                    aid = f"{nid}-{k}"
                    dot.node(aid, f"@{k}=\"{v}\"", shape="box")
                    dot.edge(nid, aid)

            # children
            for ch in node.children:
                add(ch, nid)

        add(root_node)
        out = dot.render("xml_ast", format="png", cleanup=True)
        return out


# ------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
