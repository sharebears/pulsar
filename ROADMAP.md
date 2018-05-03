# CURRENT ROADMAP

- [x] Documentation outline via Sphinx
- [x] Document existing endpoints
- [x] Make Volup validators out of registration validators
- [-] User Classes, advanced permissioning
- [ ] User manipulation (enable/disable/lock)
- [ ] Rate Limiting
- [ ] Forums

## User Classes
- [ ] Staff `/tools` for manipulation

# TODO

## Caching - Help Wanted
- [ ] Maybe only cache the heavier queries? Will indices suffice?
- [ ] Redis/Celery
- [ ] Implement caching at the models level in `from_id` and `from_hash` methods.
      Have an override flag able to re-query those elements.
      Populate an object with `setattr()`, not sure how that works with
      object updates though
- [ ] Cache relationships separately? Cache relationships per parent PK and
      load/save those separately?
- [ ] Flask-Cache with memoization?

## General
- [x] Form validation with voluptuous
- [ ] Pagination abstraction

## Users
- [ ] Administration Functions
- [ ] Schema Completion
- [x] Registration
- [x] Invites

## Permissions
- [ ] User Classes (Pri & Sec)
- [x] Individual Permissions
- [x] Turn every endpoint into a permission?

## Forums
- [ ] Entire Forum View
- [ ] Category View
- [ ] Sub-Category View
- [ ] Individual Sub-Forum View
- [ ] Thread View (Pages)
- [ ] Individual Posts
- [ ] Posting

## Rules
- [ ] Golden Rules
- [ ] Rule Categories
- [ ] Rule Addition/Edit/Deletion
- [ ] Individual Rule
- [ ] Rule Versioning

## Index
- [ ] Basic user info, API version
- [ ] SiteStatus endpoint, yada yada
- [ ] Escaping?
- [ ] News Posts

## Wiki
- [ ] Wiki Pages
- [ ] ID 1 Default Landing Page
- [ ] Permissions System
- [ ] Wiki Versioning
- [ ] Wiki Log

## Site Log
- [ ] Table for log categories
- [ ] Site log table, insert-deletion function helpers

## Reports
- [ ] Reports Hub
- [ ] Take implementations of base model from forums/torrents/users with reportable = True

## Staff Tools
- [ ] Basic Tools
- [ ] Site Specific Submodule in .gitignore

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
- [ ] Later


# Post-MVP

## General
- [ ] Sentry

## User Stats & History
- [ ] Community Stats
- [ ] Data Visualization



