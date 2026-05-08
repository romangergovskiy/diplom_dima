"""Разбор и выполнение сценария управления моделью."""

from __future__ import annotations

import re
from typing import List, Tuple

from parametric_cad.document import Document
from parametric_cad.features import BoxFeature, CylinderFeature, ExtrudeFeature


def _split_line(line: str) -> List[str]:
    line = line.split("#", 1)[0].strip()
    if not line:
        return []
    return re.findall(r'"[^"]*"|\S+', line)


def execute_script(doc: Document, source: str) -> None:
    """
    Команды (одна на строку):
      param <имя> <число> [expr остаток_строки_выражение]
      box <id> <cx> <cy> <cz> <dx> <dy> <dz>   — имена параметров для размеров и центра
      cylinder <id> <cx> <cy> <cz> <R> <H> [axis x|y|z]
      extrude <id> <h_высота> <x1> <y1> <x2> <y2> ...  — пары имён параметров вершин
    """
    for raw in source.splitlines():
        stripped = raw.split("#", 1)[0].strip()
        if not stripped:
            continue
        parts = _split_line(stripped)
        cmd = parts[0].lower()
        if cmd == "param":
            m = re.search(r"(?i)\s+expr\s+", stripped)
            if m:
                head = stripped[: m.start()].strip()
                head_parts = _split_line(head)
                if len(head_parts) < 3:
                    raise ValueError(f"param: недостаточно аргументов: {raw}")
                name = head_parts[1]
                value = float(head_parts[2])
                expr = stripped[m.end() :].strip()
                if expr.startswith('"') and expr.endswith('"'):
                    expr = expr[1:-1]
                doc.params.add(name, value, expr)
            else:
                if len(parts) < 3:
                    raise ValueError(f"param: недостаточно аргументов: {raw}")
                name = parts[1]
                value = float(parts[2])
                doc.params.add(name, value, None)
        elif cmd == "box":
            if len(parts) < 8:
                raise ValueError(f"box: ожидается box id cx cy cz dx dy dz: {raw}")
            _, fid, cx, cy, cz, dx, dy, dz = parts[:8]
            doc.add_feature(BoxFeature(fid, cx, cy, cz, dx, dy, dz))
        elif cmd == "cylinder":
            if len(parts) < 7:
                raise ValueError(
                    f"cylinder: ожидается cylinder id cx cy cz R H [ось]: {raw}"
                )
            _, fid = parts[0], parts[1]
            cx, cy, cz, r, h = parts[2:7]
            axis = "z"
            if len(parts) >= 9 and parts[7].lower() == "axis":
                axis = parts[8].lower()
            elif len(parts) >= 8 and parts[7].lower() in ("x", "y", "z"):
                axis = parts[7].lower()
            doc.add_feature(
                CylinderFeature(fid, cx, cy, cz, r, h, axis=axis)
            )
        elif cmd == "extrude":
            if len(parts) < 6 or (len(parts) - 3) % 2 != 0:
                raise ValueError(f"extrude: id height x1 y1 x2 y2 ...: {raw}")
            fid = parts[1]
            height = parts[2]
            pairs: List[Tuple[str, str]] = []
            rest = parts[3:]
            for i in range(0, len(rest), 2):
                pairs.append((rest[i], rest[i + 1]))
            doc.add_feature(ExtrudeFeature(fid, pairs, height))
        else:
            raise ValueError(f"неизвестная команда: {cmd}")
