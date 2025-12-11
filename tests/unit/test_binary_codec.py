"""Tests du codec binaire."""

import struct

import pytest

from triangulator.binary_codec import (
    POINT_SIZE,
    TRIANGLE_SIZE,
    ULONG_SIZE,
    Point,
    Triangle,
    Triangles,
    decode_point_set,
    decode_triangles,
    encode_point_set,
    encode_triangles,
)
from triangulator.exceptions import DecodingError, EncodingError


class TestEncodePointSet:
    """encode_point_set."""

    @pytest.mark.unit
    def test_encode_empty_point_set(self, empty_point_set: list[Point]) -> None:
        """PointSet vide = 4 bytes (count=0)."""
        result = encode_point_set(empty_point_set)
        assert len(result) == ULONG_SIZE
        assert struct.unpack("<I", result)[0] == 0

    @pytest.mark.unit
    def test_encode_single_point(self, single_point: list[Point]) -> None:
        """1 point = 12 bytes."""
        result = encode_point_set(single_point)
        assert len(result) == ULONG_SIZE + POINT_SIZE
        assert struct.unpack("<I", result[:4])[0] == 1

    @pytest.mark.unit
    def test_encode_multiple_points(self, triangle_points: list[Point]) -> None:
        """3 points = 4 + 3*8 bytes."""
        result = encode_point_set(triangle_points)
        expected_size = ULONG_SIZE + len(triangle_points) * POINT_SIZE
        assert len(result) == expected_size
        count = struct.unpack("<I", result[:4])[0]
        assert count == 3

    @pytest.mark.unit
    def test_encode_point_set_from_tuples(self) -> None:
        """Accepte des tuples (x, y) comme des Point."""
        tuples = [(1.0, 2.0), (3.0, 4.0)]
        result = encode_point_set(tuples)
        expected = encode_point_set([Point(1.0, 2.0), Point(3.0, 4.0)])
        assert result == expected

    @pytest.mark.unit
    def test_encode_point_set_preserves_values(self) -> None:
        """Les coordonnées sont bien réinjectées tel quel (float32)."""
        points = [Point(1.5, -2.5), Point(0.0, 100.0)]
        result = encode_point_set(points)

        count = struct.unpack("<I", result[0:4])[0]
        assert count == 2

        x1 = struct.unpack("<f", result[4:8])[0]
        y1 = struct.unpack("<f", result[8:12])[0]
        assert abs(x1 - 1.5) < 1e-6
        assert abs(y1 - (-2.5)) < 1e-6

        x2 = struct.unpack("<f", result[12:16])[0]
        y2 = struct.unpack("<f", result[16:20])[0]
        assert abs(x2 - 0.0) < 1e-6
        assert abs(y2 - 100.0) < 1e-6


class TestDecodePointSet:
    """decode_point_set."""

    @pytest.mark.unit
    def test_decode_valid_point_set(
        self, valid_binary_point_set: bytes, triangle_points: list[Point]
    ) -> None:
        """Roundtrip basique : décodage donne les bons points."""
        result = decode_point_set(valid_binary_point_set)

        assert len(result) == len(triangle_points)
        for decoded, expected in zip(result, triangle_points, strict=True):
            assert abs(decoded.x - expected.x) < 1e-6
            assert abs(decoded.y - expected.y) < 1e-6

    @pytest.mark.unit
    def test_decode_corrupted_data(self, corrupted_binary_data: bytes) -> None:
        """Données invalides → DecodingError."""
        with pytest.raises(DecodingError):
            decode_point_set(corrupted_binary_data)

    @pytest.mark.unit
    def test_decode_truncated_data(self, truncated_binary_data: bytes) -> None:
        """Données tronquées → DecodingError avec message 'too short'."""
        with pytest.raises(DecodingError) as exc_info:
            decode_point_set(truncated_binary_data)
        assert "too short" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_decode_empty_data(self) -> None:
        """Bytes vides → DecodingError."""
        with pytest.raises(DecodingError):
            decode_point_set(b"")

    @pytest.mark.unit
    def test_decode_empty_point_set(self) -> None:
        """count=0 → liste vide."""
        data = struct.pack("<I", 0)
        result = decode_point_set(data)
        assert result == []


