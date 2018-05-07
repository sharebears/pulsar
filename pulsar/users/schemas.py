from .models import User
from pulsar import ma
from pulsar.auth.schemas import APIKeySchema, SessionSchema


class UserSchema(ma.ModelSchema):
    class Meta:
        model = User
        fields = ('id',
                  'username',
                  'user_class',
                  'secondary_classes',
                  'uploaded',
                  'downloaded',
                  'invites',
                  )


class DetailedUserSchema(ma.ModelSchema):

    class Meta:
        model = User
        fields = ('id',
                  'username',
                  'email',
                  'user_class',
                  'secondary_classes',
                  'uploaded',
                  'downloaded',
                  'invites',
                  'api_keys',
                  'sessions',
                  )

    api_keys = ma.Nested(APIKeySchema)
    sessions = ma.Nested(SessionSchema)


user_schema = UserSchema()
detailed_user_schema = DetailedUserSchema()
multiple_user_schema = UserSchema(many=True)
