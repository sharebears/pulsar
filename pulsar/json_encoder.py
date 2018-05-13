from flask.json import JSONEncoder
from datetime import datetime


class JSONEncoder(JSONEncoder):
    """
    Custom JSON Encoder class to apply the to_dict()
    function to all PulsarModels and turn timestamps
    into unixtime.
    """

    def default(self, obj):
        from pulsar import PulsarModel
        if isinstance(obj, datetime):
            return datetime.timestamp()
        elif isinstance(obj, PulsarModel):
            return obj.to_dict()
        return super().default(obj)
