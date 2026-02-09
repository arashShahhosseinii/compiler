# -*- coding: utf-8 -*-
"""Grammar + FIRST/FOLLOW + LL(1) parsing table."""

from __future__ import annotations

from typing import Dict, List, Set, Tuple


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
