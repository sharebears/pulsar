API Documentation
=================
pulsar has a JSON API written in Python, using Flask. Endpoints are protected
by permissions, which can be assigned to users and user classes by site admins.

Two forms of authentication are supported: session-based and token authentication.
More information is available in :doc:`authentication`.

`To-be-built:`
Requests are rate limited; by default limiting to 50 requests every 80 seconds per
session or API key, with a global limit of 70 requests every 80 seconds per account.

All request data must be dictionaries encoded as JSON. Query arguments are occasionally
used as well. For boolean query arguments, ``1`` and ``true`` are accepted as True and
``0`` and ``false`` are accepted as False. Booleans in query arguments are interpreted
as case insensitive.

.. toctree::
   :maxdepth: 2

   users
   authentication
   permissions
   invites
