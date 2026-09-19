"""Authenticated demo controls; all monetary execution stays inside PaperBroker."""
import os
import hmac
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, session
from .paper_controls import update_controls
from workers.paper_loop import PaperScheduler


def has_access():
    expected = os.environ.get("PAPER_CONTROL_TOKEN", "")
    supplied = request.headers.get("Authorization", "").removeprefix("Bearer ")
    return bool(expected) and (session.get("paper_operator") is True or hmac.compare_digest(expected, supplied))


def create_operator_blueprint(factory, config):
    bp = Blueprint("paper_operator", __name__)

    @bp.post('/api/paper/session')
    def login():
        expected = os.environ.get('PAPER_CONTROL_TOKEN', '')
        supplied = (request.get_json(silent=True) or {}).get('key', '')
        if not isinstance(supplied, str) or not expected or not hmac.compare_digest(expected, supplied):
            return jsonify(error='Portfolio access key is not valid'), 401
        session.clear()
        session['paper_operator'] = True
        return jsonify(authenticated=True, mode='PAPER')

    @bp.delete('/api/paper/session')
    def logout():
        session.clear()
        return jsonify(authenticated=False)

    @bp.post('/api/paper/controls')
    def controls():
        if not has_access():
            return jsonify(error='Unlock portfolio controls with your access key'), 401
        if config is None:
            return jsonify(error='Paper account is not configured'), 503
        repository = factory()
        try:
            result = update_controls(repository, config, request.get_json(silent=True))
            return jsonify(controls=result, mode='PAPER', live_execution=False)
        except ValueError as exc:
            return jsonify(error=str(exc)), 422
        finally:
            repository.close()

    @bp.post('/api/paper/cycle')
    def cycle():
        if not has_access():
            return jsonify(error='Unlock portfolio controls with your access key'), 401
        if config is None:
            return jsonify(error='Paper account is not configured'), 503
        repository = factory()
        try:
            job = PaperScheduler(repository, config.account_id, interval_seconds=config.interval_seconds).enqueue(datetime.now(timezone.utc).isoformat())
            return jsonify(state='SCHEDULED', job_key=job.job_key, mode='PAPER'), 202
        finally:
            repository.close()

    @bp.errorhandler(Exception)
    def unavailable(exc):
        from werkzeug.exceptions import HTTPException
        if isinstance(exc, HTTPException):
            return exc
        return jsonify(error='Paper controls unavailable; no change confirmed'), 503
    return bp
