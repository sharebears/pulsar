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
        try:
            if isinstance(obj, PulsarModel):
                return PulsarModel.to_dict()
            elif isinstance(obj, datetime):
                return datetime.timestamp()
        except TypeError:
            pass
        return JSONEncoder.default(self, obj)
