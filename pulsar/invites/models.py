import flask
import secrets
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import INET
from pulsar import db, cache


class Invite(db.Model):
    __tablename__ = 'invites'
    __cache_key__ = 'invites_{id}'
    __cache_key_of_user__ = 'invites_user_{user_id}'

    __serialize_self__ = ('id', 'inviter_id', 'email', 'time_sent', 'active', 'invitee')
    __serialize_detailed__ = __serialize_self__ + ('from_ip', )

    __permission_detailed__ = 'view_invites_others'

    id = db.Column(db.String(24), primary_key=True)
    inviter_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    invitee_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    email = db.Column(db.String(255), nullable=False)
    time_sent = db.Column(db.DateTime(timezone=True), server_default=func.now())
    from_ip = db.Column(INET, nullable=False, server_default='0.0.0.0')
    expired = db.Column(db.Boolean, nullable=False, index=True, server_default='f')

    @property
    def invitee(self):
        from pulsar.models import User
        return User.from_id(self.invitee_id)

    @classmethod
    def generate_invite(cls, inviter_id, email, ip):
        """
        Generate a random invite code.

        :param int inviter_id: User ID of the inviter
        :param str email: E-mail to send the invite to
        :param str ip: IP address the invite was sent from
        """
        while True:
            code = secrets.token_hex(12)
            if not cls.from_code(code, include_dead=True):
                break
        cache.delete(cls.__cache_key_of_user__.format(user_id=inviter_id))
        return super().new(
            inviter_id=inviter_id,
            code=code,
            email=email.lower().strip(),
            from_ip=ip)

    @classmethod
    def from_inviter(cls, inviter_id, include_dead=False):
        """
        Get all invites sent by a user.

        :param int inviter_id: The User ID of the inviter.
        :param bool include_dead: (Default ``False``) Whether or not to include dead
            invites in the list

        :return: A ``list`` of ``Invite`` objects
        """
        return cls.get_many(
            key=cls.__cache_key_of_user__.format(user_id=inviter_id),
            filter=cls.inviter_id == inviter_id,
            order=cls.time_sent.desc(),
            include_dead=include_dead)

    def belongs_to_user(self):
        return flask.g.user and self.inviter_id == flask.g.user.id
