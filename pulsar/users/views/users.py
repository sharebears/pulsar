import flask
from .. import bp
from ..models import User
from ..schemas import user_schema
from pulsar import _404Exception
from pulsar.utils import require_auth

app = flask.current_app


@bp.route('/users/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    """
    Return general information about a user with the given user ID.
    If the user is getting information about themselves,
    the API will also return their number of invites.

    .. :quickref: User; Get user information.

    **Example request**:

    .. sourcecode:: http

       GET /users/1 HTTP/1.1
       Host: pul.sar
       Accept: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
           "id": 1,
           "username": "lights",
           "invites": 2
         }
       }

    :>jsonarr int id: User ID of user
    :>jsonarr string username: Username of user
    :>jsonarr int invites: (Restricted to self view) Invites available to user

    :statuscode 200: User exists
    :statuscode 404: User does not exist
    """
    user = User.from_id(user_id)
    if not user:
        raise _404Exception('User')
    return user_schema.jsonify(user)
