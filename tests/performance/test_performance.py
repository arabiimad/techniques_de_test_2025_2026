"""Tests de perf - marqueur @pytest.mark.performance, exclus par défaut."""

import math
import time

import pytest

from triangulator.binary_codec import (
    Point,
    decode_point_set,
    decode_triangles,
    encode_point_set,
    encode_triangles,
)
from triangulator.triangulation import triangulate


def generate_random_points(n: int, seed: int = 42) -> list[Point]:
    """Génère n points pseudo-aléatoires déterministes (LCG simple)."""
    points = []
    x = seed
    for _ in range(n):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        px = (x / 0x7FFFFFFF) * 100
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        py = (x / 0x7FFFFFFF) * 100
        points.append(Point(px, py))
    return points


def generate_circular_points(n: int) -> list[Point]:
    """Génère n points sur un cercle de rayon 50 centré en (50, 50)."""
    return [
        Point(
            math.cos(2 * math.pi * i / n) * 50 + 50,
            math.sin(2 * math.pi * i / n) * 50 + 50,
        )
        for i in range(n)
    ]


class TestTriangulationPerformance:
    """Perfs triangulation."""

    @pytest.mark.performance
    def test_triangulation_10_points(self) -> None:
        """10 points < 10ms."""
        points = generate_random_points(10)
        start = time.perf_counter()
        result = triangulate(points)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.010
        assert len(result.triangles) > 0
        print(f"\nTriangulation 10 points: {elapsed*1000:.2f}ms")

    @pytest.mark.performance
    def test_triangulation_100_points(self) -> None:
        """100 points < 100ms."""
        points = generate_random_points(100)
        start = time.perf_counter()
        result = triangulate(points)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.100
        assert len(result.triangles) > 0
        print(f"\nTriangulation 100 points: {elapsed*1000:.2f}ms")

    @pytest.mark.performance
    def test_triangulation_1000_points(self) -> None:
        """1000 points < 1s."""
        points = generate_random_points(1000)
        start = time.perf_counter()
        result = triangulate(points)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0
        assert len(result.triangles) > 0
        print(f"\nTriangulation 1000 points: {elapsed*1000:.2f}ms")

    @pytest.mark.performance
    @pytest.mark.slow
    def test_triangulation_10000_points(self) -> None:
        """10000 points < 10s (slow)."""
        points = generate_random_points(10000)
        start = time.perf_counter()
        result = triangulate(points)
        elapsed = time.perf_counter() - start
        assert elapsed < 10.0
        assert len(result.triangles) > 0
        print(f"\nTriangulation 10000 points: {elapsed*1000:.2f}ms")


class TestEncodingPerformance:
    """Perfs encode/decode."""

    @pytest.mark.performance
    def test_encode_10000_points(self) -> None:
        """Encode 10k points < 100ms."""
        points = generate_random_points(10000)
        start = time.perf_counter()
        result = encode_point_set(points)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.100
        assert len(result) > 0
        print(f"\nEncodage 10000 points: {elapsed*1000:.2f}ms")

    @pytest.mark.performance
    def test_decode_10000_points(self) -> None:
        """Decode 10k points < 100ms."""
        points = generate_random_points(10000)
        encoded = encode_point_set(points)
        start = time.perf_counter()
        result = decode_point_set(encoded)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.100
        assert len(result) == 10000
        print(f"\nDécodage 10000 points: {elapsed*1000:.2f}ms")

    @pytest.mark.performance
    def test_encode_triangles_large(self) -> None:
        """Encode d'une grande triangulation."""
        points = generate_random_points(1000)
        triangulation = triangulate(points)
        start = time.perf_counter()
        _ = encode_triangles(triangulation)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.100
        print(f"\nEncodage triangulation (1000 points): {elapsed*1000:.2f}ms")

    @pytest.mark.performance
    def test_decode_triangles_large(self) -> None:
        """Decode d'une grande triangulation."""
        points = generate_random_points(1000)
        triangulation = triangulate(points)
        encoded = encode_triangles(triangulation)
        start = time.perf_counter()
        _ = decode_triangles(encoded)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.100
        print(f"\nDécodage triangulation (1000 points): {elapsed*1000:.2f}ms")


