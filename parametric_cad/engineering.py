"""Инженерные расчёты по твердотельной модели."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import trimesh


@dataclass
class MassProps:
    volume: float
    center_of_mass: np.ndarray
    mass: float


def mass_properties(mesh: trimesh.Trimesh, density_kg_m3: float) -> MassProps:
    """Объём (м³), центр масс, масса при заданной плотности (кг/м³)."""
    if not mesh.is_watertight:
        mesh = mesh.copy()
        mesh.fill_holes()
    vol = float(mesh.volume)
    com = np.array(mesh.center_mass, dtype=float)
    mass = vol * density_kg_m3
    return MassProps(volume=vol, center_of_mass=com, mass=mass)
