# Current Path

- [x] Rate Limiting
- [x] Caching
- [x] Permissioned Serialization
- [-] Forums
- [ ] Rules
- [ ] News Posts
- [ ] Index

# TODO

## General
- [x] Form validation with voluptuous
- [x] Permissioned Serialization
- [ ] Write test that iterates over all models and validates
their dunder attributes

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
- [-] Models
- [ ] Category View
- [ ] Forum View
- [ ] Thread View
- [ ] Posts View

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
