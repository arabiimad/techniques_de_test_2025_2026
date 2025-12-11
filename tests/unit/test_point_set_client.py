"""Tests du client PointSetManager."""

import pytest

from triangulator.exceptions import (
    InvalidUUIDError,
    PointSetNotFoundError,
    ServiceUnavailableError,
)
from triangulator.point_set_client import PointSetClient, validate_uuid


class TestValidateUUID:
    """validate_uuid."""

    @pytest.mark.unit
    def test_validate_valid_uuid(self, valid_uuid: str) -> None:
        """UUID classique."""
        result = validate_uuid(valid_uuid)
        assert result == valid_uuid

    @pytest.mark.unit
    def test_validate_valid_uuid_uppercase(self) -> None:
        """UUID en majuscules normalisé en minuscules."""
        uuid_upper = "123E4567-E89B-12D3-A456-426614174000"
        result = validate_uuid(uuid_upper)
        assert result.lower() == result

    @pytest.mark.unit
    def test_validate_invalid_uuid(self, invalid_uuid: str) -> None:
        """Pas un UUID → InvalidUUIDError."""
        with pytest.raises(InvalidUUIDError) as exc_info:
            validate_uuid(invalid_uuid)
        assert "invalid" in str(exc_info.value).lower()
        assert exc_info.value.code == "INVALID_UUID"

    @pytest.mark.unit
    def test_validate_empty_string(self) -> None:
        """Chaîne vide."""
        with pytest.raises(InvalidUUIDError):
            validate_uuid("")

    @pytest.mark.unit
    def test_validate_none(self) -> None:
        """None."""
        with pytest.raises(InvalidUUIDError):
            validate_uuid(None)  # type: ignore

    @pytest.mark.unit
    def test_validate_uuid_without_dashes(self) -> None:
        """Sans tirets : accepté."""
        uuid_no_dash = "123e4567e89b12d3a456426614174000"
        result = validate_uuid(uuid_no_dash)
        assert result is not None

    @pytest.mark.unit
    def test_validate_partial_uuid(self) -> None:
        """UUID coupé → rejet."""
        with pytest.raises(InvalidUUIDError):
            validate_uuid("123e4567-e89b")


class TestPointSetClientWithMock:
    """Tests avec le MockPointSetClient."""

    @pytest.mark.unit
    def test_get_point_set_success(
        self, mock_client, valid_uuid: str, triangle_points
    ) -> None:
        """Succès : on récupère les points configurés."""
        mock_client.set_points(valid_uuid, triangle_points)
        result = mock_client.get_point_set(valid_uuid)
        assert len(result) == len(triangle_points)

    @pytest.mark.unit
    def test_get_point_set_not_found(
        self, mock_client, valid_uuid: str, another_valid_uuid: str
    ) -> None:
        """UUID non configuré → PointSetNotFoundError."""
        mock_client.set_points(valid_uuid, [])
        with pytest.raises(PointSetNotFoundError) as exc_info:
            mock_client.get_point_set(another_valid_uuid)
        assert exc_info.value.code == "POINTSET_NOT_FOUND"
        assert another_valid_uuid in str(exc_info.value)

    @pytest.mark.unit
    def test_get_point_set_invalid_uuid(self, mock_client, invalid_uuid: str) -> None:
        """UUID invalide → InvalidUUIDError même côté mock."""
        with pytest.raises(InvalidUUIDError) as exc_info:
            mock_client.get_point_set(invalid_uuid)
        assert exc_info.value.code == "INVALID_UUID"

    @pytest.mark.unit
    def test_get_point_set_service_unavailable(
        self, mock_client, valid_uuid: str
    ) -> None:
        """Échec configuré → ServiceUnavailableError."""
        mock_client.set_failure(
            ServiceUnavailableError("PointSetManager is unavailable")
        )
        with pytest.raises(ServiceUnavailableError) as exc_info:
            mock_client.get_point_set(valid_uuid)
        assert exc_info.value.code == "SERVICE_UNAVAILABLE"


class TestPointSetClientConfiguration:
    """Configuration du client réel."""

    @pytest.mark.unit
    def test_client_default_url(self) -> None:
        """URL par défaut = localhost."""
        client = PointSetClient()
        assert "localhost" in client.base_url or "127.0.0.1" in client.base_url

    @pytest.mark.unit
    def test_client_custom_url(self) -> None:
        """URL custom respectée."""
        custom_url = "http://custom-server:8080"
        client = PointSetClient(base_url=custom_url)
        assert client.base_url == custom_url

    @pytest.mark.unit
    def test_client_custom_timeout(self) -> None:
        """Timeout custom respecté."""
        client = PointSetClient(timeout=30)
        assert client.timeout == 30


class TestPointSetClientIntegration:
    """Tests réseau réels - désactivés par défaut."""

    @pytest.mark.unit
    @pytest.mark.skip(reason="Nécessite un serveur PointSetManager en cours d'exécution")
    def test_real_connection(self) -> None:
        """Test contre un vrai serveur."""
        client = PointSetClient()
        with pytest.raises(ServiceUnavailableError):
            client.get_point_set("123e4567-e89b-12d3-a456-426614174000")