class TestPointSetRoundtrip:
    """Roundtrips encode → decode."""

    @pytest.mark.unit
    def test_roundtrip_empty(self, empty_point_set: list[Point]) -> None:
        """Vide."""
        encoded = encode_point_set(empty_point_set)
        decoded = decode_point_set(encoded)
        assert decoded == empty_point_set

    @pytest.mark.unit
    def test_roundtrip_single_point(self, single_point: list[Point]) -> None:
        """1 point."""
        encoded = encode_point_set(single_point)
        decoded = decode_point_set(encoded)

        assert len(decoded) == 1
        assert abs(decoded[0].x - single_point[0].x) < 1e-6
        assert abs(decoded[0].y - single_point[0].y) < 1e-6

    @pytest.mark.unit
    def test_roundtrip_multiple_points(self, square_points: list[Point]) -> None:
        """Plusieurs points."""
        encoded = encode_point_set(square_points)
        decoded = decode_point_set(encoded)

        assert len(decoded) == len(square_points)
        for d, s in zip(decoded, square_points, strict=True):
            assert abs(d.x - s.x) < 1e-6
            assert abs(d.y - s.y) < 1e-6

    @pytest.mark.unit
    def test_roundtrip_large_values(self) -> None:
        """Grandes et petites valeurs."""
        points = [Point(1e6, -1e6), Point(1e-6, 1e-6)]
        encoded = encode_point_set(points)
        decoded = decode_point_set(encoded)

        for d, p in zip(decoded, points, strict=True):
            assert abs(d.x - p.x) / max(abs(p.x), 1) < 1e-5
            assert abs(d.y - p.y) / max(abs(p.y), 1) < 1e-5


class TestEncodeTriangles:
    """encode_triangles."""

    @pytest.mark.unit
    def test_encode_simple_triangulation(
        self, sample_triangulation: Triangles
    ) -> None:
        """Triangulation simple : taille attendue 28 + 16 = 44 bytes."""
        result = encode_triangles(sample_triangulation)
        expected_size = (
            ULONG_SIZE
            + 3 * POINT_SIZE
            + ULONG_SIZE
            + 1 * TRIANGLE_SIZE
        )
        assert len(result) == expected_size

    @pytest.mark.unit
    def test_encode_empty_triangulation(self) -> None:
        """Sommets sans triangles : count_triangles = 0."""
        tri = Triangles(
            vertices=[Point(0, 0), Point(1, 0)],
            triangles=[],
        )
        result = encode_triangles(tri)

        expected_size = ULONG_SIZE + 2 * POINT_SIZE + ULONG_SIZE
        assert len(result) == expected_size

        triangle_count_offset = ULONG_SIZE + 2 * POINT_SIZE
        count = struct.unpack(
            "<I", result[triangle_count_offset : triangle_count_offset + 4]
        )[0]
        assert count == 0

    @pytest.mark.unit
    def test_encode_triangles_indices(self) -> None:
        """Vérifie que l'ordre i, j, k est préservé dans le binaire."""
        tri = Triangles(
            vertices=[Point(0, 0), Point(1, 0), Point(0.5, 1)],
            triangles=[Triangle(2, 1, 0)],
        )
        result = encode_triangles(tri)

        offset = ULONG_SIZE + 3 * POINT_SIZE + ULONG_SIZE
        i = struct.unpack("<I", result[offset : offset + 4])[0]
        j = struct.unpack("<I", result[offset + 4 : offset + 8])[0]
        k = struct.unpack("<I", result[offset + 8 : offset + 12])[0]

        assert i == 2
        assert j == 1
        assert k == 0


class TestDecodeTriangles:
    """decode_triangles."""

    @pytest.mark.unit
    def test_decode_valid_triangulation(
        self, sample_triangulation: Triangles
    ) -> None:
        """Roundtrip basique."""
        encoded = encode_triangles(sample_triangulation)
        decoded = decode_triangles(encoded)

        assert len(decoded.vertices) == len(sample_triangulation.vertices)
        assert len(decoded.triangles) == len(sample_triangulation.triangles)

    @pytest.mark.unit
    def test_decode_corrupted_triangles(self) -> None:
        """Bytes invalides → DecodingError."""
        with pytest.raises(DecodingError):
            decode_triangles(b"\x00\x01\x02")

    @pytest.mark.unit
    def test_decode_triangles_empty_data(self) -> None:
        """Bytes vides → DecodingError."""
        with pytest.raises(DecodingError):
            decode_triangles(b"")


