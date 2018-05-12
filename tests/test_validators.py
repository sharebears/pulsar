import pytest
from voluptuous import Invalid
from pulsar.validators import bool_get


@pytest.mark.parametrize(
    'inputs, output', [
        ([True, '1', 'TruE', 'true'], True),
        ([False, '0', 'FaLsE', 'false'], False),
    ])
def test_bool_get(inputs, output):
    for input_ in inputs:
        assert output == bool_get(input_)


def test_bool_get_invalid():
    for input_ in [1, 0, 'Yes', 'No', '11']:
        with pytest.raises(Invalid):
            bool_get(input_)
