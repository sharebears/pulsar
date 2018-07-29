from pulsar.mixins import Attribute, Serializer


class UserSerializer(Serializer):
    id = Attribute()
    username = Attribute()
    enabled = Attribute()
    user_class = Attribute()
    secondary_classes = Attribute()
    uploaded = Attribute()
    downloaded = Attribute()
    email = Attribute(permission='moderate_users')
    locked = Attribute(permission='moderate_users')
    invites = Attribute(permission='moderate_users')
    inviter = Attribute(permission='moderate_users', self_access=False, nested=False)
    api_keys = Attribute(permission='moderate_users', nested=False)
    basic_permissions = Attribute(permission='moderate_users', self_access=False, nested=False)
    forum_permissions = Attribute(permission='moderate_users', nested=False)
    permissions = Attribute(permission='moderate_users_advanced', nested=False)


class InviteSerializer(Serializer):
    code = Attribute(permission='view_invites_others')
    email = Attribute(permission='view_invites_others')
    time_sent = Attribute(permission='view_invites_others')
    expired = Attribute(permission='view_invites_others')
    invitee = Attribute(permission='view_invites_others')
    from_ip = Attribute(permission='view_invites_others', self_access=False)
    inviter = Attribute(permission='view_invites_others', nested=False, self_access=False)


class APIKeySerializer(Serializer):
    hash = Attribute(permission='view_api_keys_others')
    user_id = Attribute(permission='view_api_keys_others')
    last_used = Attribute(permission='view_api_keys_others')
    ip = Attribute(permission='view_api_keys_others')
    user_agent = Attribute(permission='view_api_keys_others')
    revoked = Attribute(permission='view_api_keys_others')
    permissions = Attribute(permission='view_api_keys_others')
