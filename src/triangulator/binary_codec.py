"""Codec binaire pour PointSet et Triangles.

Format PointSet :
    4 bytes (uint32 LE) : nombre de points N
    N * 8 bytes : (X float32 LE, Y float32 LE)

Format Triangles :
    PointSet des sommets, puis
    4 bytes (uint32 LE) : nombre de triangles T
    T * 12 bytes : (i, j, k) en uint32 LE
"""

import struct
from typing import NamedTuple

from triangulator.exceptions import DecodingError, EncodingError

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
    try:
        result = struct.pack(ULONG_FORMAT, len(points))
        for point in points:
            if isinstance(point, Point):
                x, y = point.x, point.y
            else:
                x, y = point[0], point[1]
            result += struct.pack(FLOAT_FORMAT, x)
            result += struct.pack(FLOAT_FORMAT, y)
        return result
    except (struct.error, TypeError, IndexError) as e:
        raise EncodingError(f"Failed to encode PointSet: {e}") from e


def decode_point_set(data: bytes) -> list[Point]:
    """Décode des bytes PointSet en liste de Point.

    Lève DecodingError si les données sont trop courtes ou corrompues.
    """
    if len(data) < ULONG_SIZE:
        raise DecodingError("Data too short: cannot read point count")

    try:
        (num_points,) = struct.unpack(ULONG_FORMAT, data[:ULONG_SIZE])

        expected_size = ULONG_SIZE + num_points * POINT_SIZE
        if len(data) < expected_size:
            raise DecodingError(
                f"Data too short: expected {expected_size} bytes, got {len(data)}"
            )

        points = []
        offset = ULONG_SIZE
        for _ in range(num_points):
            (x,) = struct.unpack(FLOAT_FORMAT, data[offset : offset + FLOAT_SIZE])
            offset += FLOAT_SIZE
            (y,) = struct.unpack(FLOAT_FORMAT, data[offset : offset + FLOAT_SIZE])
            offset += FLOAT_SIZE
            points.append(Point(x, y))

        return points
    except struct.error as e:
        raise DecodingError(f"Failed to decode PointSet: {e}") from e


def encode_triangles(triangulation: Triangles) -> bytes:
    """Encode une triangulation au format Triangles binaire."""
    try:
        result = encode_point_set(triangulation.vertices)
        result += struct.pack(ULONG_FORMAT, len(triangulation.triangles))
        for triangle in triangulation.triangles:
            result += struct.pack(ULONG_FORMAT, triangle.i)
            result += struct.pack(ULONG_FORMAT, triangle.j)
            result += struct.pack(ULONG_FORMAT, triangle.k)
        return result
    except (struct.error, TypeError, AttributeError) as e:
        raise EncodingError(f"Failed to encode Triangles: {e}") from e


def decode_triangles(data: bytes) -> Triangles:
    """Décode des bytes Triangles en structure Triangles.

    Lève DecodingError si les données sont trop courtes ou corrompues.
    """
    if len(data) < ULONG_SIZE:
        raise DecodingError("Data too short: cannot read vertex count")

    try:
        (num_vertices,) = struct.unpack(ULONG_FORMAT, data[:ULONG_SIZE])
        vertices_size = ULONG_SIZE + num_vertices * POINT_SIZE

        if len(data) < vertices_size + ULONG_SIZE:
            raise DecodingError("Data too short: cannot read triangle count")

        vertices = decode_point_set(data[:vertices_size])

        offset = vertices_size
        (num_triangles,) = struct.unpack(
            ULONG_FORMAT, data[offset : offset + ULONG_SIZE]
        )
        offset += ULONG_SIZE

        expected_size = offset + num_triangles * TRIANGLE_SIZE
        if len(data) < expected_size:
            raise DecodingError(
                f"Data too short for triangles: expected {expected_size}, got {len(data)}"
            )

        triangles = []
        for _ in range(num_triangles):
            (i,) = struct.unpack(ULONG_FORMAT, data[offset : offset + ULONG_SIZE])
            offset += ULONG_SIZE
            (j,) = struct.unpack(ULONG_FORMAT, data[offset : offset + ULONG_SIZE])
            offset += ULONG_SIZE
            (k,) = struct.unpack(ULONG_FORMAT, data[offset : offset + ULONG_SIZE])
            offset += ULONG_SIZE
            triangles.append(Triangle(i, j, k))

        return Triangles(vertices=vertices, triangles=triangles)
    except struct.error as e:
        raise DecodingError(f"Failed to decode Triangles: {e}") from e
