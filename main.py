#!/usr/bin/env python3
"""Запуск прототипа: загрузка сценария, экспорт STL, вывод инженерных величин."""

from __future__ import annotations

import argparse
import pathlib
import sys

from parametric_cad.document import Document
from parametric_cad.engineering import mass_properties
from parametric_cad.scripting import execute_script


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Параметрический 3D-модуль (прототип для ВКР)"
    )
    parser.add_argument("script", type=pathlib.Path, help="файл сценария (.txt)")
    parser.add_argument(
        "-o",
        "--output",
        type=pathlib.Path,
        default=None,
        help="путь для экспорта STL",
    )
    parser.add_argument(
        "--density",
        type=float,
        default=7850.0,
        help="плотность стали для оценки массы, кг/м³ (по умолчанию 7850)",
    )
    args = parser.parse_args()

    text = args.script.read_text(encoding="utf-8")
    doc = Document()
    execute_script(doc, text)
    mesh = doc.rebuild_mesh()

    print("Параметры:")
    for n in sorted(doc.params.names()):
        print(f"  {n} = {doc.params.get(n):.6g}")

    mp = mass_properties(mesh, args.density)
    print(f"Объём (при замкнутой сетке): {mp.volume:.6e} м³")
    print(
        f"Центр масс: ({mp.center_of_mass[0]:.6g}, "
        f"{mp.center_of_mass[1]:.6g}, {mp.center_of_mass[2]:.6g})"
    )
    print(f"Масса (ρ={args.density}): {mp.mass:.6g} кг")

    out = args.output
    if out:
        mesh.export(str(out))
        print(f"Экспорт STL: {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
