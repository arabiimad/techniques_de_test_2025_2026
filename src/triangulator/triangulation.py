"""Triangulation de Delaunay par algo de Bowyer-Watson."""

import math
from typing import NamedTuple

from triangulator.binary_codec import Point, Triangle, Triangles
from triangulator.exceptions import TriangulationError


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
    return Edge(min(i, j), max(i, j))


def _circumcircle(p1: Point, p2: Point, p3: Point) -> Circle | None:
    """Cercle circonscrit aux 3 points, None si colinéaires."""
    ax, ay = p1.x, p1.y
    bx, by = p2.x, p2.y
    cx, cy = p3.x, p3.y

    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))

    if abs(d) < 1e-10:
        return None

    ax2_ay2 = ax * ax + ay * ay
    bx2_by2 = bx * bx + by * by
    cx2_cy2 = cx * cx + cy * cy

    ux = (ax2_ay2 * (by - cy) + bx2_by2 * (cy - ay) + cx2_cy2 * (ay - by)) / d
    uy = (ax2_ay2 * (cx - bx) + bx2_by2 * (ax - cx) + cx2_cy2 * (bx - ax)) / d

    radius = math.sqrt((ax - ux) ** 2 + (ay - uy) ** 2)

    return Circle(ux, uy, radius)


def _point_in_circumcircle(point: Point, circle: Circle) -> bool:
    """True si le point est strictement à l'intérieur du cercle."""
    dx = point.x - circle.cx
    dy = point.y - circle.cy
    dist = math.sqrt(dx * dx + dy * dy)
    return dist < circle.radius - 1e-10


def _create_super_triangle(points: list[Point]) -> tuple[Point, Point, Point]:
    """Super-triangle qui englobe tous les points (large pour éviter les soucis de bord)."""
    if not points:
        return (Point(-1, -1), Point(3, -1), Point(1, 3))

    min_x = min(p.x for p in points)
    max_x = max(p.x for p in points)
    min_y = min(p.y for p in points)
    max_y = max(p.y for p in points)

    dx = max_x - min_x
    dy = max_y - min_y
    delta_max = max(dx, dy, 1.0)
    mid_x = (min_x + max_x) / 2
    mid_y = (min_y + max_y) / 2

    p1 = Point(mid_x - 20 * delta_max, mid_y - delta_max)
    p2 = Point(mid_x, mid_y + 20 * delta_max)
    p3 = Point(mid_x + 20 * delta_max, mid_y - delta_max)

    return (p1, p2, p3)


def triangulate(points: list[Point] | list[tuple[float, float]]) -> Triangles:
    """Triangulation de Delaunay (Bowyer-Watson).

    Accepte des Point ou des tuples (x, y). Pour <3 points, renvoie 0 triangles.
    Lève TriangulationError en cas d'échec.
    """
    try:
        point_list = [
            Point(p[0], p[1]) if not isinstance(p, Point) else p for p in points
        ]

        if len(point_list) < 3:
            return Triangles(vertices=list(point_list), triangles=[])

        # dédoublonnage en gardant l'ordre
        seen: set[tuple[float, float]] = set()
        unique_points: list[Point] = []
        for p in point_list:
            key = (p.x, p.y)
            if key not in seen:
                seen.add(key)
                unique_points.append(p)

        if len(unique_points) < 3:
            return Triangles(vertices=list(unique_points), triangles=[])

        return _bowyer_watson(unique_points)
    except Exception as e:
        if isinstance(e, TriangulationError):
            raise
        raise TriangulationError(f"Triangulation failed: {e}") from e


def _bowyer_watson(points: list[Point]) -> Triangles:
    """Coeur de Bowyer-Watson sur des points déjà uniques (>=3)."""
    st = _create_super_triangle(points)

    vertices: list[Point] = [st[0], st[1], st[2]] + list(points)
    triangles: list[tuple[int, int, int]] = [(0, 1, 2)]

    for point_idx in range(3, len(vertices)):
        point = vertices[point_idx]

        bad_triangles: list[tuple[int, int, int]] = []

        for tri in triangles:
            p1, p2, p3 = vertices[tri[0]], vertices[tri[1]], vertices[tri[2]]
            circle = _circumcircle(p1, p2, p3)
            if circle is not None and _point_in_circumcircle(point, circle):
                bad_triangles.append(tri)

        # arêtes du polygone = celles qui apparaissent qu'une fois
        edge_count: dict[Edge, int] = {}
        for tri in bad_triangles:
            edges = [
                _make_edge(tri[0], tri[1]),
                _make_edge(tri[1], tri[2]),
                _make_edge(tri[2], tri[0]),
            ]
            for edge in edges:
                edge_count[edge] = edge_count.get(edge, 0) + 1

        polygon_edges = [edge for edge, count in edge_count.items() if count == 1]

        triangles = [t for t in triangles if t not in bad_triangles]

        for edge in polygon_edges:
            new_tri = (edge.p1, edge.p2, point_idx)
            triangles.append(new_tri)

    # on vire tout triangle qui touche le super-triangle (indices 0/1/2)
    final_triangles: list[tuple[int, int, int]] = []
    for tri in triangles:
        if tri[0] >= 3 and tri[1] >= 3 and tri[2] >= 3:
            final_triangles.append(tri)

    result_vertices = vertices[3:]
    result_triangles = [
        Triangle(tri[0] - 3, tri[1] - 3, tri[2] - 3) for tri in final_triangles
    ]

    return Triangles(vertices=result_vertices, triangles=result_triangles)


def validate_triangulation(triangulation: Triangles) -> bool:
    """Vérifie la propriété de Delaunay : aucun sommet dans un cercle circonscrit."""
    vertices = triangulation.vertices
    triangles = triangulation.triangles

    for tri in triangles:
        p1 = vertices[tri.i]
        p2 = vertices[tri.j]
        p3 = vertices[tri.k]

        circle = _circumcircle(p1, p2, p3)
        if circle is None:
            continue

        for idx, point in enumerate(vertices):
            if idx in (tri.i, tri.j, tri.k):
                continue
            if _point_in_circumcircle(point, circle):
                return False

    return True
