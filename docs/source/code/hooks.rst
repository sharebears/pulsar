Request Hooks
=============

These hooks run before and after each request gets sent to a
controller, taking care of various checks and overrides that
apply to every view.

Before
------

Before relaying the request to its proper controller, check the
authentication of the requester, either with a session or an
API key. If the requester has the ``no_ip_history`` permission,
set their IP to ``127.0.0.1``. If the user authenticated via
session, also validate their CSRF token.

.. automodule:: pulsar.hooks.before
    :members:
    :show-inheritance:

After
-----

After receiving a response from the controller, wrap it in
a homogenized response dictionary and serialize it to JSON.
The response dictionary will have a ``status`` key and,
if the request came with session based authentication, a
CRSF token.

.. automodule:: pulsar.hooks.after
    :members:
    :show-inheritance:
