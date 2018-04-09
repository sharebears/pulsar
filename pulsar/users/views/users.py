import flask
from . import bp
from ..models import User
from ..schemas import user_schema
from pulsar import _404Exception
from pulsar.utils import require_auth

app = flask.current_app


@bp.route('/users/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    user = User.from_id(user_id)
    if not user:
        raise _404Exception('User')
    return user_schema.jsonify(user)
