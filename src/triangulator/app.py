"""API Flask du Triangulator."""

from flask import Flask, Response, jsonify

from triangulator.binary_codec import encode_triangles
from triangulator.exceptions import (
    DecodingError,
    InvalidUUIDError,
    PointSetNotFoundError,
    ServiceUnavailableError,
    TriangulationError,
    TriangulatorError,
)
from triangulator.point_set_client import PointSetClient
from triangulator.triangulation import triangulate


def create_app(point_set_client: PointSetClient | None = None) -> Flask:
    """Construit l'app Flask, avec un client injectable pour les tests."""
    app = Flask(__name__)

    client = point_set_client or PointSetClient()

    @app.errorhandler(TriangulatorError)
    def handle_triangulator_error(error: TriangulatorError) -> tuple[Response, int]:
        """Mappe nos exceptions vers (JSON, code HTTP)."""
        status_codes = {
            InvalidUUIDError: 400,
            PointSetNotFoundError: 404,
            TriangulationError: 500,
            DecodingError: 500,
            ServiceUnavailableError: 503,
        }

        status_code = status_codes.get(type(error), 500)

        response = jsonify({"code": error.code, "message": error.message})
        return response, status_code

    @app.route("/triangulation/<point_set_id>", methods=["GET"])
    def get_triangulation(point_set_id: str) -> Response | tuple[Response, int]:
        """Récupère le PointSet, triangule, renvoie le binaire."""
        points = client.get_point_set(point_set_id)
        triangulation = triangulate(points)
        binary_data = encode_triangles(triangulation)

        return Response(
            binary_data,
            status=200,
            mimetype="application/octet-stream",
        )

    @app.route("/health", methods=["GET"])
    def health_check() -> tuple[Response, int]:
        """Healthcheck simple."""
        return jsonify({"status": "healthy"}), 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
