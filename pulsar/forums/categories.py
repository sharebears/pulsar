import flask
from voluptuous import All, Any, Length, Optional, Range, Schema

from pulsar import APIException, db
from pulsar.forums.models import ForumCategory
from pulsar.utils import require_permission, validate_data
from pulsar.validators import bool_get

from . import bp

app = flask.current_app


VIEW_FORUM_CATEGORY_SCHEMA = Schema({
    'include_dead': bool_get,
    })


@bp.route('/forums/categories', methods=['GET'])
@require_permission('view_forums')
@validate_data(VIEW_FORUM_CATEGORY_SCHEMA)
def view_categories(include_dead: bool = False) -> flask.Response:
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
    categories = ForumCategory.get_all(
        include_dead=include_dead and flask.g.user.has_permission('modify_forums'))
    return flask.jsonify(categories)


ADD_FORUM_CATEGORY_SCHEMA = Schema({
    'name': All(str, Length(max=32)),
    Optional('description', default=None): Any(All(str, Length(max=1024)), None),
    Optional('position', default=0): All(int, Range(min=0, max=99999)),
    }, required=True)


@bp.route('/forums/categories', methods=['POST'])
@require_permission('modify_forums')
@validate_data(ADD_FORUM_CATEGORY_SCHEMA)
def add_category(name: str,
                 description: str = None,
                 position: int = 0) -> flask.Response:
    """
    This is the endpoint for forum category creation. The ``modify_forums`` permission
    is required to access this endpoint.

    .. :quickref: ForumCategory; Create a forum category.

    **Example request**:

    .. sourcecode:: http

       POST /forums/categories HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "name": "Support",
         "description": "The place for confused share bears.",
         "position": 6
       }

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


MODIFY_FORUM_CATEGORY_SCHEMA = Schema({
    'name': All(str, Length(max=32)),
    'description': All(str, Length(max=1024)),
    'position': All(int, Range(min=0, max=99999)),
    })


@bp.route('/forums/categories/<int:id>', methods=['PUT'])
@require_permission('modify_forums')
@validate_data(MODIFY_FORUM_CATEGORY_SCHEMA)
def edit_category(id: int,
                  name: str = None,
                  description: str = None,
                  position: int = None) -> flask.Response:
    """
    This is the endpoint for forum category editing. The ``modify_forums`` permission
    is required to access this endpoint. The name, description, and position of a forum
    category can be changed here.

    .. :quickref: ForumCategory; Edit a forum category.

    **Example request**:

    .. sourcecode:: http

       PUT /forums/categories/6 HTTP/1.1
       Host: pul.sar
       Accept: application/json
       Content-Type: application/json

       {
         "name": "Support",
         "description": "The place for **very** confused share bears.",
         "position": 99
       }


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

    :>json list response: The edited forum category

    :statuscode 200: Editing successful
    :statuscode 400: Editing unsuccessful
    :statuscode 404: Forum category does not exist
    """
    category = ForumCategory.from_pk(id, _404=True)
    if name:
        category.name = name
    if description:
        category.description = description
    if position is not None:
        category.position = position
    db.session.commit()
    return flask.jsonify(category)


@bp.route('/forums/categories/<int:id>', methods=['DELETE'])
@require_permission('modify_forums')
def delete_category(id: int) -> flask.Response:
    """
    This is the endpoint for forum category deletion . The ``modify_forums`` permission
    is required to access this endpoint. The category must have no forums assigned to it
    in order to delete it.

    .. :quickref: ForumCategory; Delete a forum category.

    **Example request**:

    .. sourcecode:: http

       DELETE /forums/categories/2 HTTP/1.1
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

    :>json list response: The newly deleted forum category

    :statuscode 200: Deletion successful
    :statuscode 400: Deletion unsuccessful
    :statuscode 404: Forum category does not exist
    """
    category = ForumCategory.from_pk(id, _404=True)
    if category.forums:
        raise APIException(
            'You cannot delete a forum category while it still has forums assigned to it.')
    category.deleted = True
    db.session.commit()
    return flask.jsonify(f'ForumCategory {id} ({category.name}) has been deleted.')
