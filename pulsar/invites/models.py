import flask
import secrets
from sqlalchemy import func
from pulsar import db, cache


class Invite(db.Model):
    __tablename__ = 'invites'
    __cache_key__ = 'invites_{code}'
    __cache_key_of_user__ = 'invites_user_{user_id}'

    __serialize_self__ = ('code', 'inviter_id', 'email', 'time_sent', 'active', 'invitee')
    __serialize_detailed__ = __serialize_self__ + ('from_ip', )

    __permission_detailed__ = 'view_invites_others'

    code = db.Column(db.String(24), primary_key=True)
    inviter_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    invitee_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    email = db.Column(db.String(255), nullable=False)
    time_sent = db.Column(db.DateTime(timezone=True), server_default=func.now())
    from_ip = db.Column(db.String(39), nullable=False, server_default='0.0.0.0')
    active = db.Column(db.Boolean, nullable=False, index=True, server_default='t')

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
        invite = cls(
            inviter_id=inviter_id,
            code=code,
            email=email.lower().strip(),
            from_ip=ip)

        db.session.add(invite)
        db.session.commit()

        cache.cache_model(invite)
        cache.delete(cls.__cache_key_of_user__.format(user_id=inviter_id))
        return invite

    @classmethod
    def from_code(cls, code, include_dead=False):
        """
        Get an invite from its invite code.

        :param str code: The invite code
        :param bool include_dead: (Default ``False``) Whether or not to include expired
            invites in the search

        :return: A ``Invite`` object or ``None``
        """
        invite = cls.from_cache(
            key=cls.__cache_key__.format(code=code),
            query=cls.query.filter(cls.code == code))

        if invite and (include_dead or invite.active):
            return invite
        return None

    @classmethod
    def from_inviter(cls, inviter_id, include_dead=False):
        """
        Get all invites sent by a user.

        :param int inviter_id: The User ID of the inviter.
        :param bool include_dead: (Default ``False``) Whether or not to include dead
            invites in the list

        :return: A ``list`` of ``Invite`` objects
        """
        cache_key = cls.__cache_key_of_user__.format(user_id=inviter_id)
        invite_codes = cache.get(cache_key)
        if not invite_codes:
            invite_codes = [
                i[0] for i in db.session.query(cls.code).filter(
                    cls.inviter_id == inviter_id).all()]
            cache.set(cache_key, invite_codes)

        invites = []
        for code in invite_codes:
            invites.append(cls.from_code(code, include_dead=True))

        return [i for i in invites if i and (include_dead or i.active)]

    @property
    def cache_key(self):
        return self.__cache_key__.format(code=self.code)

    def belongs_to_user(self):
        return flask.g.user and self.inviter_id == flask.g.user.id
