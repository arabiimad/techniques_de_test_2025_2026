"""Codec binaire pour PointSet et Triangles.

Format PointSet :
    4 bytes (uint32 LE) : nombre de points N
    N * 8 bytes : (X float32 LE, Y float32 LE)

Format Triangles :
    PointSet des sommets, puis
    4 bytes (uint32 LE) : nombre de triangles T
    T * 12 bytes : (i, j, k) en uint32 LE
"""

from typing import NamedTuple

ULONG_FORMAT = "<I"
FLOAT_FORMAT = "<f"
ULONG_SIZE = 4
FLOAT_SIZE = 4
POINT_SIZE = 2 * FLOAT_SIZE
TRIANGLE_SIZE = 3 * ULONG_SIZE


class Point(NamedTuple):
    """Point 2D (x, y)."""

    x: float
    y: float


class Triangle(NamedTuple):
    """Triangle référencé par les indices de ses 3 sommets."""

    i: int
    j: int
    k: int


class Triangles(NamedTuple):
    """Triangulation : liste de sommets + liste de triangles (indices)."""

    vertices: list[Point]
    triangles: list[Triangle]


def encode_point_set(points: list[Point] | list[tuple[float, float]]) -> bytes:
    """Encode une liste de points (Point ou tuples) au format PointSet binaire."""
    raise NotImplementedError


def decode_point_set(data: bytes) -> list[Point]:
    """Décode des bytes PointSet en liste de Point."""
    raise NotImplementedError


def encode_triangles(triangulation: Triangles) -> bytes:
    """Encode une triangulation au format Triangles binaire."""
    raise NotImplementedError


def decode_triangles(data: bytes) -> Triangles:
    """Décode des bytes Triangles en structure Triangles."""
    raise NotImplementedError
