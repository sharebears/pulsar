from datetime import datetime

import pytest
import pytz

from pulsar import NewJSONEncoder


def test_failed_serialization_default():
    """Assert that serialization still fails for invalid inputs."""
    with pytest.raises(TypeError):
        NewJSONEncoder().default('a string')


def test_serialization_of_datetimes():
    """Make sure that datetimes are properly serialized in the new encoder."""
    time = datetime.utcnow().replace(tzinfo=pytz.utc)
    posix_time = int(time.timestamp())
    assert posix_time > 1500000000
    assert posix_time == NewJSONEncoder().default(time)


def test_serialization_of_sets():
    """Make sure that datetimes are properly serialized in the new encoder."""
    set_ = {1, 2, 3, 4, 5}
    list_ = NewJSONEncoder().default(set_)
    assert isinstance(list_, list)
    assert all(s in list_ for s in set_)
