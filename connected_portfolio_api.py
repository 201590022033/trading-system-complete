"""Connected account display and authenticated manual journal; no order routes."""
import re
from flask import Blueprint, jsonify, request
from application.opportunities.operator_api import has_access
from connected_accounts import connected_snapshot
from manual_demo_journal import ManualDemoJournal


def create_connected_blueprint(factory, provider=connected_snapshot):
    bp = Blueprint('connected_portfolio', __name__)

    @bp.get('/api/portfolio/accounts')
    def accounts():
        result = provider()
        # Future real-account adapters must not expose financial data anonymously.
        if not has_access():
            result = {**result, 'accounts': [a for a in result['accounts'] if a['environment'] == 'DEMO'],
                      'groups': {k: v for k, v in result['groups'].items() if k == 'DEMO'}}
        return jsonify(**result, control_access=has_access())

    @bp.route('/api/portfolio/accounts/<key>/trades', methods=['GET', 'POST'])
    @bp.post('/api/portfolio/accounts/<key>/trades/<trade_id>/close')
    def trades(key, trade_id=None):
        if not has_access():
            return jsonify(error='Unlock the journal with your portfolio access key'), 401
        if not re.fullmatch('[a-f0-9]{24}', key):
            return jsonify(error='Invalid account identity'), 422
        repo = factory()
        try:
            journal = ManualDemoJournal(repo)
            if request.method == 'GET':
                return jsonify(journal.review(key))
            body = request.get_json(silent=True)
            if trade_id:
                result = journal.close(key, trade_id, body)
            else:
                account = next((a for a in provider()['accounts'] if a['key'] == key), None)
                if not account:
                    raise ValueError('Connected account unavailable')
                result = journal.open(account, body)
            return jsonify(record=result, order_submitted=False), 200
        except ValueError as exc:
            return jsonify(error=str(exc)), 422
        finally:
            repo.close()

    @bp.errorhandler(Exception)
    def unavailable(exc):
        from werkzeug.exceptions import HTTPException
        if isinstance(exc, HTTPException):
            return exc
        return jsonify(error='Connected portfolio unavailable; retry with the same trade ID if a save was interrupted'), 503
    return bp
