"""Tests de l'algo de triangulation."""

import math

import pytest

from triangulator.binary_codec import Point, Triangles
from triangulator.triangulation import (
    _circumcircle,
    _point_in_circumcircle,
    triangulate,
    validate_triangulation,
)


class TestTriangulateBasicCases:
    """Cas basiques."""

    @pytest.mark.unit
    def test_triangulate_three_points(self, triangle_points: list[Point]) -> None:
        """3 points = 1 triangle qui utilise les 3."""
        result = triangulate(triangle_points)

        assert len(result.vertices) == 3
        assert len(result.triangles) == 1

        tri = result.triangles[0]
        indices = {tri.i, tri.j, tri.k}
        assert indices == {0, 1, 2}

    @pytest.mark.unit
    def test_triangulate_four_points_square(self, square_points: list[Point]) -> None:
        """Carré = 2 triangles, indices valides et distincts."""
        result = triangulate(square_points)

        assert len(result.vertices) == 4
        assert len(result.triangles) == 2

        for tri in result.triangles:
            assert 0 <= tri.i < 4
            assert 0 <= tri.j < 4
            assert 0 <= tri.k < 4
            assert len({tri.i, tri.j, tri.k}) == 3

    @pytest.mark.unit
    def test_triangulate_collinear_points(self, collinear_points: list[Point]) -> None:
        """Points alignés : pas de vrai triangle."""
        result = triangulate(collinear_points)
        assert len(result.vertices) == len(collinear_points)
        # le nombre de triangles dépend de l'implem, on vérifie juste que ça plante pas

    @pytest.mark.unit
    def test_triangulate_less_than_three_points_empty(
        self, empty_point_set: list[Point]
    ) -> None:
        """0 point → 0 triangle."""
        result = triangulate(empty_point_set)
        assert len(result.vertices) == 0
        assert len(result.triangles) == 0

    @pytest.mark.unit
    def test_triangulate_less_than_three_points_one(
        self, single_point: list[Point]
    ) -> None:
        """1 point → 0 triangle."""
        result = triangulate(single_point)
        assert len(result.vertices) == 1
        assert len(result.triangles) == 0

    @pytest.mark.unit
    def test_triangulate_less_than_three_points_two(
        self, two_points: list[Point]
    ) -> None:
        """2 points → 0 triangle."""
        result = triangulate(two_points)
        assert len(result.vertices) == 2
        assert len(result.triangles) == 0

    @pytest.mark.unit
    def test_triangulate_duplicate_points(self, duplicate_points: list[Point]) -> None:
        """Doublons : dédoublonnés, pas de plantage, résultat valide."""
        result = triangulate(duplicate_points)
        assert len(result.vertices) <= len(duplicate_points)
        if len(result.triangles) > 0:
            assert validate_triangulation(result)


class TestTriangulateLargeDataset:
    """Cas un peu plus gros."""

    @pytest.mark.unit
    def test_triangulate_large_point_set(self, large_point_set: list[Point]) -> None:
        """100 points : triangles présents, indices dans les bornes."""
        result = triangulate(large_point_set)
        assert len(result.vertices) <= len(large_point_set)
        assert len(result.triangles) > 0

        num_vertices = len(result.vertices)
        for tri in result.triangles:
            assert 0 <= tri.i < num_vertices
            assert 0 <= tri.j < num_vertices
            assert 0 <= tri.k < num_vertices

    @pytest.mark.unit
    def test_triangulate_regular_grid(self) -> None:
        """Grille 5x5 → au moins ~20 triangles."""
        points = [Point(float(x), float(y)) for x in range(5) for y in range(5)]
        result = triangulate(points)
        assert len(result.vertices) == 25
        assert len(result.triangles) >= 20

    @pytest.mark.unit
    def test_triangulate_circular_pattern(self) -> None:
        """Points sur un cercle."""
        n = 12
        points = [
            Point(math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n))
            for i in range(n)
        ]
        result = triangulate(points)
        assert len(result.vertices) == n
        assert len(result.triangles) > 0


