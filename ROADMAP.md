# Current Path

- [x] Rate Limiting
- [x] Caching
- [x] Permissioned Serialization
- [x] Boilerplate Refactors & Typing (Issues)
- [x] Forums
- [ ] Rules
- [ ] Forum Documentation
- [ ] Profile the PUT queries and solve if need be
- [ ] Thread permissions
- [ ] Thread subscriptions
- [ ] Thread last read post
- [ ] Polls
- [ ] News Posts
- [ ] Index

# Issues
- [x] Add serialization case for sets--turn into list, then use sets instead of deduping lists
- [x] Users can't view deleted threads even if they have the perm, can only view embedded in forum
- [x] Cache function properties
- [x] Figure out a way to jiggle mypy
- [x] Utilize redis get_many in ModelMixin.get_many and then query for all missing ones at once.
      Turn filling out empty lists into a two-step process instead of an overly large one.
- [ ] Refactor the mess that I made in get_many making it efficient
- [ ] Hypothesis property testing for the schemas and validators
- [ ] Fix PUT endpoints to be one change total, not one change per model (test SQLA profiling first)
- [ ] Built in debug logging?
 

# TODO

## General
- [x] Form validation with voluptuous
- [x] Permissioned Serialization
- [ ] Docker/Vagrant environment
- [ ] More inventive and free serialization - Define objects for serialization and have them
      use custom kwarg arguments which are passed down to all nested models?
      Mixins! The sauce of life!
     

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
- [ ] Documentation
- [ ] Forum/Thread Permissions
- [ ] Subscriptions
- [ ] Last viewed post in a thread | "viewed" boolean, clear on new post in thread
- [ ] Max post lengths on a per-user basis
- [ ] Polls

## Rules
- [ ] Dictionary files to be imported - enable reload of import without restarting site

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

## Type Checking
- [ ] Stub files for used interfaces of libraries?

## User Stats & History
- [ ] Community Stats
- [ ] Data Visualization
