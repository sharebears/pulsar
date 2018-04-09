class APIException(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(self)
        self.message = message
        self.status_code = status_code

    def __repr__(self):
        return f'<APIException (Code: {self.status_code}) [Message: {self.message}]>'


class _500Exception(APIException):
    def __init__(self):
        super().__init__(
            message='Something went wrong with your request.',
            status_code=500)


class _405Exception(APIException):
    def __init__(self, resource='Resource'):
        super().__init__(
            message='Method not allowed for this resource.',
            status_code=404)


class _404Exception(APIException):
    def __init__(self, resource='Resource'):
        super().__init__(
            message=f'{resource} does not exist.',
            status_code=404)


class _403Exception(APIException):
    def __init__(self, masquerade=False, message=None):
        super().__init__(
            message=(message or 'You do not have permission to access this resource.'),
            status_code=403)

        if masquerade:
            self.status_code = 404
            self.message = 'Resource does not exist.'


class _401Exception(APIException):
    def __init__(self, message='Invalid authorization.'):
        super().__init__(
            message=message,
            status_code=401)


class _312Exception(APIException):
    "Hopefully keep Alastor away from this codebase."
    def __init__(self):
        super().__init__(
            message='Your account has been disabled.',
            status_code=403,
            )
