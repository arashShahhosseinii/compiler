# amirhosein shayan <402170981> 
# arash shahhoseini <402170979>
"""
C-minus: Scanner + Predictive Recursive Descent Parser
input.txt  ->  parse_tree.txt + syntax_errors.txt
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
import os


# -----------------------------
# Scanner
# -----------------------------

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


# -----------------------------
# Parse tree + rendering
# -----------------------------

@dataclass
class PTNode:
    name: str
    children: List["PTNode"] = field(default_factory=list)

    def add(self, child: "PTNode") -> None:
        self.children.append(child)


def render_tree(root: PTNode) -> str:
    out: List[str] = []

    def rec(node: PTNode, prefix: str, is_last: bool, is_root: bool) -> None:
        if is_root:
            out.append(node.name)
            child_prefix = ""
        else:
            out.append(prefix + ("└── " if is_last else "├── ") + node.name)
            child_prefix = prefix + ("    " if is_last else "│   ")

        idx = 0
        total = len(node.children)
        while idx < total:
            rec(node.children[idx], child_prefix, idx == total - 1, False)
            idx += 1

    rec(root, "", True, True)
    return "\n".join(out)


# -----------------------------
# Grammar (predictive) + FIRST/FOLLOW + parse table
# -----------------------------

EPS = "EPSILON"

GRAMMAR: Dict[str, List[List[str]]] = {
    "Program": [["Declaration-list"]],
    "Declaration-list": [["Declaration", "Declaration-list"], [EPS]],
    "Declaration": [["Declaration-initial", "Declaration-prime"]],
    "Declaration-initial": [["Type-specifier", "ID"]],
    "Declaration-prime": [["Fun-declaration-prime"], ["Var-declaration-prime"]],
    "Var-declaration-prime": [["[", "NUM", "]", ";"], [";"]],
    "Fun-declaration-prime": [["(", "Params", ")", "Compound-stmt"]],
    "Type-specifier": [["int"], ["void"]],
    "Params": [["int", "ID", "Param-prime", "Param-list"], ["void"]],
    "Param-list": [[",", "Param", "Param-list"], [EPS]],
    "Param": [["Declaration-initial", "Param-prime"]],
    "Param-prime": [["[", "]"], [EPS]],
    "Compound-stmt": [["{", "Declaration-list", "Statement-list", "}"]],
    "Statement-list": [["Statement", "Statement-list"], [EPS]],
    "Statement": [["Expression-stmt"], ["Compound-stmt"], ["Selection-stmt"], ["Iteration-stmt"], ["Return-stmt"]],
    "Expression-stmt": [["Expression", ";"], ["break", ";"], [";"]],
    "Selection-stmt": [["if", "(", "Expression", ")", "Statement", "Else-stmt"]],
    "Else-stmt": [["else", "Statement"], [EPS]],
    "Iteration-stmt": [["for", "(", "Expression", ";", "Expression", ";", "Expression", ")", "Compound-stmt"]],
    "Return-stmt": [["return", "Return-stmt-prime"]],
    "Return-stmt-prime": [["Expression", ";"], [";"]],
    "Expression": [["Simple-expression-zegond"], ["ID", "B"]],
    "B": [["=", "Expression"], ["[", "Expression", "]", "H"], ["Simple-expression-prime"]],
    "H": [["=", "Expression"], ["G", "D", "C"]],
    "Simple-expression-zegond": [["Additive-expression-zegond", "C"]],
    "Simple-expression-prime": [["Additive-expression-prime", "C"]],
    "C": [["Relop", "Additive-expression"], [EPS]],
    "Relop": [["=="], ["<"]],
    "Additive-expression": [["Term", "D"]],
    "Additive-expression-prime": [["Term-prime", "D"]],
    "Additive-expression-zegond": [["Term-zegond", "D"]],
    "D": [["Addop", "Term", "D"], [EPS]],
    "Addop": [["+"], ["-"]],
    "Term": [["Signed-factor", "G"]],
    "Term-prime": [["Factor-prime", "G"]],
    "Term-zegond": [["Signed-factor-zegond", "G"]],
    "G": [["*", "Signed-factor", "G"], ["/", "Signed-factor", "G"], [EPS]],
    "Signed-factor": [["+", "Factor"], ["-", "Factor"], ["Factor"]],
    "Signed-factor-zegond": [["+", "Factor"], ["-", "Factor"], ["Factor-zegond"]],
    "Factor": [["(", "Expression", ")"], ["ID", "Var-call-prime"], ["NUM"]],
    "Var-call-prime": [["(", "Args", ")"], ["Var-prime"]],
    "Var-prime": [["[", "Expression", "]"], [EPS]],
    "Factor-prime": [["(", "Args", ")"], [EPS]],
    "Factor-zegond": [["(", "Expression", ")"], ["NUM"]],
    "Args": [["Arg-list"], [EPS]],
    "Arg-list": [["Expression", "Arg-list-prime"]],
    "Arg-list-prime": [[",", "Expression", "Arg-list-prime"], [EPS]],
}

NONTERMINALS: Set[str] = set(GRAMMAR.keys())


def compute_first_follow(grammar: Dict[str, List[List[str]]]) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    nts = set(grammar.keys())
    first: Dict[str, Set[str]] = {A: set() for A in nts}

    # FIRST
    changed = True
    while changed:
        changed = False

        items = list(grammar.items())
        i_items = 0
        while i_items < len(items):
            A, prods = items[i_items]

            i_prod = 0
            while i_prod < len(prods):
                prod = prods[i_prod]

                if prod == [EPS]:
                    if EPS not in first[A]:
                        first[A].add(EPS)
                        changed = True
                    i_prod += 1
                    continue

                nullable_prefix = True
                i_sym = 0
                while i_sym < len(prod):
                    sym = prod[i_sym]

                    if sym == EPS:
                        if EPS not in first[A]:
                            first[A].add(EPS)
                            changed = True
                        nullable_prefix = False
                        break

                    if sym in nts:
                        add = first[sym] - {EPS}
                        if not add.issubset(first[A]):
                            first[A] |= add
                            changed = True
                        if EPS in first[sym]:
                            i_sym += 1
                            continue
                        nullable_prefix = False
                        break
                    else:
                        if sym not in first[A]:
                            first[A].add(sym)
                            changed = True
                        nullable_prefix = False
                        break

                if nullable_prefix:
                    if EPS not in first[A]:
                        first[A].add(EPS)
                        changed = True

                i_prod += 1

            i_items += 1

    follow: Dict[str, Set[str]] = {A: set() for A in nts}
    follow["Program"].add("$")

    def first_of_seq(seq: List[str]) -> Set[str]:
        out: Set[str] = set()
        if not seq or seq == [EPS]:
            out.add(EPS)
            return out

        i = 0
        while i < len(seq):
            sym = seq[i]

            if sym == EPS:
                out.add(EPS)
                return out

            if sym in nts:
                out |= (first[sym] - {EPS})
                if EPS in first[sym]:
                    i += 1
                    continue
                return out

            out.add(sym)
            return out

        out.add(EPS)
        return out

    # FOLLOW
    changed = True
    while changed:
        changed = False

        items = list(grammar.items())
        i_items = 0
        while i_items < len(items):
            A, prods = items[i_items]

            i_prod = 0
            while i_prod < len(prods):
                prod = prods[i_prod]

                i = 0
                while i < len(prod):
                    B = prod[i]
                    if B not in nts:
                        i += 1
                        continue

                    beta = prod[i + 1:]
                    fb = first_of_seq(beta)

                    add1 = fb - {EPS}
                    if not add1.issubset(follow[B]):
                        follow[B] |= add1
                        changed = True

                    if (EPS in fb) or (not beta):
                        if not follow[A].issubset(follow[B]):
                            follow[B] |= follow[A]
                            changed = True

                    i += 1

                i_prod += 1

            i_items += 1

    return first, follow


FIRST, FOLLOW = compute_first_follow(GRAMMAR)


def build_parse_table(
    grammar: Dict[str, List[List[str]]],
    first: Dict[str, Set[str]],
    follow: Dict[str, Set[str]],
) -> Dict[str, Dict[str, List[str]]]:
    nts = set(grammar.keys())

    def first_of_seq(seq: List[str]) -> Set[str]:
        out: Set[str] = set()
        if not seq or seq == [EPS]:
            out.add(EPS)
            return out

        i = 0
        while i < len(seq):
            sym = seq[i]

            if sym == EPS:
                out.add(EPS)
                return out

            if sym in nts:
                out |= (first[sym] - {EPS})
                if EPS in first[sym]:
                    i += 1
                    continue
                return out

            out.add(sym)
            return out

        out.add(EPS)
        return out

    table: Dict[str, Dict[str, List[str]]] = {A: {} for A in nts}

    # IMPORTANT: epsilon productions must NOT overwrite existing entries (e.g. Else-stmt on 'else')
    items = list(grammar.items())
    i_items = 0
    while i_items < len(items):
        A, prods = items[i_items]

        i_prod = 0
        while i_prod < len(prods):
            prod = prods[i_prod]
            fs = first_of_seq(prod)

            terms = list(fs - {EPS})
            j = 0
            while j < len(terms):
                t = terms[j]
                if t not in table[A]:
                    table[A][t] = prod
                j += 1

            if EPS in fs:
                flw = list(follow[A])
                k = 0
                while k < len(flw):
                    b = flw[k]
                    if b not in table[A]:
                        table[A][b] = prod
                    k += 1

            i_prod += 1

        i_items += 1

    return table


PARSE_TABLE = build_parse_table(GRAMMAR, FIRST, FOLLOW)


# -----------------------------
# Parser
# -----------------------------

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


# -----------------------------
# Main
# -----------------------------

def main() -> None:
    try:
        with open("input.txt", "r", encoding="utf-8") as f:
            src = f.read()
    except FileNotFoundError:
        with open("parse_tree.txt", "w", encoding="utf-8") as f:
            f.write("Program\n")
        with open("syntax_errors.txt", "w", encoding="utf-8") as f:
            f.write("No syntax errors found.")
        return

    scanner = Scanner(src)
    parser = Parser(scanner)
    tree = parser.parse()

    files = ["parse_tree.txt", "syntax_errors.txt"]
    idx = 0
    while idx < len(files):
        name = files[idx]
        try:
            if os.path.exists(name):
                os.remove(name)
        except Exception:
            pass
        idx += 1

    with open("parse_tree.txt", "w", encoding="utf-8") as f:
        f.write(render_tree(tree))

    with open("syntax_errors.txt", "w", encoding="utf-8") as f:
        if not parser.errors:
            f.write("No syntax errors found.")
        else:
            f.write("\n".join(parser.errors))


if __name__ == "__main__":
    main()
