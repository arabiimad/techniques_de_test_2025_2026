"""Client HTTP pour le PointSetManager."""

import os
import urllib.error
import urllib.request
import uuid

from triangulator.binary_codec import Point, decode_point_set
from triangulator.exceptions import (
    DecodingError,
    InvalidUUIDError,
    PointSetNotFoundError,
    ServiceUnavailableError,
)

DEFAULT_POINT_SET_MANAGER_URL = "http://localhost:5000"
TIMEOUT_SECONDS = 10


def get_point_set_manager_url() -> str:
    """URL du PointSetManager via env var POINT_SET_MANAGER_URL ou défaut localhost:5000."""
    return os.environ.get("POINT_SET_MANAGER_URL", DEFAULT_POINT_SET_MANAGER_URL)


def validate_uuid(uuid_string: str) -> str:
    """Valide un UUID et retourne sa forme normalisée. Lève InvalidUUIDError sinon."""
    try:
        if uuid_string is None:
            raise InvalidUUIDError("None")
        parsed = uuid.UUID(uuid_string)
        return str(parsed)
    except (ValueError, AttributeError, TypeError) as e:
        raise InvalidUUIDError(str(uuid_string)) from e


def fetch_point_set(point_set_id: str) -> list[Point]:
    """Récupère un PointSet via HTTP (version fonctionnelle, utilisée pour les tests rapides)."""
    validated_id = validate_uuid(point_set_id)

    base_url = get_point_set_manager_url()
    url = f"{base_url}/pointset/{validated_id}"

    try:
        request = urllib.request.Request(
            url,
            method="GET",
            headers={"Accept": "application/octet-stream"},
        )

        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            data = response.read()
            return decode_point_set(data)

    except urllib.error.HTTPError as e:
        if e.code == 400:
            raise InvalidUUIDError(point_set_id) from e
        if e.code == 404:
            raise PointSetNotFoundError(point_set_id) from e
        if e.code == 503:
            raise ServiceUnavailableError(
                "PointSetManager database is unavailable"
            ) from e
        raise ServiceUnavailableError(f"HTTP error {e.code}: {e.reason}") from e

    except urllib.error.URLError as e:
        raise ServiceUnavailableError(
            f"Cannot connect to PointSetManager: {e.reason}"
        ) from e

    except TimeoutError as e:
        raise ServiceUnavailableError("Connection to PointSetManager timed out") from e

    except DecodingError:
        raise

    except Exception as e:
        raise ServiceUnavailableError(f"Unexpected error: {e}") from e


class PointSetClient:
    """Client pour le PointSetManager, injectable et mockable pour les tests."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = TIMEOUT_SECONDS,
    ) -> None:
        """Configure URL et timeout (valeurs par défaut depuis env / constantes)."""
        self.base_url = base_url or get_point_set_manager_url()
        self.timeout = timeout

    def get_point_set(self, point_set_id: str) -> list[Point]:
        """GET /pointset/{id} et décode la réponse binaire."""
        validated_id = validate_uuid(point_set_id)

        url = f"{self.base_url}/pointset/{validated_id}"

        try:
            request = urllib.request.Request(
                url,
                method="GET",
                headers={"Accept": "application/octet-stream"},
            )

            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = response.read()
                return decode_point_set(data)

        except urllib.error.HTTPError as e:
            if e.code == 400:
                raise InvalidUUIDError(point_set_id) from e
            if e.code == 404:
                raise PointSetNotFoundError(point_set_id) from e
            if e.code == 503:
                raise ServiceUnavailableError(
                    "PointSetManager database is unavailable"
                ) from e
            raise ServiceUnavailableError(f"HTTP error {e.code}: {e.reason}") from e

        except urllib.error.URLError as e:
            raise ServiceUnavailableError(
                f"Cannot connect to PointSetManager: {e.reason}"
            ) from e

        except TimeoutError as e:
            raise ServiceUnavailableError(
                "Connection to PointSetManager timed out"
            ) from e

        except DecodingError:
            raise

        except Exception as e:
            raise ServiceUnavailableError(f"Unexpected error: {e}") from e
