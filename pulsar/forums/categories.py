import flask
from voluptuous import All, Any, Length, Optional, Range, Schema

from pulsar.models import ForumCategory
from pulsar.utils import require_permission, validate_data

from . import bp

app = flask.current_app


@bp.route('/forums/categories', methods=['GET'])
@require_permission('view_forums')
def view_categories():
    """
    This endpoint allows users to view the available forum categories
    and the forums in each category, along with some information about
    each forum.

    .. :quickref: ForumCategory; View forum categories.

    **Example request**:

    .. sourcecode:: http

       GET /forums/categories HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": [
           {
           }
         ]
       }

    :>json list response: A list of forum categories

    :statuscode 200: View successful
    :statuscode 401: View unsuccessful
    """
    categories = ForumCategory.get_all()
    return flask.jsonify(categories)


ADD_FORUM_CATEGORY_SCHEMA = Schema({
    'name': All(str, Length(max=32)),
    Optional('description', default=None): Any(All(str, Length(max=1024)), None),
    Optional('position', default=0): All(int, Range(min=0, max=99999)),
    }, required=True)


@bp.route('/forums/categories', methods=['POST'])
@require_permission('modify_forums')
@validate_data(ADD_FORUM_CATEGORY_SCHEMA)
def add_category(name, description, position):
    """
    This is the endpoint for forum category creation. The ``modify_forums`` permission
    is required to access this endpoint.

    .. :quickref: ForumCategory; Create a ForumCategory.

    **Example request**:

    .. sourcecode:: http

       POST /forums/categories HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

    **Example response**:

    .. sourcecode:: http

       HTTP/1.1 200 OK
       Vary: Accept
       Content-Type: application/json

       {
         "status": "success",
         "response": {
         }
       }

    :>json list response: The newly created forum category

    :statuscode 200: Creation successful
    :statuscode 400: Creation unsuccessful
    """
    category = ForumCategory.new(
        name=name,
        description=description,
        position=position)
    return flask.jsonify(category)
