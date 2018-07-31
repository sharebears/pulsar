These are the objects returned in API responses. Attributes/keys of objects
are permissioned and restricted based on the accessing user, as well as whether
or not they are nested in another object.

Every object on this page will have an example JSON and what each attribute/key
is.

Objects
=======

APIKey
------

.. parsed-literal::
  {
    "revoked": false,
    "user_id": 1,
    "hash": "abcdefghij",
    "ip": "127.0.0.1",
    "last_used": "1970-01-01T00:00:00.000001+00:00",
    "user-agent": "curl/7.59.0",
    "permissions": [
      "view_api_keys",
      "send_invites"
    ]
  }

* **revoked** - Whether or not the API key is revoked
* **hash** - The identification id of the API key
* **ip** - The last IP to access the API key
* **user-agent** - The last User Agent to access the API key
* **permissions** - A list of permissions allowed to the API key, encoded as ``str``