class TestDelaunayProperty:
    """Propriété de Delaunay."""

    @pytest.mark.unit
    def test_delaunay_property_simple(self, triangle_points: list[Point]) -> None:
        """Triangle simple."""
        result = triangulate(triangle_points)
        assert validate_triangulation(result)

    @pytest.mark.unit
    def test_delaunay_property_square(self, square_points: list[Point]) -> None:
        """Carré."""
        result = triangulate(square_points)
        assert validate_triangulation(result)

    @pytest.mark.unit
    def test_delaunay_property_random(self) -> None:
        """6 points 'aléatoires' déterministes."""
        points = [
            Point(0.1, 0.2),
            Point(0.8, 0.3),
            Point(0.5, 0.9),
            Point(0.2, 0.6),
            Point(0.9, 0.7),
            Point(0.4, 0.1),
        ]
        result = triangulate(points)
        assert validate_triangulation(result)


class TestCircumcircle:
    """Fonctions auxiliaires de cercle circonscrit."""

    @pytest.mark.unit
    def test_circumcircle_equilateral(self) -> None:
        """Triangle équilatéral centré → cercle centré près de l'origine."""
        h = math.sqrt(3) / 2
        p1 = Point(-0.5, -h / 3)
        p2 = Point(0.5, -h / 3)
        p3 = Point(0.0, 2 * h / 3)

        circle = _circumcircle(p1, p2, p3)

        assert circle is not None
        assert abs(circle.cx) < 0.1
        assert abs(circle.cy) < 0.1

    @pytest.mark.unit
    def test_circumcircle_right_triangle(self) -> None:
        """Triangle rectangle → centre au milieu de l'hypoténuse."""
        p1 = Point(0, 0)
        p2 = Point(2, 0)
        p3 = Point(0, 2)

        circle = _circumcircle(p1, p2, p3)

        assert circle is not None
        assert abs(circle.cx - 1.0) < 1e-6
        assert abs(circle.cy - 1.0) < 1e-6
        assert abs(circle.radius - math.sqrt(2)) < 1e-6

    @pytest.mark.unit
    def test_circumcircle_collinear_returns_none(self) -> None:
        """Points alignés → None."""
        p1 = Point(0, 0)
        p2 = Point(1, 1)
        p3 = Point(2, 2)

        circle = _circumcircle(p1, p2, p3)
        assert circle is None

    @pytest.mark.unit
    def test_point_in_circumcircle_inside(self) -> None:
        """Point au centre du triangle = dedans."""
        p1 = Point(0, 0)
        p2 = Point(2, 0)
        p3 = Point(1, 2)

        circle = _circumcircle(p1, p2, p3)
        assert circle is not None

        inside_point = Point(1.0, 0.5)
        assert _point_in_circumcircle(inside_point, circle)

    @pytest.mark.unit
    def test_point_in_circumcircle_outside(self) -> None:
        """Point loin = dehors."""
        p1 = Point(0, 0)
        p2 = Point(2, 0)
        p3 = Point(1, 2)

        circle = _circumcircle(p1, p2, p3)
        assert circle is not None

        outside_point = Point(10.0, 10.0)
        assert not _point_in_circumcircle(outside_point, circle)


class TestTriangulateFromTuples:
    """Entrées en tuples."""

    @pytest.mark.unit
    def test_triangulate_from_tuples(self) -> None:
        """Tuples (x, y) acceptés."""
        tuples = [(0.0, 0.0), (1.0, 0.0), (0.5, 1.0)]
        result = triangulate(tuples)
        assert len(result.vertices) == 3
        assert len(result.triangles) == 1

    @pytest.mark.unit
    def test_triangulate_mixed_input(self) -> None:
        """Mélange tuple + Point."""
        mixed = [Point(0.0, 0.0), (1.0, 0.0), Point(0.5, 1.0)]
        result = triangulate(mixed)
        assert len(result.vertices) == 3
        assert len(result.triangles) == 1


class TestTriangulationValidation:
    """validate_triangulation."""

    @pytest.mark.unit
    def test_validate_empty_triangulation(self) -> None:
        """Triangulation vide = valide."""
        empty = Triangles(vertices=[], triangles=[])
        assert validate_triangulation(empty)

    @pytest.mark.unit
    def test_validate_single_triangle(self, sample_triangulation: Triangles) -> None:
        """Triangle simple = valide."""
        assert validate_triangulation(sample_triangulation)

    @pytest.mark.unit
    def test_validate_after_triangulation(self, large_point_set: list[Point]) -> None:
        """Sortie de triangulate doit être valide."""
        result = triangulate(large_point_set)
        assert validate_triangulation(result)
