# -*- coding: utf-8 -*-
"""Scanner for C-minus (pipeline-friendly)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Set


KEYWORDS: Set[str] = {"break", "else", "for", "if", "int", "return", "void"}
WHITESPACE: Set[str] = {" ", "\n", "\r", "\t", "\v", "\f"}

# Used as "safe boundaries" when we decide to skip a garbage chunk
BOUNDARY_SYMBOLS: Set[str] = {";", ":", ",", "[", "]", "(", ")", "{", "}", "+", "-", "*", "/", "=", "<"}


def _is_letter(ch: str) -> bool:
    return bool(ch) and ch.isalpha()


def _is_digit(ch: str) -> bool:
    return bool(ch) and ch.isdigit()


def _is_alnum_or_underscore(ch: str) -> bool:
    return bool(ch) and (ch.isalnum() or ch == "_")


@dataclass
class Token:
    typ: str    # KEYWORD, ID, NUM, SYMBOL, EOF
    lex: str
    line: int


class Scanner:
    # One-character symbols returned as SYMBOL tokens
    SINGLE_SYMBOLS: Set[str] = {";", ":", ",", "[", "]", "(", ")", "{", "}", "+", "-", "<"}

    def __init__(self, src: str):
        self.src = src
        self.n = len(src)
        self.pos = 0
        self.line = 1

    def peek(self, k: int = 1) -> str:
        if self.pos >= self.n:
            return ""
        return self.src[self.pos:self.pos + k]

    def advance(self, k: int = 1) -> str:
        grabbed = ""
        steps = 0
        while steps < k:
            if self.pos >= self.n:
                return grabbed
            ch = self.src[self.pos]
            self.pos += 1
            grabbed += ch
            if ch == "\n":
                self.line += 1
            steps += 1
        return grabbed

    def get_next_token(self) -> Token:
        while True:
            start_line = self.line
            ch = self.peek(1)

            if not ch:
                return Token("EOF", "$", self.line)

            if ch in WHITESPACE:
                self.advance(1)
                continue

            # ID / KEYWORD
            if _is_letter(ch) or ch == "_":
                lexeme = self.advance(1)
                while _is_alnum_or_underscore(self.peek(1)):
                    lexeme += self.advance(1)

                # If garbage is stuck to an identifier, skip it up to a boundary
                nxt = self.peek(1)
                if nxt and (nxt not in WHITESPACE) and (nxt not in BOUNDARY_SYMBOLS) and (not _is_alnum_or_underscore(nxt)):
                    while True:
                        t = self.peek(1)
                        if (not t) or (t in WHITESPACE) or (t in BOUNDARY_SYMBOLS):
                            break
                        self.advance(1)
                    continue

                if lexeme in KEYWORDS:
                    return Token("KEYWORD", lexeme, start_line)
                return Token("ID", lexeme, start_line)

            # NUM
            if _is_digit(ch):
                lexeme = self.advance(1)
                while _is_digit(self.peek(1)):
                    lexeme += self.advance(1)

                nxt = self.peek(1)

                # Example: 12abc => drop the whole token
                if nxt and (_is_letter(nxt) or nxt == "_"):
                    while _is_alnum_or_underscore(self.peek(1)):
                        self.advance(1)
                    continue

                # Example: 012 => ignore it (keeps behavior identical to previous version)
                if len(lexeme) > 1 and lexeme[0] == "0":
                    continue

                # If garbage is stuck to a number, skip it up to a boundary
                if nxt and (nxt not in WHITESPACE) and (nxt not in BOUNDARY_SYMBOLS) and (not _is_alnum_or_underscore(nxt)):
                    while True:
                        t = self.peek(1)
                        if (not t) or (t in WHITESPACE) or (t in BOUNDARY_SYMBOLS):
                            break
                        self.advance(1)
                    continue

                return Token("NUM", lexeme, start_line)

            # comments or '/'
            if ch == "/":
                two = self.peek(2)

                if two == "//":
                    self.advance(2)
                    while self.peek(1) not in ["\n", "\f", ""]:
                        self.advance(1)
                    continue

                if two == "/*":
                    self.advance(2)
                    while True:
                        if not self.peek(1):
                            return Token("EOF", "$", self.line)
                        if self.peek(2) == "*/":
                            self.advance(2)
                            break
                        self.advance(1)
                    continue

                self.advance(1)
                return Token("SYMBOL", "/", start_line)

            # '=' or '=='
            if ch == "=":
                if self.peek(2) == "==":
                    self.advance(2)
                    return Token("SYMBOL", "==", start_line)
                self.advance(1)
                return Token("SYMBOL", "=", start_line)

            # '*' (and ignore stray '*/')
            if ch == "*":
                self.advance(1)
                if self.peek(1) == "/":
                    self.advance(1)
                    continue
                return Token("SYMBOL", "*", start_line)

            # Other one-char symbols
            if ch in self.SINGLE_SYMBOLS:
                self.advance(1)
                return Token("SYMBOL", ch, start_line)

            # Anything else: discard up to the next boundary
            self.advance(1)
            while True:
                t = self.peek(1)
                if (not t) or (t in WHITESPACE) or (t in BOUNDARY_SYMBOLS):
                    break
                self.advance(1)
            continue
