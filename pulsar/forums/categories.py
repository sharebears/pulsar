import flask
from voluptuous import Schema, Optional, Any, All, Length
from . import bp
from pulsar.models import ForumCategory
from pulsar.utils import many_to_dict, require_permission, validate_data

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
    return flask.jsonify(many_to_dict(categories))


add_forum_category_schema = Schema({
    'name': All(str, Length(max=32)),
    Optional('description', default=None): Any(str, None),
    Optional('position', default=0): int,
    }, required=True)


@bp.route('/forums/categories', methods=['POST'])
@require_permission('modify_forums')
@validate_data(add_forum_category_schema)
def add_category(name, description, position):
    """
    GOOd Docstring.
    """
    category = ForumCategory.new(
        name=name,
        description=description,
        position=position)
    return flask.jsonify(category.to_dict())
