"""Triangulation de Delaunay par algo de Bowyer-Watson."""

from typing import NamedTuple

from triangulator.binary_codec import Point, Triangles


class Circle(NamedTuple):
    """Cercle (centre + rayon)."""

    cx: float
    cy: float
    radius: float


class Edge(NamedTuple):
    """Arête entre deux indices de sommets, normalisée (p1 < p2)."""

    p1: int
    p2: int


def _make_edge(i: int, j: int) -> Edge:
    """Crée une arête avec indices triés pour la comparaison."""
    raise NotImplementedError


def _circumcircle(p1: Point, p2: Point, p3: Point) -> Circle | None:
    """Cercle circonscrit aux 3 points, None si colinéaires."""
    raise NotImplementedError


def _point_in_circumcircle(point: Point, circle: Circle) -> bool:
    """True si le point est strictement à l'intérieur du cercle."""
    raise NotImplementedError


def triangulate(points: list[Point] | list[tuple[float, float]]) -> Triangles:
    """Triangulation de Delaunay (Bowyer-Watson)."""
    raise NotImplementedError


def validate_triangulation(triangulation: Triangles) -> bool:
    """Vérifie la propriété de Delaunay : aucun sommet dans un cercle circonscrit."""
    raise NotImplementedError
