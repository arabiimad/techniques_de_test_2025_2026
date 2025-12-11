"""Exceptions du Triangulator."""


class TriangulatorError(Exception):
    """Base des exceptions du service."""

    def __init__(self, code: str, message: str) -> None:
        """Construit l'exception avec un code interne et un message."""
        super().__init__(message)
        self.code = code
        self.message = message


class InvalidUUIDError(TriangulatorError):
    """UUID mal formé."""

    def __init__(self, uuid_string: str) -> None:
        """Stocke la chaîne fautive."""
        super().__init__(
            code="INVALID_UUID",
            message=f"Invalid UUID format: '{uuid_string}'",
        )


class PointSetNotFoundError(TriangulatorError):
    """PointSet inexistant côté PointSetManager."""

    def __init__(self, point_set_id: str) -> None:
        """Stocke l'id non trouvé."""
        super().__init__(
            code="POINTSET_NOT_FOUND",
            message=f"PointSet with ID '{point_set_id}' was not found",
        )


class ServiceUnavailableError(TriangulatorError):
    """PointSetManager indisponible (réseau, 503, timeout...)."""

    def __init__(self, reason: str = "Service temporarily unavailable") -> None:
        """Stocke la raison."""
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=reason,
        )


class DecodingError(TriangulatorError):
    """Données binaires invalides au décodage."""

    def __init__(self, reason: str = "Failed to decode binary data") -> None:
        """Stocke la raison."""
        super().__init__(
            code="DECODING_ERROR",
            message=reason,
        )


class EncodingError(TriangulatorError):
    """Erreur d'encodage binaire."""

    def __init__(self, reason: str = "Failed to encode data") -> None:
        """Stocke la raison."""
        super().__init__(
            code="ENCODING_ERROR",
            message=reason,
        )


class TriangulationError(TriangulatorError):
    """Échec de l'algo de triangulation."""

    def __init__(self, reason: str = "Triangulation computation failed") -> None:
        """Stocke la raison."""
        super().__init__(
            code="TRIANGULATION_FAILED",
            message=reason,
        )
