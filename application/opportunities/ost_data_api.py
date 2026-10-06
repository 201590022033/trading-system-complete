"""Local-only export ingress. No login, session, cookie or password endpoint."""
from datetime import datetime, timezone
import os
from urllib.parse import urlsplit
from flask import Blueprint, jsonify, request
from .ost_data import coverage, install_exports, read_primary, ROOT


def create_ost_blueprint(factory, folder=ROOT):
    bp = Blueprint('ost_onboarding', __name__)

    def local_import_allowed():
        return (os.environ.get('OST_LOCAL_IMPORT_ENABLED') == '1'
            and not os.environ.get('RAILWAY_ENVIRONMENT_ID')
            and request.remote_addr in ('127.0.0.1', '::1')
            and urlsplit(request.host_url).hostname in ('127.0.0.1', 'localhost', '::1'))

    @bp.get('/api/v1/ost/onboarding')
    def status():
        now = datetime.now(timezone.utc)
        if not os.environ.get('RAILWAY_ENVIRONMENT_ID'):
            data = read_primary(folder)
        else:
            from .swing_research import latest_dataset
            repo = factory()
            try: data = latest_dataset(repo)
            finally: repo.close()
        result = coverage(data, now)
        result['local_import_available'] = local_import_allowed()
        return jsonify(result)

    @bp.post('/api/v1/ost/import')
    def import_export():
        if not local_import_allowed() or request.headers.get('Origin') != request.host_url.rstrip('/'):
            return jsonify(error='Import requires the local dashboard and same-origin request'), 403
        if request.content_length is None or request.content_length > 2_100_000:
            return jsonify(error='Maximum request size is 2.1 MB'), 413
        try:
            data = request.get_json(silent=True)
            if not isinstance(data, dict) or data.get('instrument_confirmed') is not True:
                raise ValueError('instrument confirmation required')
            rows = data['exports']
            if not isinstance(rows, list) or not 1 <= len(rows) <= 34:
                raise ValueError('bounded exports required')
            exports = [{'instrument_id': row['instrument_id'], 'acquired_at': row['acquired_at'],
                        'raw': row['csv'].encode('utf-8')} for row in rows]
            result = install_exports(exports, datetime.now(timezone.utc), folder)
            result['upload_state'] = 'LOCAL_ONLY_NEXT_SCHEDULED_UPLOAD'
            return jsonify(result), 201
        except (ValueError, KeyError, TypeError, UnicodeError, OverflowError):
            return jsonify(error='Export rejected. Check OST headers, selected instrument, actual capture time, numeric values and duplicates.'), 422

    @bp.errorhandler(Exception)
    def failed(exc):
        from werkzeug.exceptions import HTTPException
        return exc if isinstance(exc, HTTPException) else (jsonify(error='OST onboarding unavailable'), 503)
    return bp
