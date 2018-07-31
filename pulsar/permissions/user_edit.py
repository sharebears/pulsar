import flask

from pulsar.utils import get_all_permissions, require_permission

from . import bp

app = flask.current_app


@bp.route('/permissions', methods=['GET'])
@require_permission('modify_permissions')
def view_permissions(user_id: int = None,
                     all: bool = False) -> flask.Response:
    """
    View all permissions available. Requires the ``modify_permissions`` permission.

    .. :quickref: Permission; View available permissions.

    **Example request**:

    .. parsed-literal::

       GET /permissions HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. parsed-literal::

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": [
           "list_permissions",
           "modify_permissions",
           "change_password"
         ]
       }

    :>json list response: A list of permission name strings

    :statuscode 200: View successful
    :statuscode 403: User lacks sufficient permissions to view permissions
    """
    return flask.jsonify({'permissions': get_all_permissions()})
