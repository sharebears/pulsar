import pytest
from voluptuous import Invalid

from pulsar.validators import BoolGET


@pytest.mark.parametrize(
    'inputs, output', [
        ([True, '1', 'TruE', 'true'], True),
        ([False, '0', 'FaLsE', 'false'], False),
    ])
def test_BoolGET(inputs, output):
    """Bool get accepts all provided values."""
    for input_ in inputs:
        assert output == BoolGET(input_)


def test_BoolGET_invalid():
    """BoolGET only accepts 1/0 true/false string/booleans."""
    for input_ in [1, 0, 'Yes', 'No', '11']:
        with pytest.raises(Invalid):
            BoolGET(input_)
