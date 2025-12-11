"""Client HTTP pour le PointSetManager."""

import os

from triangulator.binary_codec import Point

DEFAULT_POINT_SET_MANAGER_URL = "http://localhost:5000"
TIMEOUT_SECONDS = 10


def get_point_set_manager_url() -> str:
    """URL du PointSetManager via env var POINT_SET_MANAGER_URL ou défaut localhost:5000."""
    return os.environ.get("POINT_SET_MANAGER_URL", DEFAULT_POINT_SET_MANAGER_URL)


def validate_uuid(uuid_string: str) -> str:
    """Valide un UUID et retourne sa forme normalisée. Lève InvalidUUIDError sinon."""
    raise NotImplementedError


def fetch_point_set(point_set_id: str) -> list[Point]:
    """Récupère un PointSet via HTTP."""
    raise NotImplementedError


class PointSetClient:
    """Client pour le PointSetManager, injectable et mockable pour les tests."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = TIMEOUT_SECONDS,
    ) -> None:
        """Configure URL et timeout."""
        self.base_url = base_url or get_point_set_manager_url()
        self.timeout = timeout

    def get_point_set(self, point_set_id: str) -> list[Point]:
        """GET /pointset/{id} et décode la réponse binaire."""
        raise NotImplementedError
