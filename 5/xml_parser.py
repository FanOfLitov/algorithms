from xml_lexer import XMLToken, XMLLexerError, XMLLexer


class XMLParserError(Exception):
    pass


class XMLNode:
    def __init__(self, kind, name=None, text=None, attrs=None, children=None):
        self.kind = kind            # element, text, comment, cdata
        self.name = name            # tag name
        self.text = text            # for text/comment/cdata
        self.attrs = attrs or {}    # dict
        self.children = children or []

    def __repr__(self):
        if self.kind == "element":
            return f"<Element {self.name} attrs={self.attrs} children={len(self.children)}>"
        elif self.kind == "text":
            return f"<Text {self.text!r}>"
        elif self.kind == "comment":
            return f"<Comment {self.text!r}>"
        elif self.kind == "cdata":
            return f"<CData {self.text!r}>"


class XMLParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    def peek(self):
        if self.i < len(self.tokens):
            return self.tokens[self.i]
        return None

    def advance(self):
        tok = self.peek()
        self.i += 1
        return tok

    def error(self, msg):
        raise XMLParserError(f"[token {self.i}] {msg}")

    # ----------------------------------------------------------------------

    def parse(self):
        """Document → Prolog? Element"""
        if self.peek() and self.peek().type == "PROLOG":
            self.advance()  # skip

        elem = self.parse_element()

        if self.peek() is not None:
            self.error("Extra content after root element")

        return elem

    # ----------------------------------------------------------------------

    def parse_element(self):
        tok = self.peek()
        if tok is None:
            self.error("Unexpected end of tokens")

        # <tag ...>
        if tok.type == "STARTTAG":
            _, (name, attrs) = tok.type, tok.value
            self.advance()

            children = self.parse_content()

            # expecting </tag>
            endtag = self.advance()
            if endtag.type != "ENDTAG":
                self.error("Expected closing tag")
            if endtag.value != name:
                self.error(f"Mismatched closing tag: </{endtag.value}> for <{name}>")

            return XMLNode("element", name=name, attrs=attrs, children=children)

        # <tag .../>
        elif tok.type == "SELFCLOSE":
            _, (name, attrs) = tok.type, tok.value
            self.advance()
            return XMLNode("element", name=name, attrs=attrs, children=[])

        self.error("Expected element start")

    # ----------------------------------------------------------------------

    def parse_content(self):
        """content → (TEXT | COMMENT | CDATA | element)*"""

        children = []
        while True:
            tok = self.peek()
            if tok is None:
                self.error("Unexpected end, missing closing tag")

            if tok.type == "TEXT":
                children.append(XMLNode("text", text=tok.value))
                self.advance()

            elif tok.type == "COMMENT":
                children.append(XMLNode("comment", text=tok.value))
                self.advance()

            elif tok.type == "CDATA":
                children.append(XMLNode("cdata", text=tok.value))
                self.advance()

            elif tok.type in ("STARTTAG", "SELFCLOSE"):
                children.append(self.parse_element())

            else:
                break

        return children


# ----------------------------------------------------------------------
# Convenience API
# ----------------------------------------------------------------------

def parse_xml_string(text):
    lexer = XMLLexer(text)
    try:
        tokens = lexer.tokenize()
    except XMLLexerError as e:
        raise XMLParserError(f"Lexer error: {e}")

    parser = XMLParser(tokens)
    return parser.parse()


def parse_xml_file(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return parse_xml_string(text)
