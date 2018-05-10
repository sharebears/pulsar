import secrets
from sqlalchemy import func
from pulsar import db


class Invite(db.Model):
    __tablename__ = 'invites'
    __serializable_attrs__ = ('code', 'inviter_id', 'email',
                              'time_sent', 'active', 'invitee')

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
        from pulsar.users.models import User
        return User.from_id(self.invitee_id) if self.invitee_id else None

    @classmethod
    def generate_invite(cls, inviter_id, email, ip):
        while True:
            code = secrets.token_hex(12)
            if not cls.from_code(code, include_dead=True):
                break
        return cls(
            inviter_id=inviter_id,
            code=code,
            email=email.lower().strip(),
            from_ip=ip,
            )

    @classmethod
    def from_code(cls, code, include_dead=False):
        query = cls.query.filter(cls.code == code)
        if not include_dead:
            query = query.filter(cls.active == 't')
        return query.one_or_none()

    @classmethod
    def from_inviter(cls, user_id, include_dead=False):
        query = cls.query.filter(cls.inviter_id == user_id)
        if not include_dead:
            query = query.filter(cls.active == 't')
        return query.all()
