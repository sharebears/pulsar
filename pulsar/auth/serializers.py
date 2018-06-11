from pulsar.mixins import Serializer, Attribute


class APIKeySerializer(Serializer):
    hash = Attribute(permission='view_api_keys_others')
    user_id = Attribute(permission='view_api_keys_others')
    last_used = Attribute(permission='view_api_keys_others')
    ip = Attribute(permission='view_api_keys_others')
    user_agent = Attribute(permission='view_api_keys_others')
    revoked = Attribute(permission='view_api_keys_others')
    permissions = Attribute(permission='view_api_keys_others')
