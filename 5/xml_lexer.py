import re

class XMLToken:
    def __init__(self, type, value=None, pos=None):
        self.type = type
        self.value = value
        self.pos = pos

    def __repr__(self):
        if self.value is None:
            return f"<{self.type}>"
        return f"<{self.type}: {self.value}>"


class XMLLexerError(Exception):
    pass


class XMLLexer:
    """
    Полный XML-лексер на Python.
    Поддерживает:
    - <?xml ... ?>
    - <!-- comment -->
    - <![CDATA[ ... ]]>
    - <tag ...>
    - </tag>
    - <tag/>
    - text nodes
    - атрибуты
    - сущности &lt; &gt; &amp; &apos; &quot;
    """

    ENTITY_MAP = {
        "&lt;": "<",
        "&gt;": ">",
        "&amp;": "&",
        "&quot;": "\"",
        "&apos;": "'",
    }

    def __init__(self, text):
        self.text = text
        self.i = 0
        self.n = len(text)

    def peek(self, k=0):
        if self.i + k < self.n:
            return self.text[self.i + k]
        return None

    def advance(self, k=1):
        self.i += k

    def match(self, s):
        """Если текст впереди начинается с s — вернуть True и сдвинуть указатель."""
        if self.text.startswith(s, self.i):
            self.i += len(s)
            return True
        return False

    def error(self, msg):
        raise XMLLexerError(f"[pos={self.i}] {msg}")

    def tokenize(self):
        tokens = []

        while self.i < self.n:
            c = self.peek()

            # whitespace between tokens → можно игнорировать
            if c.isspace():
                self.advance()
                continue

            # XML prolog
            if self.match("<?xml"):
                end = self.text.find("?>", self.i)
                if end == -1:
                    self.error("Unclosed XML prolog")
                tokens.append(XMLToken("PROLOG", self.text[self.i:end].strip()))
                self.i = end + 2
                continue

            # comment <!-- ... -->
            if self.match("<!--"):
                end = self.text.find("-->", self.i)
                if end == -1:
                    self.error("Unclosed comment")
                comment = self.text[self.i:end]
                tokens.append(XMLToken("COMMENT", comment.strip()))
                self.i = end + 3
                continue

            # CDATA <![CDATA[ ... ]]>
            if self.match("<![CDATA["):
                end = self.text.find("]]>", self.i)
                if end == -1:
                    self.error("Unclosed CDATA")
                data = self.text[self.i:end]
                tokens.append(XMLToken("CDATA", data))
                self.i = end + 3
                continue

            # closing tag </tag>
            if self.match("</"):
                name = self.read_tag_name()
                self.skip_spaces()
                if not self.match(">"):
                    self.error("Expected '>'")
                tokens.append(XMLToken("ENDTAG", name))
                continue

            # self-closing <tag .../>
            if self.match("<"):
                name = self.read_tag_name()
                attrs = self.read_attributes()

                self.skip_spaces()

                if self.match("/>"):
                    tokens.append(XMLToken("SELFCLOSE", (name, attrs)))
                elif self.match(">"):
                    tokens.append(XMLToken("STARTTAG", (name, attrs)))
                else:
                    self.error("Expected '>' or '/>'")
                continue

            # текстовые узлы + сущности
            txt = self.read_text()
            if txt.strip() != "":
                tokens.append(XMLToken("TEXT", txt))
            continue

        return tokens

    # --------------------------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------------------------

    def skip_spaces(self):
        while self.peek() and self.peek().isspace():
            self.advance()

    def read_tag_name(self):
        start = self.i
        while (ch := self.peek()) and (ch.isalnum() or ch in "_:-."):
            self.advance()
        if self.i == start:
            self.error("Tag name expected")
        return self.text[start:self.i]

    def read_attributes(self):
        attrs = {}
        while True:
            self.skip_spaces()
            ch = self.peek()
            if not ch or ch in ['>', '/']:
                break
            name = self.read_tag_name()

            self.skip_spaces()
            if not self.match("="):
                self.error("Expected '=' after attribute name")

            self.skip_spaces()
            val = self.read_attr_value()

            attrs[name] = val

        return attrs

    def read_attr_value(self):
        if not self.match("\""):
            self.error("Attribute value must start with '\"'")
        start = self.i
        while True:
            ch = self.peek()
            if ch is None:
                self.error("Unterminated attribute value")
            if ch == "\"":
                val = self.text[start:self.i]
                self.advance()  # skip closing quote
                return val
            self.advance()

    def read_text(self):
        start = self.i
        while True:
            if self.peek() is None or self.text.startswith("<", self.i):
                break
            self.advance()
        txt = self.text[start:self.i]

        # replace XML entities
        for ent, repl in self.ENTITY_MAP.items():
            txt = txt.replace(ent, repl)
        return txt


