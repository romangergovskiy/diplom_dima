#!/usr/bin/env python3
"""Веб-интерфейс для параметрического 3D-модуля."""

from __future__ import annotations

import base64
from dataclasses import asdict
from pathlib import Path
from typing import Dict

from flask import Flask, jsonify, render_template, request

from parametric_cad.document import Document
from parametric_cad.engineering import MassProps, mass_properties
from parametric_cad.scripting import execute_script

BASE_DIR = Path(__file__).parent
EXAMPLES_DIR = BASE_DIR / "examples"

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "web" / "templates"),
    static_folder=str(BASE_DIR / "web" / "static"),
)


def list_examples() -> Dict[str, str]:
    examples: Dict[str, str] = {}
    if not EXAMPLES_DIR.exists():
        return examples
    for path in sorted(EXAMPLES_DIR.glob("*.txt")):
        examples[path.name] = path.read_text(encoding="utf-8")
    return examples


def _mass_props_to_dict(mp: MassProps) -> Dict[str, object]:
    data = asdict(mp)
    data["center_of_mass"] = [float(v) for v in mp.center_of_mass]
    return data


def build_model(script: str, density: float) -> Dict[str, object]:
    doc = Document()
    execute_script(doc, script)
    mesh = doc.rebuild_mesh()
    mp = mass_properties(mesh, density)
    stl_bytes = mesh.export(file_type="stl")
    stl_b64 = base64.b64encode(stl_bytes).decode("ascii")
    params = {name: float(doc.params.get(name)) for name in sorted(doc.params.names())}
    mesh_data = {
        "vertices": [[float(c) for c in v] for v in mesh.vertices.tolist()],
        "faces": [[int(i) for i in f] for f in mesh.faces.tolist()],
    }
    return {
        "params": params,
        "mass_props": _mass_props_to_dict(mp),
        "stl_base64": stl_b64,
        "mesh_data": mesh_data,
    }


@app.get("/")
def index() -> str:
    examples = list_examples()
    default_script = examples.get("simple_box.txt", "")
    return render_template("index.html", examples=examples, default_script=default_script)


@app.post("/api/build")
def api_build():
    payload = request.get_json(silent=True) or {}
    script = str(payload.get("script", ""))
    density = float(payload.get("density", 7850.0))

    if not script.strip():
        return jsonify({"ok": False, "error": "Сценарий пуст."}), 400

    try:
        result = build_model(script, density)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400

    return jsonify({"ok": True, **result})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
