"""Fixtures partagées + config pytest."""

import pytest

from triangulator.app import create_app
from triangulator.binary_codec import Point, Triangle, Triangles, encode_point_set


@pytest.fixture
def empty_point_set() -> list[Point]:
    """Liste vide."""
    return []


@pytest.fixture
def single_point() -> list[Point]:
    """Un seul point."""
    return [Point(1.0, 2.0)]


@pytest.fixture
def two_points() -> list[Point]:
    """Deux points."""
    return [Point(0.0, 0.0), Point(1.0, 1.0)]


@pytest.fixture
def triangle_points() -> list[Point]:
    """3 points qui forment un triangle."""
    return [Point(0.0, 0.0), Point(1.0, 0.0), Point(0.5, 1.0)]


@pytest.fixture
def square_points() -> list[Point]:
    """4 points en carré."""
    return [Point(0.0, 0.0), Point(1.0, 0.0), Point(1.0, 1.0), Point(0.0, 1.0)]


@pytest.fixture
def collinear_points() -> list[Point]:
    """Points alignés sur y = x."""
    return [Point(0.0, 0.0), Point(1.0, 1.0), Point(2.0, 2.0), Point(3.0, 3.0)]


@pytest.fixture
def duplicate_points() -> list[Point]:
    """Liste avec un doublon."""
    return [Point(0.0, 0.0), Point(1.0, 1.0), Point(0.0, 0.0), Point(2.0, 2.0)]


@pytest.fixture
def large_point_set() -> list[Point]:
    """100 points pour les tests un peu plus gros."""
    import math

    points = []
    for i in range(100):
        angle = 2 * math.pi * i / 100
        x = math.cos(angle) + 0.1 * (i % 10)
        y = math.sin(angle) + 0.1 * (i % 10)
        points.append(Point(x, y))
    return points


@pytest.fixture
def sample_triangulation() -> Triangles:
    """Triangulation de référence : 3 sommets, 1 triangle."""
    vertices = [Point(0.0, 0.0), Point(1.0, 0.0), Point(0.5, 1.0)]
    triangles = [Triangle(0, 1, 2)]
    return Triangles(vertices=vertices, triangles=triangles)


@pytest.fixture
def valid_binary_point_set(triangle_points: list[Point]) -> bytes:
    """Encodage binaire des triangle_points."""
    return encode_point_set(triangle_points)


@pytest.fixture
def corrupted_binary_data() -> bytes:
    """Bytes invalides."""
    return b"\x00\x01\x02\x03"


@pytest.fixture
def truncated_binary_data() -> bytes:
    """Annonce 5 points mais pas assez de bytes."""
    return b"\x05\x00\x00\x00\x00\x00\x80\x3f"


@pytest.fixture
def valid_uuid() -> str:
    """UUID valide."""
    return "123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture
def invalid_uuid() -> str:
    """Chaîne qui n'est pas un UUID."""
    return "not-a-valid-uuid"


@pytest.fixture
def another_valid_uuid() -> str:
    """Autre UUID valide."""
    return "550e8400-e29b-41d4-a716-446655440000"


class MockPointSetClient:
    """Mock du PointSetClient, configurable via set_points / set_failure."""

    def __init__(self) -> None:
        """Init."""
        self.points: dict[str, list[Point]] = {}
        self.should_fail: str | None = None
        self.fail_with: Exception | None = None

    def set_points(self, point_set_id: str, points: list[Point]) -> None:
        """Configure les points renvoyés pour un id."""
        self.points[point_set_id] = points

    def set_failure(self, error: Exception) -> None:
        """Configure une exception à lever."""
        self.fail_with = error

    def get_point_set(self, point_set_id: str) -> list[Point]:
        """Renvoie les points configurés ou lève l'erreur configurée."""
        from triangulator.exceptions import PointSetNotFoundError
        from triangulator.point_set_client import validate_uuid

        validate_uuid(point_set_id)

        if self.fail_with:
            raise self.fail_with

        if point_set_id not in self.points:
            raise PointSetNotFoundError(point_set_id)

        return self.points[point_set_id]


@pytest.fixture
def mock_client() -> MockPointSetClient:
    """Mock client."""
    return MockPointSetClient()


@pytest.fixture
def test_app(mock_client: MockPointSetClient):
    """App Flask avec le mock injecté, TESTING=True."""
    app = create_app(point_set_client=mock_client)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def test_client(test_app):
    """Client Flask de test."""
    return test_app.test_client()


def pytest_configure(config):
    """Enregistre les marqueurs custom."""
    config.addinivalue_line("markers", "unit: Tests unitaires rapides")
    config.addinivalue_line("markers", "integration: Tests d'intégration")
    config.addinivalue_line(
        "markers", "performance: Tests de performance (exclus par défaut)"
    )
    config.addinivalue_line("markers", "slow: Tests lents (> 1s)")
