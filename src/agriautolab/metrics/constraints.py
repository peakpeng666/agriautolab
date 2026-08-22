"""硬可行性门槛与可互相权衡的指标分开求值：门槛不参与折中。"""

from __future__ import annotations

from shapely.geometry.base import BaseGeometry

from agriautolab.contracts.artifacts import PathArtifact
from agriautolab.geometry.footprint import sweep_piece
from agriautolab.geometry.robust import robust_union
from agriautolab.geometry.validate import line_from_spec


def _body_sweep(path: PathArtifact, body_width_m: float, scale_hint: float) -> BaseGeometry:
    pieces = tuple(sweep_piece(line_from_spec(segment.line), body_width_m) for segment in path.segments)
    return robust_union(pieces, scale_hint=scale_hint)


def collision_area(path: PathArtifact, obstacles: BaseGeometry, *, body_width_m: float, scale_hint: float) -> float:
    return _body_sweep(path, body_width_m, scale_hint).intersection(obstacles).area


def outside_area(path: PathArtifact, allowed: BaseGeometry, *, body_width_m: float, scale_hint: float) -> float:
    return _body_sweep(path, body_width_m, scale_hint).difference(allowed).area


def max_abs_declared_curvature(path: PathArtifact) -> float:
    if not path.segments:
        return 0.0
    return max(abs(segment.signed_curvature_m_inv) for segment in path.segments)
