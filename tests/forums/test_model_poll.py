import pytest

from pulsar import APIException, _403Exception, db
from pulsar.forums.models import ForumPoll, ForumPollAnswer, ForumPollChoice


def test_forum_poll_from_id(app, authed_client):
    poll = ForumPoll.from_pk(1)
    assert poll.question == 'Question 1'


def test_forum_poll_from_thread(app, authed_client):
    poll = ForumPoll.from_thread(1)
    assert poll.id == 1


def test_forum_poll_from_featured(app, authed_client):
    poll = ForumPoll.get_featured()
    assert poll.id == 3


def test_forum_poll_new(app, authed_client):
    poll = ForumPoll.new(thread_id=5, question='Una pregunta')
    assert poll.id == 5
    assert poll.thread_id == 5
    assert poll.question == 'Una pregunta'
    assert poll.closed is False
    assert poll.featured is False


def test_forum_poll_new_nonexistent_thread(app, authed_client):
    with pytest.raises(APIException):
        ForumPoll.new(thread_id=10, question='.')


def test_unfeature_poll(app, authed_client):
    ForumPoll.unfeature_existing()
    assert not ForumPoll.get_featured()
    assert ForumPoll.from_pk(3).featured is False
    ForumPoll.unfeature_existing()  # Validate no errors here


def test_poll_choices(app, authed_client):
    choices = ForumPoll.from_pk(1).choices
    assert {1, 2, 3} == set(c.id for c in choices)


def test_poll_choice_from_poll_nonexistent(app, authed_client):
    choices = ForumPollChoice.from_poll(4)
    assert choices == []


def test_poll_new_choice(app, authed_client):
    choice = ForumPollChoice.new(poll_id=3, choice='bitsu!')
    assert choice.id == 7
    assert choice.poll_id == 3
    assert choice.choice == 'bitsu!'
    assert {6, 7} == set(c.id for c in ForumPoll.from_pk(3).choices)


def test_poll_new_choice_nonexistent_poll(app, authed_client):
    with pytest.raises(APIException):
        ForumPollChoice.new(poll_id=99, choice='bitsu!')


def test_poll_answers(app, authed_client):
    assert ForumPollChoice.from_pk(1).answers == 2
    assert ForumPollChoice.from_pk(3).answers == 0


def test_poll_answer_new(app, authed_client):
    ForumPollChoice.from_pk(6).answers  # cache it
    answer = ForumPollAnswer.new(poll_id=3, user_id=2, choice_id=6)
    assert answer.poll_id == 3
    assert answer.user_id == 2
    assert answer.choice_id == 6
    assert ForumPollChoice.from_pk(6).answers == 1


def test_poll_answer_new_already_voted(app, authed_client):
    # ForumPollChoice.from_pk(3).answers  # cache it
    with pytest.raises(APIException) as e:
        ForumPollAnswer.new(poll_id=1, user_id=2, choice_id=3)
    assert e.value.message == 'You have already voted for this poll.'


@pytest.mark.parametrize(
    'poll_id, user_id, choice_id', [
        (8, 1, 2), (1, 1, 2), (1, 2, 5), (1, 2, 100)])
def test_poll_answer_invalid_data(app, authed_client, poll_id, user_id, choice_id):
    with pytest.raises(APIException):
        ForumPollAnswer.new(poll_id=poll_id, user_id=user_id, choice_id=choice_id)


def test_poll_no_permissions(app, authed_client):
    db.engine.execute("""DELETE FROM forums_permissions
                      WHERE permission = 'forums_forums_permission_2'""")
    db.engine.execute("""DELETE FROM forums_permissions
                      WHERE permission = 'forums_threads_permission_3'""")
    with pytest.raises(_403Exception):
        ForumPoll.from_pk(3, error=True)
