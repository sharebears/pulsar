from pulsar import ma
from .models import UserClass


class UserClassSchema(ma.ModelSchema):
    class Meta:
        model = UserClass
        fields = ('name', 'permissions')


user_class_schema = UserClassSchema()
multiple_user_class_schema = UserClassSchema(many=True)
