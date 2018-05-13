import flask
from flask.json import JSONEncoder
from datetime import datetime


class JSONEncoder(JSONEncoder):
    """
    Custom JSON Encoder class to apply the _to_dict() function to
    all PulsarModels and turn timestamps into unixtime. This encoder
    allows ``flask.jsonify`` to receive a ``PulsarModel`` subclass
    as an argument, which will then be turned into a dictionary
    automatically.
    """

    def default(self, obj):
        """
        Overridden default method for the JSONEncoder. The JSON encoder will
        now serialize all timestamps to POSIX time and turn PulsarModels
        into dictionaries.
        """
        from pulsar import PulsarModel
        if isinstance(obj, datetime):
            return int(obj.timestamp())
        elif isinstance(obj, PulsarModel):
            return self._to_dict(obj)
        else:
            return super().default(obj)

    def _to_dict(self, model, nested=False):
        """
        Convert the model to a dictionary based on its defined serializable attributes.
        ``PulsarModel`` objects embedded in the dictionary or lists in the dictionary
        will be replaced with the result of their ``_to_dict`` methods.

        :param bool detailed: Whether or not to include detailed serializable attributes
        :param bool very_detailed: Whether or not to include very detailed serializable attributes

        :return: The ``dict`` of serialized attributes
        """
        attrs = model.__serialize__
        if model.belongs_to_user():
            attrs += model.__serialize_self__
        if flask.g.user and flask.g.user.has_permission(model.__permission_detailed__):
            attrs += model.__serialize_detailed__
        if flask.g.user and flask.g.user.has_permission(model.__permission_very_detailed__):
            attrs += model.__serialize_very_detailed__
        if nested:
            attrs += model.__serialize_nested_include__
            attrs = [a for a in attrs if a not in model.__serialize_nested_exclude__]

        return self._objects_to_dict(
            {attr: getattr(model, attr, None) for attr in list(set(attrs))})

    def _objects_to_dict(self, dict_):
        """
        Iterate through all values inside a dictionary and "fix" a dictionary to be
        JSON serializable by applying the _to_dict() function to all embedded models.
        All datetime objects are converted to a POSIX timestamp (seconds since epoch).

        :param dict dict_: The dictionary to iterate over and make JSON serializable

        :return: A JSON serializable ``dict``
        """
        from pulsar import PulsarModel

        def iter_handler(value):
            if isinstance(value, dict):
                return self._objects_to_dict(value)
            elif isinstance(value, list):
                new_value = []
                for i, v2 in enumerate(value):
                    if v2 is not None:
                        new_value.append(iter_handler(v2))
                return new_value
            elif isinstance(value, PulsarModel):
                return self._to_dict(value, nested=True)
            elif isinstance(value, datetime):
                return int(value.timestamp())
            return value

        for k, v in dict_.items():
            dict_[k] = iter_handler(v)

        return dict_
