import secrets
from datetime import datetime
from typing import List

import flask
from sqlalchemy import and_, func
from sqlalchemy.dialects.postgresql import INET

from pulsar import cache, db
from pulsar.mixin import ModelMixin
from pulsar.users.models import User


class Invite(db.Model, ModelMixin):
    __tablename__: str = 'invites'
    __cache_key__: str = 'invites_{id}'
    __cache_key_of_user__: str = 'invites_user_{user_id}'

    __serialize_self__: tuple = (
        'id',
        'email',
        'time_sent',
        'expired',
        'invitee')
    __serialize_detailed__: tuple = __serialize_self__ + (
        'from_ip',
        'inviter')
    __serialize_nested_exclude__: tuple = (
        'inviter', )

    __permission_detailed__ = 'view_invites_others'

    id: str = db.Column(db.String(24), primary_key=True)
    inviter_id: int = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    invitee_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    email: str = db.Column(db.String(255), nullable=False)
    time_sent: datetime = db.Column(db.DateTime(timezone=True), server_default=func.now())
    from_ip: str = db.Column(INET, nullable=False, server_default='0.0.0.0')
    expired: bool = db.Column(db.Boolean, nullable=False, index=True, server_default='f')

    @classmethod
    def new(cls,
            inviter_id: int,
            email: str,
            ip: int) -> 'Invite':
        """
        Generate a random invite code.

        :param inviter_id: User ID of the inviter
        :param email:      E-mail to send the invite to
        :param ip:         IP address the invite was sent from
        """
        while True:
            id = secrets.token_hex(12)
            if not cls.from_id(id, include_dead=True):
                break
        cache.delete(cls.__cache_key_of_user__.format(user_id=inviter_id))
        return super()._new(
            inviter_id=inviter_id,
            id=id,
            email=email.lower().strip(),
            from_ip=ip)

    @classmethod
    def from_inviter(cls,
                     inviter_id: int,
                     include_dead: bool = False,
                     used: bool = False) -> List['Invite']:
        """
        Get all invites sent by a user.

        :param inviter_id:   The User ID of the inviter.
        :param include_dead: Whether or not to include dead invites in the list
        :param used:         Whether or not to include used invites in the list

        :return:             A list of invites sent by the inviter
        """
        filter = cls.inviter_id == inviter_id
        if used:
            filter = and_(filter, cls.invitee_id.isnot(None))  # type: ignore
        return cls.get_many(
            key=cls.__cache_key_of_user__.format(user_id=inviter_id),
            filter=filter,
            order=cls.time_sent.desc(),  # type: ignore
            include_dead=include_dead or used)

    @property
    def invitee(self) -> 'User':
        return User.from_id(self.invitee_id)

    @property
    def inviter(self) -> 'User':
        return User.from_id(self.inviter_id)

    def belongs_to_user(self) -> bool:
        """Returns whether or not the requesting user matches the inviter."""
        return flask.g.user is not None and self.inviter_id == flask.g.user.id
