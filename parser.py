# -*- coding: utf-8 -*-
"""Predictive Recursive Descent parser with panic-mode recovery."""

from __future__ import annotations

from typing import List

from scanner import Token, Scanner
from parse_tree import PTNode
from grammar import FOLLOW, NONTERMINALS, PARSE_TABLE, EPS


def token_to_terminal(tok: Token) -> str:
    if tok.typ == "ID":
        return "ID"
    if tok.typ == "NUM":
        return "NUM"
    if tok.typ == "KEYWORD":
        return tok.lex
    if tok.typ == "SYMBOL":
        return tok.lex
    return "$"  # EOF


def token_display(tok: Token) -> str:
    if tok.typ == "EOF":
        return "$"
    if tok.typ == "ID":
        return f"(ID, {tok.lex})"
    if tok.typ == "NUM":
        return f"(NUM, {tok.lex})"
    if tok.typ == "KEYWORD":
        return f"(KEYWORD, {tok.lex})"
    if tok.typ == "SYMBOL":
        return f"(SYMBOL, {tok.lex})"
    return tok.lex


class Parser:
    def __init__(self, scanner: Scanner):
        self.scanner = scanner
        self.lookahead: Token = self.scanner.get_next_token()
        self.errors: List[str] = []
        self.stopped: bool = False

    @property
    def la_term(self) -> str:
        return token_to_terminal(self.lookahead)

    def advance(self) -> None:
        self.lookahead = self.scanner.get_next_token()

    def _err_illegal(self, tok: Token) -> None:
        t = token_to_terminal(tok)
        shown = t if t in ("ID", "NUM", "$") else t
        self.errors.append(f"#{tok.line} : syntax error, illegal {shown}")

    def _err_missing(self, line: int, sym: str) -> None:
        self.errors.append(f"#{line} : syntax error, missing {sym}")

    def _err_unexpected_eof(self, line: int) -> None:
        self.errors.append(f"#{line} : syntax error, Unexpected EOF")

    def match(self, expected: str, parent: PTNode) -> None:
        if self.stopped:
            return

        if self.la_term == expected:
            parent.add(PTNode(token_display(self.lookahead)))
            self.advance()
            return

        if self.la_term == "$":
            self._err_unexpected_eof(self.lookahead.line)
            self.stopped = True
            return

        # Mismatch: report missing, but do not consume and do not add a node
        self._err_missing(self.lookahead.line, expected)

    def parse_nonterminal(self, A: str, parent: PTNode) -> bool:
        if self.stopped:
            return False

        while True:
            look = self.la_term
            prod = PARSE_TABLE[A].get(look)

            if prod is not None:
                node = PTNode(A)
                parent.add(node)

                if prod == [EPS]:
                    node.add(PTNode("epsilon"))
                    return True

                i = 0
                while i < len(prod):
                    sym = prod[i]
                    if self.stopped:
                        break
                    if sym in NONTERMINALS:
                        self.parse_nonterminal(sym, node)
                    else:
                        self.match(sym, node)
                    i += 1

                return True

            # Panic mode
            if look in FOLLOW[A]:
                self._err_missing(self.lookahead.line, A)
                return False

            if look == "$":
                self._err_unexpected_eof(self.lookahead.line)
                self.stopped = True
                return False

            self._err_illegal(self.lookahead)
            self.advance()

    def parse(self) -> PTNode:
        root = PTNode("Program")
        self.parse_nonterminal("Declaration-list", root)

        if not self.stopped:
            while self.la_term != "$":
                self._err_illegal(self.lookahead)
                self.advance()
            root.add(PTNode("$"))

        return root
