import flask
from voluptuous import Schema
from voluptuous.validators import Match
from .. import bp
from pulsar import db, APIException
from pulsar.auth.models import Session
from pulsar.utils import PASSWORD_REGEX, choose_user, validate_data, require_permission

app = flask.current_app

password_change_schema = Schema({
    'existing_password': str,
    'new_password': Match(PASSWORD_REGEX, msg=(
        'Password must be 12 or more characters and contain at least 1 letter, '
        '1 number, and 1 special character.')),
    }, required=True)


# TODO: Add Admin Log Decorator
@bp.route('/users/change_password', methods=['POST'])
@bp.route('/users/<int:user_id>/change_password', methods=['POST'])
@require_permission('change_password')
@validate_data(password_change_schema)
def change_password(existing_password, new_password, user_id=None):
    user = choose_user(user_id, 'change_password_others')
    if flask.g.user == user and not user.check_password(existing_password):
        raise APIException('Invalid existing password.')
    user.set_password(new_password)
    Session.expire_all_of_user(user.id)
    db.session.commit()
    return flask.jsonify('Password changed.')
