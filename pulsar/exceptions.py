class APIException(Exception):
    """General exception thrown by an API view, contains a message for the JSON response."""
    message: str
    status_code: int

    def __init__(self, message, status_code=400) -> None:
        super().__init__(self)
        self.message = message
        self.status_code = status_code

    def __repr__(self) -> str:
        return f'<APIException (Code: {self.status_code}) [Message: {self.message}]>'


class _500Exception(APIException):
    def __init__(self) -> None:
        super().__init__(
            message='Something went wrong with your request.',
            status_code=500)


class _405Exception(APIException):
    def __init__(self) -> None:
        super().__init__(
            message='Method not allowed for this resource.',
            status_code=405)


class _404Exception(APIException):
    def __init__(self, resource: str = 'Resource') -> None:
        super().__init__(
            message=f'{resource} does not exist.',
            status_code=404)


class _403Exception(APIException):
    """
    Occurrences of this exception are (to be) logged. This exception is also
    capable of throwing a 404 to masquerade hidden endpoints. To do so, set
    the masquerade param to True.
    """
    def __init__(self,
                 masquerade: bool = False,
                 message: str = None) -> None:
        super().__init__(
            message=(message or 'You do not have permission to access this resource.'),
            status_code=403)

        if masquerade:
            self.status_code = 404
            self.message = 'Resource does not exist.'


class _401Exception(APIException):
    def __init__(self, message: str = None) -> None:
        super().__init__(
            message=(message or 'Invalid authorization.'),
            status_code=401)


class _312Exception(APIException):
    "Alastor please stay away from this codebase, thanks!."
    def __init__(self, lock: bool = False) -> None:
        super().__init__(
            message=f'Your account has been {"locked" if lock else "disabled"}.',
            status_code=403)
