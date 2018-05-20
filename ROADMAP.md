# Current Path

- [x] Rate Limiting
- [x] Caching
- [x] Permissioned Serialization
- [x] Boilerplate Refactors & Typing (Issues)
- [x] Forums
- [ ] Rules
- [ ] News Posts
- [ ] Index

# Issues
- [x] Refactor the tests

- [ ] Add tests for all lowercased schemas and convert them to uppercase
- [ ] Take cache tests out of views and move them into model tests, generally reduce the amount of shit in view tests

- [ ] Script to analyse permission usage--iterate through all files and compile list of
      require_permission, assert_permission, choose_user, has_permission and compare with
      get_all_permissions() | https://stackoverflow.com/a/25181706

- [ ] Should invite codes be stored in the URL? No! Query parameters!

- [ ] No authentication and no route should raise a 401, same with required_permission no authentication,
      although should still allow masquerade (not a 404 (can confuse clients))

- [ ] Need basic permissions access split from advanced (forums, wiki, torrent edit, irc)
- [ ] Need a way to serialize basic permissions for moderators

- [ ] Typing Stubs
- [ ] Hypothesis property testing for the schemas and validators
- [ ] Review HTTP codes in documentation and the return values
- [ ] Review usage of optional in .new(**kwarg**) stuff

- [ ] Change \_404 argument in from_id to just use classname
- [ ] Built in debug logging?
- [ ] Fix PUT endpoints to be one change total, not one change per model
 

# TODO

## General
- [x] Form validation with voluptuous
- [x] Permissioned Serialization
- [ ] Docker/Vagrant environment
- [ ] More inventive and free serialization - Define objects for serialization and have them
      use custom kwarg arguments which are passed down to all nested models?
     

## Users
- [x] Administration Functions
- [x] Schema Completion
- [x] Registration
- [x] Invites
- [ ] User Stats model
- [ ] User Settings -- Define constant defaults and save user overrides of those defaults,
      creating a user property that caches the overrides and returns a dict of boolean/(0, 1, 2)
      user settings
- [ ] Email blacklist
- [ ] Invite Trees

## Permissions
- [x] Primary User Classes
- [x] Individual Permissions
- [x] Turn every endpoint into a permission?
- [x] Secondary User Classes

## Forums
- [x] Models
- [x] Category View
- [x] Forum View
- [x] Thread View
- [x] Posts View
- [ ] Forum/Thread Permissions
- [ ] Subscriptions
- [ ] Last viewed post in a thread | "viewed" boolean, clear on new post in thread
- [ ] Max post lengths on a per-user basis
- [ ] Can view deleted threads themselves if have special perm

## Rules
- [ ] Fuck it, we're going to make these dictionaries and serve them
- [ ] Built in git versioning

## Index
(All of these get their own endpoint too)
- [ ] News Posts
- [ ] Blog Posts
- [ ] Site Stats
- [ ] (delay) Featured Torrents (Leave Vanity House as RED fork implementation)

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
- [ ] Cache Key Clearing

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
