"""Package Triangulator."""

from triangulator.binary_codec import (
    decode_point_set,
    decode_triangles,
    encode_point_set,
    encode_triangles,
)
from triangulator.triangulation import triangulate

__all__ = [
    "decode_point_set",
    "encode_point_set",
    "decode_triangles",
    "encode_triangles",
    "triangulate",
]

__version__ = "1.0.0"
