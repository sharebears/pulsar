# Current Path

- [x] Rate Limiting
- [x] Caching
- [x] Permissioned Serialization
- [ ] Boilerplate Refactors & Typing (Issues)
- [-] Forums
- [ ] Rules
- [ ] News Posts
- [ ] Index

# Issues
- [x] Add test for expired session / revoked API Key auth
- [x] User classes need unique lowercase constraints
- [x] Do integer voluptuous validators prevent overflow? A: Nope!
- [x] Abstract 404 exceptions to model queries
- [x] Set up pipenv dependencies
- [x] Static typing with annotations and mypy (well I did the basics)
- [x] Abstract model cache clears to the commit function
- [x] Take types out of documentation with https://github.com/agronholm/sphinx-autodoc-typehints
- [x] Document development tools in Installation & Development
- [x] Re-document style guide, include docstring guides, type annotation guides, and lax up on parenthesis
- [x] Fix type annotations for other models in `users.models`
- [x] Simplify ``check_permissions`` permissions/ validator complexity | gave up, exceptioned it
- [x] Documentation about model abstractions and column names / types in BaseModel
- [ ] Testing & Typing
- [ ] Script to analyse permission usage--iter through all files and compile list of
      require_permission, assert_permission, choose_user, has_permission and compare with
      get_all_permissions() | https://stackoverflow.com/a/25181706
- [ ] Should invite codes be stored in the URL?
- [ ] No authentication and no route should raise a 401, same with required_permission no authentication,
      although should still allow masquerade (not a 404 (can confuse clients))
- [ ] Need basic permissions access split from advanced (forums, wiki, torrent edit, irc)
- [ ] Need a way to serialize basic permissions for moderators

## Testing & Typing
* [x] Classify integration tests vs unit tests **(request tests = integration)**
- [x] Create serialization tests that validate the presence and accuracy
      of serialized data.
- [x] Change schema names to ALL_CAPS
- [x] Review tests for all schemas (``test_schemas.py``)
- [ ] Hypothesis property tests where possible
- [ ] Figure out how to fuzz test with hypothesis? (Assert no 500)
- [ ] Create stub files for external library interfaces that are used

## Tests Cleanup List
- [x] Cache
- [x] BaseModel
- [x] Validators
- [x] Serializer
- [x] Invites
- [x] Hooks
- [x] Users
- [x] Authentication
- [x] Permissions
- [ ] Forums


# TODO

## General
- [x] Form validation with voluptuous
- [x] Permissioned Serialization
- [ ] Docker/Vagrant environment

## Users
- [x] Administration Functions
- [x] Schema Completion
- [x] Registration
- [x] Invites
- [ ] User Stats model
- [ ] User Settings -- Define constant defaults and save user overrides of those defaults,
      creating a user property that caches the overrides and returns a dict of boolean/(0, 1, 2)
      user settings

## Permissions
- [x] Primary User Classes
- [x] Individual Permissions
- [x] Turn every endpoint into a permission?
- [x] Secondary User Classes

## Forums
- [x] Models
- [-] Category View
- [ ] Forum View
- [ ] Thread View
- [ ] Posts View
- [ ] Forum/Thread Permissions
- [ ] Subscriptions
- [ ] Last viewed post in a thread
- [ ] "viewed" boolean, clear on new post in thread

## Rules
- [ ] Fuck it, we're going to make these dictionaries and serve them
- [ ] Built in git versioning

## Index
- [ ] Basic user info, API version
- [ ] SiteStatus endpoint, yada yada
- [ ] News Posts

## Wiki
- [ ] Wiki Pages
- [ ] ID 1 Default Landing Page
- [ ] Permissions System
- [ ] Wiki Versioning (save history, let frontends do diffing)
- [ ] Wiki Log

## Site Log
- [ ] Table for log categories
- [ ] Site log table, insert-deletion function helpers

## Staff Tools
- [ ] Basic Site-Level Administration Tools
- [ ] Separate Repository * .gitignored

## Tors
- [ ] Global Base Torrent
- [ ] Global Base Group
- [ ] Global Base Uploader & Validation
- [ ] Global Base Torrent Editor
- [ ] Global Base Group Editor
- [ ] Get Group/Torrent
- [ ] Search Group/Torrent
- [ ] Delete

## Music
- [ ] Implement Torrent
- [ ] Implement Group
- [ ] Implement Uploader & Validation
- [ ] Implement Editors

## E-Books
- [ ] Implement Torrent
- [ ] Implement Group
- [ ] Implement Uploader & Validation
- [ ] Implement Editors

## Reports
- [ ] Reports Hub
- [ ] Take implementations of base model from forums/torrents/users with reportable = True

## Requests
- [ ] Creation/Editing/Deletion
- [ ] Filling/Unfilling
- [ ] View
- [ ] Search

## Collages - Collection of Groups
- [ ] Pagination
- [ ] View
- [ ] Search

## Search
- [ ] Search 1+ Categories Simultaneously
- [ ] Torrents, Collections, Requests, Forums, Wiki

## Popular (Top 10)
- [ ] Generated via scheduler
- [ ] Preserve history
- [ ] Filtering

## Scheduler
- [ ] Schedule tasks with Celery
- [ ] schedule.py per-module
- [ ] Session expiry
- [ ] Invite expiry
- [ ] Inactivity disables

## RSS Feeds
- [ ] Later

## Donations
- [ ] Unique wallet generation a la Gazelle


# Post-MVP

## General
- [ ] Sentry

## Production Debugging Features
- [ ] Hook into existing libs?

## User Stats & History
- [ ] Community Stats
- [ ] Data Visualization
