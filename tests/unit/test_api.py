"""Tests de l'API Flask (via test_client + mock injecté)."""

import pytest

from triangulator.binary_codec import Point, decode_triangles
from triangulator.exceptions import (
    ServiceUnavailableError,
)


class TestTriangulationEndpoint:
    """GET /triangulation/<id>."""

    @pytest.mark.integration
    def test_triangulation_success(
        self,
        test_client,
        mock_client,
        valid_uuid: str,
        triangle_points: list[Point],
    ) -> None:
        """200 + binaire décodable quand tout va bien."""
        mock_client.set_points(valid_uuid, triangle_points)

        response = test_client.get(f"/triangulation/{valid_uuid}")

        assert response.status_code == 200
        assert response.content_type == "application/octet-stream"

        triangulation = decode_triangles(response.data)
        assert len(triangulation.vertices) == 3
        assert len(triangulation.triangles) == 1

    @pytest.mark.integration
    def test_triangulation_invalid_uuid(
        self, test_client, invalid_uuid: str
    ) -> None:
        """UUID pourri → 400 JSON."""
        response = test_client.get(f"/triangulation/{invalid_uuid}")

        assert response.status_code == 400
        assert response.content_type == "application/json"

        data = response.get_json()
        assert "code" in data
        assert "message" in data
        assert data["code"] == "INVALID_UUID"

    @pytest.mark.integration
    def test_triangulation_pointset_not_found(
        self, test_client, mock_client, valid_uuid: str
    ) -> None:
        """UUID valide mais inconnu → 404 JSON."""
        response = test_client.get(f"/triangulation/{valid_uuid}")

        assert response.status_code == 404
        assert response.content_type == "application/json"

        data = response.get_json()
        assert data["code"] == "POINTSET_NOT_FOUND"

    @pytest.mark.integration
    def test_triangulation_service_unavailable(
        self, test_client, mock_client, valid_uuid: str
    ) -> None:
        """Client down → 503 JSON."""
        mock_client.set_failure(ServiceUnavailableError("Service down"))

        response = test_client.get(f"/triangulation/{valid_uuid}")

        assert response.status_code == 503
        assert response.content_type == "application/json"

        data = response.get_json()
        assert data["code"] == "SERVICE_UNAVAILABLE"

    @pytest.mark.integration
    def test_triangulation_content_type(
        self, test_client, mock_client, valid_uuid: str, triangle_points: list[Point]
    ) -> None:
        """Content-Type binaire en cas de succès."""
        mock_client.set_points(valid_uuid, triangle_points)

        response = test_client.get(f"/triangulation/{valid_uuid}")

        assert response.status_code == 200
        assert response.content_type == "application/octet-stream"


class TestTriangulationEdgeCases:
    """Cas limites côté API."""

    @pytest.mark.integration
    def test_triangulation_empty_pointset(
        self, test_client, mock_client, valid_uuid: str
    ) -> None:
        """PointSet vide → 200 avec 0 sommet / 0 triangle."""
        mock_client.set_points(valid_uuid, [])

        response = test_client.get(f"/triangulation/{valid_uuid}")

        assert response.status_code == 200
        triangulation = decode_triangles(response.data)
        assert len(triangulation.vertices) == 0
        assert len(triangulation.triangles) == 0

    @pytest.mark.integration
    def test_triangulation_single_point(
        self, test_client, mock_client, valid_uuid: str, single_point: list[Point]
    ) -> None:
        """1 point → 200, 1 sommet, 0 triangle."""
        mock_client.set_points(valid_uuid, single_point)

        response = test_client.get(f"/triangulation/{valid_uuid}")

        assert response.status_code == 200
        triangulation = decode_triangles(response.data)
        assert len(triangulation.vertices) == 1
        assert len(triangulation.triangles) == 0

    @pytest.mark.integration
    def test_triangulation_two_points(
        self, test_client, mock_client, valid_uuid: str, two_points: list[Point]
    ) -> None:
        """2 points → 200, 2 sommets, 0 triangle."""
        mock_client.set_points(valid_uuid, two_points)

        response = test_client.get(f"/triangulation/{valid_uuid}")

        assert response.status_code == 200
        triangulation = decode_triangles(response.data)
        assert len(triangulation.vertices) == 2
        assert len(triangulation.triangles) == 0

    @pytest.mark.integration
    def test_triangulation_large_pointset(
        self, test_client, mock_client, valid_uuid: str, large_point_set: list[Point]
    ) -> None:
        """100 points → 200, des triangles."""
        mock_client.set_points(valid_uuid, large_point_set)

        response = test_client.get(f"/triangulation/{valid_uuid}")

        assert response.status_code == 200
        triangulation = decode_triangles(response.data)
        assert len(triangulation.triangles) > 0

    @pytest.mark.integration
    def test_triangulation_collinear_points(
        self, test_client, mock_client, valid_uuid: str, collinear_points: list[Point]
    ) -> None:
        """Points colinéaires → 200 (résultat dégénéré accepté)."""
        mock_client.set_points(valid_uuid, collinear_points)
        response = test_client.get(f"/triangulation/{valid_uuid}")
        assert response.status_code == 200


class TestHealthEndpoint:
    """/health."""

    @pytest.mark.integration
    def test_health_check(self, test_client) -> None:
        """/health → 200 + status healthy."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"


class TestErrorResponses:
    """Format des erreurs JSON."""

    @pytest.mark.integration
    def test_error_response_format_400(
        self, test_client, invalid_uuid: str
    ) -> None:
        """400 a code + message."""
        response = test_client.get(f"/triangulation/{invalid_uuid}")
        assert response.status_code == 400
        data = response.get_json()
        assert "code" in data
        assert "message" in data
        assert isinstance(data["code"], str)
        assert isinstance(data["message"], str)

    @pytest.mark.integration
    def test_error_response_format_404(
        self, test_client, mock_client, valid_uuid: str
    ) -> None:
        """404 a code + message."""
        response = test_client.get(f"/triangulation/{valid_uuid}")
        assert response.status_code == 404
        data = response.get_json()
        assert "code" in data
        assert "message" in data

    @pytest.mark.integration
    def test_error_response_format_503(
        self, test_client, mock_client, valid_uuid: str
    ) -> None:
        """503 a code + message."""
        mock_client.set_failure(ServiceUnavailableError())
        response = test_client.get(f"/triangulation/{valid_uuid}")
        assert response.status_code == 503
        data = response.get_json()
        assert "code" in data
        assert "message" in data


@pytest.mark.integration
class TestApiEndToEnd:
    """Quelques tests E2E."""

    def test_e2e_successful_triangulation(
        self,
        test_client,
        mock_client,
        valid_uuid: str,
        triangle_points: list[Point],
    ) -> None:
        """E2E succès."""
        mock_client.set_points(valid_uuid, triangle_points)
        response = test_client.get(f"/triangulation/{valid_uuid}")
        assert response.status_code == 200
        assert response.mimetype == "application/octet-stream"
        triangles = decode_triangles(response.data)
        assert len(triangles.vertices) == 3
        assert len(triangles.triangles) == 1

    def test_e2e_point_set_not_found(self, test_client, mock_client, valid_uuid: str) -> None:
        """E2E 404."""
        response = test_client.get(f"/triangulation/{valid_uuid}")
        assert response.status_code == 404
        json_data = response.get_json()
        assert json_data["code"] == "POINTSET_NOT_FOUND"
        assert "not found" in json_data["message"]
