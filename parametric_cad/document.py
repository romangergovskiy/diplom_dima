"""Документ модели: параметры, дерево элементов, пересборка."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import trimesh

from parametric_cad.features import BuildContext, Feature, combine_union
from parametric_cad.parameters import ParameterStore


@dataclass
class Document:
    params: ParameterStore = field(default_factory=ParameterStore)
    features: List[Feature] = field(default_factory=list)

    def add_feature(self, feature: Feature) -> None:
        self.features.append(feature)

    def rebuild_mesh(self) -> trimesh.Trimesh:
        ctx = BuildContext(self.params)
        meshes = [f.build(ctx) for f in self.features]
        return combine_union(meshes)

    def export_stl(self, path: str) -> None:
        mesh = self.rebuild_mesh()
        mesh.export(path)
