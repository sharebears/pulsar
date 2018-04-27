from .. import bp
from pulsar.users.schemas import multiple_user_schema
from pulsar.utils import choose_user, require_permission


@bp.route('/invitees', methods=['GET'])
@bp.route('/invitees/user/<int:user_id>', methods=['GET'])
@require_permission('view_invites')
def view_invitees(user_id=None):
    user = choose_user(user_id, 'view_invites_others')
    return multiple_user_schema.jsonify(user.invitees)
