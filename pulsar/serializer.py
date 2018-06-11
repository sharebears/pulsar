from datetime import datetime

from flask.json import JSONEncoder


class NewJSONEncoder(JSONEncoder):
    """
    Custom JSON Encoder class to apply the _to_dict() function to
    all SinglePKMixins and turn timestamps into unixtime. This encoder
    allows ``flask.jsonify`` to receive a ``SinglePKMixin`` subclass
    as an argument, which will then be turned into a dictionary
    automatically.
    """

    def default(self, obj):
        """
        Overridden default method for the JSONEncoder. The JSON encoder will
        now serialize all timestamps to POSIX time and turn SinglePKMixins
        into dictionaries.
        """
        from pulsar.mixins import SinglePKMixin
        if isinstance(obj, datetime):
            return int(obj.timestamp())
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, SinglePKMixin):
            data = obj.serialize()
            return self._objects_to_dict(data) if data else None
        return super().default(obj)

    def _objects_to_dict(self, dict_: dict) -> dict:
        """
        Iterate through all values inside a dictionary and "fix" a dictionary to be
        JSON serializable by applying the _to_dict() function to all embedded models.
        All datetime objects are converted to a POSIX timestamp (seconds since epoch).
        This function only supports converting ``dict``s, ``list``s, ``SinglePKMixin``s,
        and ``datetimes``. If the value was originally serializable, it will remain
        serializable. Keys are not modified, so they must be JSON serializable.
        If your serialization needs are more complex, feel free to add to the function.

        :param dict_: The dictionary to iterate over and make JSON serializable
        :return:      A JSON serializable dict of all the elements inside the original dict
        """
        from pulsar.mixins import SinglePKMixin

        def iter_handler(value):
            if isinstance(value, dict):
                return self._objects_to_dict(value)
            if isinstance(value, SinglePKMixin):
                return self._objects_to_dict(value.serialize(nested=True))
            if isinstance(value, set):
                return list(value)
            if isinstance(value, datetime):
                return int(value.timestamp())
            if isinstance(value, list):
                new_value = []
                for i, v2 in enumerate(value):
                    if v2 is not None:
                        new_value.append(iter_handler(v2))
                return new_value
            return value

        for k, v in dict_.items():
            dict_[k] = iter_handler(v)

        return dict_
