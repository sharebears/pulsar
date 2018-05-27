import json

import pytest

from conftest import add_permissions, check_json_response
from pulsar import cache
from pulsar.forums.models import ForumPoll, ForumPollChoice


def test_view_poll(app, authed_client):
    add_permissions(app, 'view_forums')
    response = authed_client.get('/forums/polls/1')
    check_json_response(response, {
        'id': 1,
        'featured': False,
        'question': 'Question 1',
        })
    assert response.status_code == 200
    assert len(response.get_json()['response']['choices']) == 3


def test_view_poll_nonexistent(app, authed_client):
    add_permissions(app, 'view_forums')
    response = authed_client.get('/forums/polls/99')
    check_json_response(response, 'ForumPoll 99 does not exist.')


def test_modify_poll_closed_featured(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_polls')
    ForumPoll.from_pk(3)  # cache it
    response = authed_client.put('/forums/polls/1', data=json.dumps({
        'closed': True, 'featured': True}))
    check_json_response(response, {
        'id': 1,
        'featured': True,
        'closed': True,
        })
    poll = ForumPoll.from_pk(1)
    assert poll.closed is True
    assert poll.featured is True
    assert ForumPoll.from_pk(3).featured is False


def test_modify_poll_unfeature(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_polls')
    authed_client.put('/forums/polls/3', data=json.dumps({
        'featured': False,
        }))
    assert ForumPoll.get_featured() is None
    assert not cache.get(ForumPoll.__cache_key_featured__)


def test_modify_poll_choices(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_polls')
    response = authed_client.put('/forums/polls/1', data=json.dumps({
        'choices': {
            'add': ['a', 'b', 'c'],
            'delete': [1, 2],
        }}))
    choices = response.get_json()['response']['choices']
    assert len(choices) == 4
    assert {'Choice C', 'a', 'b', 'c'} == {choice['choice'] for choice in choices}
    choices = ForumPollChoice.from_poll(1)
    assert {'Choice C', 'a', 'b', 'c'} == {choice.choice for choice in choices}


def test_modify_poll_choices_errors(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_polls')
    response = authed_client.put('/forums/polls/1', data=json.dumps({
        'choices': {
            'add': ['Choice A', 'Choice B'],
            'delete': [1, 5],
        }})).get_json()['response']
    assert 'Choice A' in response
    assert 'Choice B' in response
    assert 'The following poll choices could not be added: ' in response
    assert 'The following poll choices could not be deleted: 5.' in response


def test_modify_poll_choices_partial(app, authed_client):
    add_permissions(app, 'view_forums', 'modify_forum_polls')
    response = authed_client.put('/forums/polls/1', data=json.dumps({
        'choices': {
            'add': ['Choice A', 'Choice B'],
        }})).get_json()['response']
    assert 'Choice A' in response
    assert 'Choice B' in response
    assert 'The following poll choices could not be added: ' in response


def test_vote_poll(app, authed_client):
    add_permissions(app, 'view_forums', 'forums_polls_vote')
    response = authed_client.post('/forums/polls/choices/6/vote')
    check_json_response(response, 'You have successfully voted for choice 6.')
    assert ForumPollChoice.from_pk(6).answers == 1


@pytest.mark.parametrize(
    'choice_id', [1, 2])
def test_vote_poll_already_voted(app, authed_client, choice_id):
    add_permissions(app, 'view_forums', 'forums_polls_vote')
    response = authed_client.post(f'/forums/polls/choices/{choice_id}/vote')
    check_json_response(response, 'You have already voted on this poll.')


def test_vote_poll_doesnt_exist(app, authed_client):
    add_permissions(app, 'view_forums', 'forums_polls_vote')
    response = authed_client.post(f'/forums/polls/choices/10/vote')
    check_json_response(response, 'ForumPollChoice 10 does not exist.')
