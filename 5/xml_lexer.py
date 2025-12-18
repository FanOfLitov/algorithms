# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class XMLToken:
    type: str
    value: Any = None
    pos: int = 0

    def __repr__(self) -> str:
        if self.value is None:
            return f"<{self.type}@{self.pos}>"
        return f"<{self.type}@{self.pos}: {self.value!r}>"


class XMLLexerError(Exception):
    pass


class XMLLexer:
    ENTITY_MAP = {
        "&lt;": "<",
        "&gt;": ">",
        "&amp;": "&",
        "&quot;": '"',
        "&apos;": "'",
    }

    def __init__(self, text: str):
        self.text = text or ""
        self.i = 0
        self.n = len(self.text)

    def _error(self, msg: str) -> None:
        raise XMLLexerError(f"[pos {self.i}] {msg}")

    def _peek(self, k: int = 0) -> Optional[str]:
        j = self.i + k
        if j >= self.n:
            return None
        return self.text[j]

    def _starts(self, s: str) -> bool:
        return self.text.startswith(s, self.i)

    def _advance(self, k: int = 1) -> None:
        self.i += k

    def _skip_ws(self) -> None:
        while (c := self._peek()) is not None and c.isspace():
            self._advance()

    def _read_until(self, needle: str) -> str:
        j = self.text.find(needle, self.i)
        if j == -1:
            self._error(f"Unclosed construct, expected {needle!r}")
        s = self.text[self.i:j]
        self.i = j + len(needle)
        return s

    def _unescape(self, s: str) -> str:
        for ent, repl in self.ENTITY_MAP.items():
            s = s.replace(ent, repl)
        return s

    def _read_name(self) -> str:
        c = self._peek()
        if c is None:
            self._error("Unexpected EOF while reading name")
        if not (c.isalpha() or c in "_:"):
            self._error("Tag name expected")
        start = self.i
        self._advance()
        while (c := self._peek()) is not None and (c.isalnum() or c in "_.:-"):
            self._advance()
        return self.text[start:self.i]

    def _read_quoted_value(self) -> str:
        q = self._peek()
        if q not in ("'", '"'):
            self._error("Attribute value must be quoted")
        self._advance()
        start = self.i
        while True:
            c = self._peek()
            if c is None:
                self._error("Unclosed attribute value")
            if c == q:
                val = self.text[start:self.i]
                self._advance()
                return self._unescape(val)
            self._advance()

    def _read_text_node(self) -> str:
        start = self.i
        while (c := self._peek()) is not None and c != "<":
            self._advance()
        return self._unescape(self.text[start:self.i])

    def _read_doctype(self) -> str:
        # now at "<!DOCTYPE"
        start_pos = self.i
        self._advance(len("<!DOCTYPE"))

        bracket_depth = 0
        in_quote: Optional[str] = None
        buf_start = self.i

        while True:
            c = self._peek()
            if c is None:
                self.i = start_pos
                self._error("Unclosed DOCTYPE")

            if in_quote:
                if c == in_quote:
                    in_quote = None
                self._advance()
                continue

            if c in ("'", '"'):
                in_quote = c
                self._advance()
                continue

            if c == "[":
                bracket_depth += 1
                self._advance()
                continue

            if c == "]" and bracket_depth > 0:
                bracket_depth -= 1
                self._advance()
                continue

            if c == ">" and bracket_depth == 0:
                inner = self.text[buf_start:self.i].strip()
                self._advance()  # consume '>'
                return inner

            self._advance()

    def tokenize(self) -> List[XMLToken]:
        tokens: List[XMLToken] = []

        while self.i < self.n:
            c = self._peek()
            if c is None:
                break

            if c != "<":
                pos = self.i
                txt = self._read_text_node()
                if txt != "":
                    tokens.append(XMLToken("TEXT", txt, pos))
                continue

            pos = self.i

            # prolog
            if self._starts("<?xml"):
                self._advance(len("<?xml"))
                inner = self._read_until("?>").strip()
                tokens.append(XMLToken("PROLOG", inner, pos))
                continue

            # processing instruction
            if self._starts("<?"):
                self._advance(2)
                inner = self._read_until("?>").strip()
                tokens.append(XMLToken("PI", inner, pos))
                continue

            # comment
            if self._starts("<!--"):
                self._advance(len("<!--"))
                inner = self._read_until("-->")
                tokens.append(XMLToken("COMMENT", inner, pos))
                continue

            # CDATA
            if self._starts("<![CDATA["):
                self._advance(len("<![CDATA["))
                inner = self._read_until("]]>")
                tokens.append(XMLToken("CDATA", inner, pos))
                continue

            # DOCTYPE (включая внутренний subset)
            if self._starts("<!DOCTYPE"):
                inner = self._read_doctype()
                tokens.append(XMLToken("DOCTYPE", inner, pos))
                continue

            # любые другие декларации <!ELEMENT ...>, <!ATTLIST ...> (если вдруг встретятся отдельно)
            if self._starts("<!"):
                self._advance(2)
                inner = self._read_until(">")
                tokens.append(XMLToken("DECL", inner.strip(), pos))
                continue

            # end tag
            if self._starts("</"):
                self._advance(2)
                self._skip_ws()
                name = self._read_name()
                self._skip_ws()
                if self._peek() != ">":
                    self._error("Expected '>' after end tag")
                self._advance()
                tokens.append(XMLToken("END_TAG", name, pos))
                continue

            # start tag
            if self._starts("<"):
                self._advance(1)
                self._skip_ws()
                name = self._read_name()
                attrs: Dict[str, str] = {}
                self._skip_ws()

                while True:
                    c2 = self._peek()
                    if c2 is None:
                        self._error("Unclosed start tag")
                    if c2 in (">", "/"):
                        break

                    attr_name = self._read_name()
                    self._skip_ws()
                    if self._peek() != "=":
                        self._error("Expected '=' after attribute name")
                    self._advance()
                    self._skip_ws()
                    attr_val = self._read_quoted_value()
                    attrs[attr_name] = attr_val
                    self._skip_ws()

                self_closing = False
                if self._peek() == "/":
                    self._advance()
                    if self._peek() != ">":
                        self._error("Expected '/>' for self-closing tag")
                    self._advance()
                    self_closing = True
                else:
                    if self._peek() != ">":
                        self._error("Expected '>' to close start tag")
                    self._advance()

                tokens.append(
                    XMLToken(
                        "START_TAG",
                        {"name": name, "attrs": attrs, "self_closing": self_closing},
                        pos,
                    )
                )
                continue

            self._error("Unexpected character")

        tokens.append(XMLToken("EOF", None, self.i))
        return tokens
