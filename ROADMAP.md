# Current Path

- [ ] Handle forum permissions in class mixin - why are they separated?
- [ ] Users system extras
- [ ] News Posts
- [ ] Index


# TODO

## General
- [x] Form validation
- [x] Response wrapper
- [x] Model caching
- [ ] Docker/Vagrant environment

## Users
- [x] Administration Functions
- [x] Schema Completion
- [x] Registration
- [x] Invites
- [ ] User Stats model
- [ ] User Settings -- Define constant defaults and use MTM table
- [ ] Associate certain settings with certain permissions
- [ ] Email blacklist
- [ ] Invite Trees

## Authentication
- [x] Permissioned API Keys
- [x] Sessions

## Permissions
- [x] Primary User Classes
- [x] Individual Permissions
- [x] Endpoint permissoning
- [x] Secondary User Classes
- [x] Permissions usage checker dev tool
- [x] Forum Permissions
- [ ] Wiki Permissions

## Forums
- [x] Models
- [x] Category View
- [x] Forum View
- [x] Thread View
- [x] Posts View
- [x] Last viewed post in a thread
- [x] Thread Subscriptions
- [x] Forum Subscriptions (auto-subscribe to new threads in forum)
- [x] View (New) Subscriptions
- [x] Polls
- [x] Forum Poll Permissions
- [x] Forum Thread Notes
- [ ] Individual category view with 8 threads per sub-forum

## Rules
- [x] Cached JSON files.
- [ ] Default golden rules

## Index
(All of these get their own endpoint too)
- [ ] News Posts
- [ ] Blog Posts
- [ ] Site Stats
- [ ] Featured Poll (make sure a permissioned featured poll returns null and not 403)

## Wiki
- [ ] Wiki Pages
- [ ] /wiki returns page ID 1
- [ ] Permissions System - how to Elasticsearch permissions?
- [ ] Wiki Versioning (save history, let frontends do diffing)
- [ ] Wiki Log

## Site Log
- [ ] Site log table, insert-deletion function helpers
- [ ] Store some metadata fields - torrent ID, group ID, user ID use where applicable
- [ ] String for log type? Is that normalized?

## Staff Tools
- [ ] Basic Site-Level Administration Tools
- [ ] Separate Repository * .gitignored
- [ ] Cache Key Clearing

## Scheduler
- [ ] Schedule tasks with Celery
- [ ] schedule.py per-module
- [ ] Session expiry
- [ ] Invite expiry
- [ ] Inactivity disables

## Tors
- [ ] Global Base Torrent
- [ ] Global Base Group
- [ ] Global Base Uploader & Validation
- [ ] Global Base Torrent Editor
- [ ] Global Base Group Editor
- [ ] Get Group/Torrent
- [ ] Search Group/Torrent
- [ ] Delete

## Search
- [ ] Elasticsearch
- [ ] Search 1+ Categories Simultaneously
- [ ] Torrents, Collections, Requests, Forums, Wiki

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

## Collections - Collages / Bookmarks / Labels
Create a generic collections base similar to torrents --> categories
wet_torrents from a table with certain criteria
- [ ] View
- [ ] Create/Add/Edit/Delete
- [ ] Search

## Popular (Top 10)
- [ ] Generated via scheduler
- [ ] Preserve history
- [ ] Filtering

## RSS Feeds
- [ ] Later

## Donations
- [ ] Unique wallet generation a la Gazelle


# Post-MVP

## General
- [ ] Sentry

## Production Debugging Features
- [ ] Hook into existing libs?
- [ ] Query information in production?

## Index
- [ ] Featured Torrent Groups

## Type Checking
- [ ] Stub files for used interfaces of libraries?

## User Stats & History
- [ ] Community Stats
- [ ] Data Visualization

## Public Site Usage
- [ ] Create an anonymous user with default permissions, might as well implement
      into private so I can get rid of "not flask.g.user" and "flask.g.user is not None"
