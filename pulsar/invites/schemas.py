from pulsar import ma
from .models import Invite
from pulsar.users.schemas import UserSchema


class InviteSchema(ma.ModelSchema):
    class Meta:
        model = Invite
        fields = ('code', 'time_sent', 'email', 'active', 'invitee')

    invitee = ma.Nested(UserSchema)


invite_schema = InviteSchema()
invites_schema = InviteSchema(many=True)
