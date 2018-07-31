API Documentation
=================
pulsar has a JSON API written in Python, using Flask. Endpoints are protected
by permissions, which can be assigned to users and user classes by site admins.
Authentication is also required for many endpoints. pulsar only supports token-based
authentication.

Requests are rate limited; by default limiting to 50 requests every 80 seconds per
API key, and a global limit of 90 requests every 80 seconds per account. Rate limits
are configuration settings specific to a site, so these values may not be consistent
with values on other sites.

All request data must be dictionaries encoded as JSON. Query arguments are occasionally
used as well. For boolean query arguments, ``1`` and ``true`` are accepted as True and
``0`` and ``false`` are accepted as False. Booleans in query arguments are interpreted
case insensitive.

.. toctree::
   :maxdepth: 2

   users
   permissions
   forums
   rules
