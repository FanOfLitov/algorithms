# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from xml_lexer import XMLLexer, XMLLexerError, XMLToken


class XMLParserError(Exception):
    pass


@dataclass
class XMLNode:
    kind: str                      # element | text | comment | cdata | pi | prolog | doctype
    name: Optional[str] = None     # for element
    text: Optional[str] = None     # for text/comment/cdata/etc
    attrs: Dict[str, str] = field(default_factory=dict)
    children: List["XMLNode"] = field(default_factory=list)


class _Parser:
    def __init__(self, tokens: List[XMLToken]):
        self.tokens = tokens
        self.k = 0

    def _cur(self) -> XMLToken:
        if self.k >= len(self.tokens):
            return XMLToken("EOF", None, self.tokens[-1].pos if self.tokens else 0)
        return self.tokens[self.k]

    def _eat(self, t: str) -> XMLToken:
        tok = self._cur()
        if tok.type != t:
            raise XMLParserError(f"[token {self.k}] Expected {t}, got {tok.type} at pos {tok.pos}")
        self.k += 1
        return tok

    def _skip_misc(self) -> None:
        # пропускаем служебное и пробельный текст на верхнем уровне
        while True:
            tok = self._cur()
            if tok.type in ("PROLOG", "DOCTYPE", "PI", "COMMENT", "DECL"):
                self.k += 1
                continue
            if tok.type == "TEXT" and str(tok.value or "").strip() == "":
                self.k += 1
                continue
            break

    def parse_document(self) -> XMLNode:
        self._skip_misc()
        if self._cur().type != "START_TAG":
            tok = self._cur()
            raise XMLParserError(f"[token {self.k}] Expected element start, got {tok.type} at pos {tok.pos}")

        root = self.parse_element()

        self._skip_misc()
        if self._cur().type != "EOF":
            tok = self._cur()
            raise XMLParserError(f"[token {self.k}] Unexpected token {tok.type} at pos {tok.pos}")

        return root

    def parse_element(self) -> XMLNode:
        start = self._eat("START_TAG")
        info: Any = start.value or {}
        name = info.get("name")
        attrs = dict(info.get("attrs") or {})
        self_closing = bool(info.get("self_closing"))

        node = XMLNode("element", name=name, attrs=attrs)

        if self_closing:
            return node

        while True:
            tok = self._cur()

            if tok.type == "TEXT":
                self.k += 1
                txt = str(tok.value or "")
                if txt.strip() != "":
                    node.children.append(XMLNode("text", text=txt))
                continue

            if tok.type == "COMMENT":
                self.k += 1
                node.children.append(XMLNode("comment", text=str(tok.value or "")))
                continue

            if tok.type == "CDATA":
                self.k += 1
                node.children.append(XMLNode("cdata", text=str(tok.value or "")))
                continue

            if tok.type == "PI":
                self.k += 1
                node.children.append(XMLNode("pi", text=str(tok.value or "")))
                continue

            if tok.type == "DECL":
                self.k += 1
                continue

            if tok.type == "START_TAG":
                node.children.append(self.parse_element())
                continue

            if tok.type == "END_TAG":
                end = self._eat("END_TAG")
                if end.value != name:
                    raise XMLParserError(
                        f"[token {self.k-1}] Mismatched end tag </{end.value}> for <{name}> (pos {end.pos})"
                    )
                return node

            if tok.type == "EOF":
                raise XMLParserError(f"[token {self.k}] Unexpected EOF, expected </{name}>")

            raise XMLParserError(f"[token {self.k}] Unexpected token {tok.type} at pos {tok.pos}")


def parse_xml_string(text: str) -> XMLNode:
    try:
        tokens = XMLLexer(text).tokenize()
    except XMLLexerError as e:
        raise XMLParserError(f"Lexer error: {e}") from e

    return _Parser(tokens).parse_document()


def parse_xml_file(path: str) -> XMLNode:
    with open(path, "r", encoding="utf-8") as f:
        return parse_xml_string(f.read())
