# -*- coding: utf-8 -*-
"""Entry point: read input.txt, write parse_tree.txt and syntax_errors.txt."""

from __future__ import annotations

import os

from scanner import Scanner
from parser import Parser
from parse_tree import render_tree


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
