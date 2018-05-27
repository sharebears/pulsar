import os
import json

import flask

from pulsar import cache, APIException
from pulsar.utils import require_permission

bp = flask.Blueprint('rules', __name__)

PERMISSIONS = [
    'view_rules',
]

SECTIONS = [
    'golden',
]


def get_rules(section) -> dict:
    if section not in SECTIONS:
        raise APIException(f'{section} is not a valid section of the rules.')
    rules = cache.get(f'rules_{section}')
    if not rules:
        filename = os.path.join(os.path.dirname(__file__), f'{section}.json')
        with open(filename, 'r') as f:
            rules = json.load(f)
        cache.set(f'rules_{section}', rules, 0)
    return rules


@bp.route('/rules', methods=['GET'])
@require_permission('view_rules')
def view_rules_overview() -> flask.Response:
    return flask.jsonify(SECTIONS)


@require_permission('view_rules')
@bp.route('/rules/<section>', methods=['GET'])
def view_rules(section: str) -> flask.Response:
    return flask.jsonify(get_rules(section))
