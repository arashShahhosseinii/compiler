# -*- coding: utf-8 -*-
"""Parse tree nodes + anytree-like renderer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


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
