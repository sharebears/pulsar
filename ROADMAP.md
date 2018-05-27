# Current Path

- [x] Forums
- [x] Forum Glitter
- [x] Rules
- [ ] Review Documentation
-Version 0.0.2 Cutoff-
- [ ] News Posts
- [ ] Index

# Version 0.0.2 Milestone
- [x] Apply forum thread permissions to forum poll permissions
- [x] Forum thread notes
- [x] Post length exemption permission
- [x] CamelCase validator names
- [x] Rules System
- [ ] Get rid of the horrible idea that was ``pulsar.models``
- [ ] Hypothesis property testing for validators?
- [ ] Use a rollback for tests instead of manual table clears?
- [ ] Standardize permission and cache key names
- [ ] Split up schemas and models and create nested kwarg option serialization
- [ ] Documentation Revisions
- [ ] Users system extras



# TODO

## General
- [x] Form validation
- [x] Response wrapper
- [x] Model caching
- [ ] More inventive and free serialization - Define objects for serialization and have them
      use custom kwarg arguments which are passed down to all nested models? General function
      to process kwarg arguments and compare to defined serializations? Remove default
      ignores and adds in nested serialization and define those manually in each serialization.
- [ ] Docker/Vagrant environment
     

## Users
- [x] Administration Functions
- [x] Schema Completion
- [x] Registration
- [x] Invites
- [ ] User Stats model
- [ ] User Settings -- Define constant defaults and save user overrides of those defaults,
      creating a user property that caches the overrides and returns a dict of (0, 1, 2) user settings
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
- [ ] Populate basic ruleset

## Index
(All of these get their own endpoint too)
- [ ] News Posts
- [ ] Blog Posts
- [ ] Site Stats
- [ ] Featured Poll (make sure permissioned featured poll return null)

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
