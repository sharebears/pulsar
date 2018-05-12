import flask
from . import bp

app = flask.current_app


@bp.route('/forums/categories', methods=['GET'])
def view_categories():
    """
    This endpoint allows users to view the available forum categories
    and the forums in each category, along with some metadata about
    each forum.

    .. :quickref: ForumCategory; View forum categories.

    **Example request**:

    .. sourcecode:: http

       POST /login HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "username": "lights",
         "password": "y-&~_Wbt7wjkUJdY<j-K",
         "persistent": true
       }

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "csrf_token": "d98a1a142ccae02be58ee64b",
         "response": {
           "active": true,
           "csrf_token": "d98a1a142ccae02be58ee64b",
           "hash": "abcdefghij",
           "ip": "127.0.0.1",
           "last_used": "1970-01-01T00:00:00.000001+00:00",
           "persistent": true,
           "user-agent": "curl/7.59.0"
         }
       }

    :json username: Desired username: must start with an alphanumeric
        character and can only contain alphanumeric characters,
        underscores, hyphens, and periods.
    :json password: Desired password: must be 12+ characters and contain
        at least one letter, one number, and one special character.
    :json persistent: (Optional) Whether or not to persist the session.

    :>json dict response: A session, see sessions_

    .. _sessions:

    :statuscode 200: Login successful
    :statuscode 401: Login unsuccessful
    """
    pass
