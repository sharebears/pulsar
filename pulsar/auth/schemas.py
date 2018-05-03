from pulsar import ma
from .models import Session, APIKey


class SessionSchema(ma.ModelSchema):
    class Meta:
        model = Session
        fields = ('hash', 'last_used', 'ip', 'user_agent',
                  'csrf_token', 'persistent', 'active')


class APIKeySchema(ma.ModelSchema):
    class Meta:
        model = APIKey
        fields = ('hash', 'last_used', 'ip', 'user_agent', 'active', 'permissions')


session_schema = SessionSchema()
multiple_session_schema = SessionSchema(many=True)
api_key_schema = APIKeySchema()
multiple_api_key_schema = APIKeySchema(many=True)