class TestTrianglesRoundtrip:
    """Roundtrips Triangles."""

    @pytest.mark.unit
    def test_roundtrip_simple(self, sample_triangulation: Triangles) -> None:
        """Simple."""
        encoded = encode_triangles(sample_triangulation)
        decoded = decode_triangles(encoded)

        assert len(decoded.vertices) == len(sample_triangulation.vertices)
        for dv, sv in zip(decoded.vertices, sample_triangulation.vertices, strict=True):
            assert abs(dv.x - sv.x) < 1e-6
            assert abs(dv.y - sv.y) < 1e-6

        assert len(decoded.triangles) == len(sample_triangulation.triangles)
        for dt, st in zip(decoded.triangles, sample_triangulation.triangles, strict=True):
            assert dt.i == st.i
            assert dt.j == st.j
            assert dt.k == st.k

    @pytest.mark.unit
    def test_roundtrip_multiple_triangles(self) -> None:
        """Plusieurs triangles."""
        tri = Triangles(
            vertices=[
                Point(0, 0),
                Point(1, 0),
                Point(1, 1),
                Point(0, 1),
            ],
            triangles=[Triangle(0, 1, 2), Triangle(0, 2, 3)],
        )

        encoded = encode_triangles(tri)
        decoded = decode_triangles(encoded)

        assert len(decoded.triangles) == 2
        assert decoded.triangles[0] == Triangle(0, 1, 2)
        assert decoded.triangles[1] == Triangle(0, 2, 3)

    @pytest.mark.unit
    def test_roundtrip_no_triangles(self) -> None:
        """Sommets seuls, pas de triangles."""
        tri = Triangles(
            vertices=[Point(0, 0), Point(1, 1)],
            triangles=[],
        )

        encoded = encode_triangles(tri)
        decoded = decode_triangles(encoded)

        assert len(decoded.vertices) == 2
        assert len(decoded.triangles) == 0


class TestEncodingErrors:
    """Cas d'erreur encode."""

    @pytest.mark.unit
    def test_encode_point_set_with_invalid_data(self) -> None:
        """Valeurs non numériques → EncodingError."""
        invalid_points = [("not", "numbers")]
        with pytest.raises(EncodingError):
            encode_point_set(invalid_points)

    @pytest.mark.unit
    def test_encode_point_set_with_none_values(self) -> None:
        """None dans les coordonnées → EncodingError."""
        invalid_points = [(None, None)]
        with pytest.raises(EncodingError):
            encode_point_set(invalid_points)


class TestDecodingEdgeCases:
    """Cas limites decode."""

    @pytest.mark.unit
    def test_decode_point_set_incomplete_point_data(self) -> None:
        """1 point annoncé mais 4 bytes au lieu de 8."""
        data = struct.pack("<I", 1) + b"1234"
        with pytest.raises(DecodingError):
            decode_point_set(data)

    @pytest.mark.unit
    def test_decode_triangles_invalid_vertex_index(self) -> None:
        """Indice de sommet hors borne : decode passe quand même."""
        vertices_data = struct.pack("<I", 2)
        vertices_data += struct.pack("<ff", 0.0, 0.0)
        vertices_data += struct.pack("<ff", 1.0, 1.0)

        triangles_data = struct.pack("<I", 1)
        triangles_data += struct.pack("<III", 0, 1, 5)

        data = vertices_data + triangles_data

        result = decode_triangles(data)
        assert 5 in result.triangles[0]

    @pytest.mark.unit
    def test_decode_triangles_incomplete_triangle_data(self) -> None:
        """1 triangle annoncé mais seulement 8 bytes (au lieu de 12)."""
        vertices_data = struct.pack("<I", 3)
        vertices_data += struct.pack("<ff", 0.0, 0.0)
        vertices_data += struct.pack("<ff", 1.0, 0.0)
        vertices_data += struct.pack("<ff", 0.5, 1.0)

        triangles_data = struct.pack("<I", 1)
        triangles_data += b"12345678"

        data = vertices_data + triangles_data

        with pytest.raises(DecodingError):
            decode_triangles(data)


class TestExceptionRepresentation:
    """Format des exceptions custom."""

    @pytest.mark.unit
    def test_decoding_error_str(self) -> None:
        """DecodingError contient le message et le code."""
        error = DecodingError("Test error message")
        assert "Test error message" in str(error)
        assert error.code == "DECODING_ERROR"

    @pytest.mark.unit
    def test_encoding_error_str(self) -> None:
        """EncodingError contient le message et le code."""
        error = EncodingError("Test encoding error")
        assert "Test encoding error" in str(error)
        assert error.code == "ENCODING_ERROR"