class TestScalability:
    """Scalabilité."""

    @pytest.mark.performance
    def test_triangulation_scalability(self) -> None:
        """Ratio temps/n*log(n) à peu près stable (facteur 10 max)."""
        sizes = [100, 200, 400, 800]
        times = []
        ratios = []

        for n in sizes:
            points = generate_random_points(n)
            start = time.perf_counter()
            triangulate(points)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            n_log_n = n * math.log2(n)
            ratio = elapsed / n_log_n
            ratios.append(ratio)

        max_ratio = max(ratios)
        min_ratio = min(ratios)

        print("\nScalabilité de la triangulation:")
        for i, n in enumerate(sizes):
            print(f"  n={n}: {times[i]*1000:.2f}ms, ratio={ratios[i]:.6f}")

        assert max_ratio / min_ratio < 10, "La complexité semble supérieure à O(n log n)"

    @pytest.mark.performance
    def test_encoding_scalability(self) -> None:
        """Encode doit être ~O(n) → temps double quand n double."""
        sizes = [1000, 2000, 4000, 8000]
        times = []

        for n in sizes:
            points = generate_random_points(n)
            start = time.perf_counter()
            encode_point_set(points)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        print("\nScalabilité de l'encodage:")
        for i, n in enumerate(sizes):
            print(f"  n={n}: {times[i]*1000:.2f}ms")

        for i in range(len(times) - 1):
            ratio = times[i + 1] / times[i] if times[i] > 0 else 0
            assert ratio < 4, f"Ratio trop élevé: {ratio}"


class TestWorstCaseScenarios:
    """Cas un peu pénibles."""

    @pytest.mark.performance
    def test_circular_points_performance(self) -> None:
        """500 points sur un cercle."""
        points = generate_circular_points(500)
        start = time.perf_counter()
        _ = triangulate(points)
        elapsed = time.perf_counter() - start
        print(f"\nTriangulation cercle (500 points): {elapsed*1000:.2f}ms")
        assert elapsed < 1.0

    @pytest.mark.performance
    def test_grid_points_performance(self) -> None:
        """Grille 50x50."""
        points = [Point(float(x), float(y)) for x in range(50) for y in range(50)]
        start = time.perf_counter()
        _ = triangulate(points)
        elapsed = time.perf_counter() - start
        print(f"\nTriangulation grille (2500 points): {elapsed*1000:.2f}ms")
        assert elapsed < 5.0

    @pytest.mark.performance
    def test_clustered_points_performance(self) -> None:
        """10 clusters de 100 points."""
        points = []
        for cluster in range(10):
            cx, cy = cluster * 20, cluster * 15
            for i in range(100):
                x = cx + (i % 10) * 0.1
                y = cy + (i // 10) * 0.1
                points.append(Point(x, y))

        start = time.perf_counter()
        _ = triangulate(points)
        elapsed = time.perf_counter() - start
        print(f"\nTriangulation clusters (1000 points): {elapsed*1000:.2f}ms")
        assert elapsed < 2.0


class TestMemoryBenchmarks:
    """Taille des buffers encodés."""

    @pytest.mark.performance
    def test_memory_encoded_size(self) -> None:
        """Taille = 4 + n*8."""
        sizes = [100, 1000, 10000]

        print("\nTaille des données encodées:")
        for n in sizes:
            points = generate_random_points(n)
            encoded = encode_point_set(points)
            expected = 4 + n * 8
            assert len(encoded) == expected
            print(f"  {n} points: {len(encoded)} bytes ({len(encoded)/1024:.1f} KB)")

    @pytest.mark.performance
    def test_memory_triangulation_size(self) -> None:
        """Taille d'une triangulation encodée."""
        points = generate_random_points(1000)
        triangulation = triangulate(points)
        encoded = encode_triangles(triangulation)

        num_vertices = len(triangulation.vertices)
        num_triangles = len(triangulation.triangles)

        print("\nTriangulation 1000 points:")
        print(f"  Sommets: {num_vertices}")
        print(f"  Triangles: {num_triangles}")
        print(f"  Taille encodée: {len(encoded)} bytes ({len(encoded)/1024:.1f} KB)")
