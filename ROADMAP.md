# CURRENT ROADMAP

- [x] Documentation outline via Sphinx
- [x] Document existing endpoints
- [x] Make Volup validators out of registration validators
- [x] User Classes, advanced permissioning
- [x] User manipulation (enable/disable/lock)
- [x] Rate Limiting
- [ ] Forums

# TODO

## Caching - Help Wanted
- [x] Redis
- [ ] Maybe only cache the heavier queries? Will indices suffice?
- [ ] Implement caching at the models level in `from_id` and `from_hash` methods.
      Have an override flag able to re-query those elements.
      Populate an object with `setattr()`, not sure how that works with
      object updates though
- [ ] Cache relationships separately? Cache relationships per parent PK and
      load/save those separately?

## General
- [x] Form validation with voluptuous
- [ ] Pagination abstraction

## Users
- [x] Administration Functions
- [x] Schema Completion
- [x] Registration
- [x] Invites

## Permissions
- [x] Primary User Classes
- [x] Individual Permissions
- [x] Turn every endpoint into a permission?
- [x] Secondary User Classes

## Forums
- [ ] Entire Forum View
- [ ] Category View
- [ ] Sub-Category View
- [ ] Individual Sub-Forum View
- [ ] Thread View (Pages)
- [ ] Individual Posts
- [ ] Posting

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

# Post-MVP

## General
- [ ] Sentry

## User Stats & History
- [ ] Community Stats
- [ ] Data Visualization

## Donations
- [ ] Unique wallet generation a la Gazelle
