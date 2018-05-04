Development
===========

* All permission checks should be abstracted to a utility function,
  such as ``require_permission``, ``require_auth``, or ``choose_user``;
  or to the user object (``User.has_permission``).
