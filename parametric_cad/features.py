"""Параметрические элементы построения (аналог операций в CAD)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import trimesh
from shapely.geometry import Polygon

from parametric_cad.parameters import ParameterStore


@dataclass
class BuildContext:
    params: ParameterStore


class Feature(ABC):
    id: str

    @abstractmethod
    def build(self, ctx: BuildContext) -> trimesh.Trimesh:
        ...


class BoxFeature(Feature):
    def __init__(
        self,
        fid: str,
        cx: str,
        cy: str,
        cz: str,
        dx: str,
        dy: str,
        dz: str,
    ) -> None:
        self.id = fid
        self.cx, self.cy, self.cz = cx, cy, cz
        self.dx, self.dy, self.dz = dx, dy, dz

    def build(self, ctx: BuildContext) -> trimesh.Trimesh:
        p = ctx.params
        w, h, d = p.get(self.dx), p.get(self.dy), p.get(self.dz)
        box = trimesh.creation.box(extents=[w, h, d])
        box.apply_translation(
            [p.get(self.cx), p.get(self.cy), p.get(self.cz)]
        )
        return box


class CylinderFeature(Feature):
    def __init__(
        self,
        fid: str,
        cx: str,
        cy: str,
        cz: str,
        radius: str,
        height: str,
        axis: str = "z",
    ) -> None:
        self.id = fid
        self.cx, self.cy, self.cz = cx, cy, cz
        self.radius, self.height = radius, height
        self.axis = axis.lower()

    def build(self, ctx: BuildContext) -> trimesh.Trimesh:
        p = ctx.params
        cyl = trimesh.creation.cylinder(
            radius=p.get(self.radius),
            height=p.get(self.height),
            sections=48,
        )
        if self.axis == "x":
            R = trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0])
            cyl.apply_transform(R)
        elif self.axis == "y":
            R = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
            cyl.apply_transform(R)
        cyl.apply_translation(
            [p.get(self.cx), p.get(self.cy), p.get(self.cz)]
        )
        return cyl


class ExtrudeFeature(Feature):
    """Экструзия многоугольника в плоскости XY вдоль +Z."""

    def __init__(
        self,
        fid: str,
        point_param_pairs: List[Tuple[str, str]],
        height: str,
        offset_x: Optional[str] = None,
        offset_y: Optional[str] = None,
        offset_z: Optional[str] = None,
    ) -> None:
        self.id = fid
        self.point_param_pairs = point_param_pairs
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.offset_z = offset_z

    def build(self, ctx: BuildContext) -> trimesh.Trimesh:
        p = ctx.params
        pts = [(p.get(px), p.get(py)) for px, py in self.point_param_pairs]
        poly = Polygon(pts)
        if not poly.is_valid:
            poly = poly.buffer(0)
        h = p.get(self.height)
        mesh = trimesh.creation.extrude_polygon(poly, height=h)
        if (
            self.offset_x is not None
            and self.offset_y is not None
            and self.offset_z is not None
        ):
            mesh.apply_translation(
                [p.get(self.offset_x), p.get(self.offset_y), p.get(self.offset_z)]
            )
        return mesh


def combine_union(meshes: List[trimesh.Trimesh]) -> trimesh.Trimesh:
    if not meshes:
        raise ValueError("нет геометрии")
    if len(meshes) == 1:
        return meshes[0]
    return trimesh.util.concatenate(meshes)
