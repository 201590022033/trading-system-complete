"""Authenticated bounded local-data ingress; research reads are public."""
from datetime import datetime, timezone
import hmac
import os
from flask import Blueprint, jsonify, request
from .swing_research import accept_dataset, research_status


def create_research_blueprint(factory):
    bp = Blueprint("swing_research", __name__)

    @bp.post("/api/v1/swing-research/datasets")
    def upload():
        expected = os.environ.get("SWING_DATA_UPLOAD_TOKEN", "")
        supplied = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if not expected or not hmac.compare_digest(expected.encode(), supplied.encode()):
            return jsonify(error="Data upload authentication required"), 401
        if request.content_length is None or request.content_length > 2_000_000:
            return jsonify(error="Bounded dataset body required"), 413
        payload = request.get_json(silent=True)
        repository = factory()
        try:
            return jsonify(accept_dataset(repository, payload, datetime.now(timezone.utc))), 202
        except (ValueError, TypeError, KeyError, OverflowError):
            return jsonify(error="Dataset rejected: check canonical identity, dates, raw fields and bounds"), 422
        finally:
            repository.close()

    @bp.get("/api/v1/swing-research/status")
    def status():
        repository = factory()
        try:
            return jsonify(research_status(repository, datetime.now(timezone.utc)))
        finally:
            repository.close()

    @bp.errorhandler(Exception)
    def unavailable(exc):
        from werkzeug.exceptions import HTTPException
        return exc if isinstance(exc, HTTPException) else (jsonify(error="Swing research unavailable"), 503)
    return bp
