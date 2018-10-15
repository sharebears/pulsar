--postgresification of the old model for ERD viewing pleasure
--note that I removed index creation 
-- as it isn't going to help too much at this point to see what was indexed.

DROP DATABASE gazelle;

CREATE DATABASE gazelle encoding='UTF8';

CREATE TABLE IF NOT EXISTS "api_applications" (
  "ID" serial,
  "UserID" integer NOT NULL,
  "Token" char(32) NOT NULL,
  "Name" varchar(50) NOT NULL,
  PRIMARY KEY ("ID")
);

DROP TYPE IF EXISTS "state1" CASCADE;
CREATE TYPE "state1" AS enum('0','1','2');

CREATE TABLE IF NOT EXISTS "api_users" (
  "UserID" integer NOT NULL,
  "AppID" integer NOT NULL,
  "Token" char(32) NOT NULL,
  "State" state1 NOT NULL DEFAULT '0',
  "Time" timestamp NOT NULL,
  "Access" text,
  PRIMARY KEY ("UserID","AppID")
);

CREATE TABLE IF NOT EXISTS "artists_alias" (
  "AliasID" serial,
  "ArtistID" integer NOT NULL,
  "Name" varchar(200) DEFAULT NULL,
  "Redirect" integer NOT NULL DEFAULT '0',
  "UserID" bigint NOT NULL DEFAULT '0',
  PRIMARY KEY ("AliasID")
);

CREATE TABLE IF NOT EXISTS "artists_group" (
  "ArtistID" serial,
  "Name" varchar(200) DEFAULT NULL,
  "RevisionID" integer DEFAULT NULL,
  "VanityHouse" smallint DEFAULT '0',
  "LastCommentID" integer NOT NULL DEFAULT '0',
  PRIMARY KEY ("ArtistID")
);

CREATE TABLE IF NOT EXISTS "artists_similar" (
  "ArtistID" integer NOT NULL DEFAULT '0',
  "SimilarID" integer NOT NULL DEFAULT '0',
  PRIMARY KEY ("ArtistID","SimilarID")
);

CREATE TABLE IF NOT EXISTS "artists_similar_scores" (
  "SimilarID" serial,
  "Score" integer NOT NULL DEFAULT '0',
  PRIMARY KEY ("SimilarID")
);
DROP TYPE IF EXISTS "way" CASCADE;
CREATE TYPE "way" as enum('up','down');

CREATE TABLE IF NOT EXISTS "artists_similar_votes" (
  "SimilarID" integer NOT NULL,
  "UserID" integer NOT NULL,
  "Way" way NOT NULL DEFAULT 'up',
  PRIMARY KEY ("SimilarID","UserID","Way")
);

CREATE TABLE IF NOT EXISTS "artists_tags" (
  "TagID" integer NOT NULL DEFAULT '0',
  "ArtistID" integer NOT NULL DEFAULT '0',
  "PositiveVotes" integer NOT NULL DEFAULT '1',
  "NegativeVotes" integer NOT NULL DEFAULT '1',
  "UserID" integer DEFAULT NULL,
  PRIMARY KEY ("TagID","ArtistID")
);

CREATE TABLE IF NOT EXISTS "bad_passwords" (
  "Password" char(32) NOT NULL,
  PRIMARY KEY ("Password")
);

CREATE TABLE IF NOT EXISTS "blog" (
  "ID" serial,
  "UserID" bigint NOT NULL,
  "Title" varchar(255) NOT NULL,
  "Body" text NOT NULL,
  "Time" timestamp NOT NULL DEFAULT now(),
  "ThreadID" bigint DEFAULT NULL,
  "Important" smallint NOT NULL DEFAULT '0',
  PRIMARY KEY ("ID")
);


CREATE TABLE IF NOT EXISTS "bookmarks_artists" (
  "UserID" integer NOT NULL,
  "ArtistID" integer NOT NULL,
  "Time" timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS "bookmarks_collages" (
  "UserID" integer NOT NULL,
  "CollageID" integer NOT NULL,
  "Time" timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS "bookmarks_requests" (
  "UserID" integer NOT NULL,
  "RequestID" integer NOT NULL,
  "Time" timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS "bookmarks_torrents" (
  "UserID" integer NOT NULL,
  "GroupID" integer NOT NULL,
  "Time" timestamp NOT NULL,
  "Sort" integer NOT NULL DEFAULT '0',
  UNIQUE ("GroupID","UserID")
);

CREATE TABLE IF NOT EXISTS "calendar" (
  "ID" serial,
  "Title" varchar(255) DEFAULT NULL,
  "Body" text,
  "Category" smallint DEFAULT NULL,
  "StartDate" timestamp DEFAULT NULL,
  "EndDate" timestamp DEFAULT NULL,
  "AddedBy" integer DEFAULT NULL,
  "Importance" smallint DEFAULT NULL,
  "Team" smallint DEFAULT '1',
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "changelog" (
  "ID" serial,
  "Time" timestamp NOT NULL DEFAULT now(),
  "Message" text NOT NULL,
  "Author" varchar(30) NOT NULL,
  PRIMARY KEY ("ID")
);

DROP TYPE IF EXISTS "deleted" CASCADE;
CREATE TYPE "deleted" AS  enum('0','1');

DROP TYPE IF EXISTS "locked" CASCADE;
CREATE TYPE "locked" AS enum('0','1');

CREATE TABLE IF NOT EXISTS "collages" (
  "ID" serial,
  "Name" varchar(100) NOT NULL DEFAULT '',
  "Description" text NOT NULL,
  "UserID" integer NOT NULL DEFAULT '0',
  "NumTorrents" integer NOT NULL DEFAULT '0',
  "Deleted" deleted DEFAULT '0',
  "Locked" locked NOT NULL DEFAULT '0',
  "CategoryID" integer NOT NULL DEFAULT '1',
  "TagList" varchar(500) NOT NULL DEFAULT '',
  "MaxGroups" integer NOT NULL DEFAULT '0',
  "MaxGroupsPerUser" integer NOT NULL DEFAULT '0',
  "Featured" smallint NOT NULL DEFAULT '0',
  "Subscribers" integer DEFAULT '0',
  "updated" timestamp NOT NULL,
  PRIMARY KEY ("ID"),
  UNIQUE("Name")
);

CREATE TABLE IF NOT EXISTS "collages_artists" (
  "CollageID" integer NOT NULL,
  "ArtistID" integer NOT NULL,
  "UserID" integer NOT NULL,
  "Sort" integer NOT NULL DEFAULT '0',
  "AddedOn" timestamp NOT NULL DEFAULT now(),
  PRIMARY KEY ("CollageID","ArtistID")
);

CREATE TABLE IF NOT EXISTS "collages_torrents" (
  "CollageID" integer NOT NULL,
  "GroupID" integer NOT NULL,
  "UserID" integer NOT NULL,
  "Sort" integer NOT NULL DEFAULT '0',
  "AddedOn" timestamp NOT NULL DEFAULT now(),
  PRIMARY KEY ("CollageID","GroupID")
);

DROP TYPE IF EXISTS "page" CASCADE;
CREATE TYPE "page" AS enum('artist','collages','requests','torrents');

CREATE TABLE IF NOT EXISTS "comments" (
  "ID" serial,
  "Page" page NOT NULL,
  "PageID" integer NOT NULL,
  "AuthorID" integer NOT NULL,
  "AddedTime" timestamp NOT NULL DEFAULT now(),
  "Body" text,
  "EditedUserID" integer DEFAULT NULL,
  "EditedTime" timestamp DEFAULT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "comments_edits" (
  "Page" page DEFAULT NULL,
  "PostID" integer DEFAULT NULL,
  "EditUser" integer DEFAULT NULL,
  "EditTime" timestamp DEFAULT NULL,
  "Body" text
);

CREATE TABLE IF NOT EXISTS "comments_edits_tmp" (
  "Page" page DEFAULT NULL,
  "PostID" integer DEFAULT NULL,
  "EditUser" integer DEFAULT NULL,
  "EditTime" timestamp DEFAULT NULL,
  "Body" text
);

CREATE TABLE IF NOT EXISTS "concerts" (
  "ID" serial,
  "ConcertID" integer NOT NULL,
  "TopicID" integer NOT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "cover_art" (
  "ID" serial,
  "GroupID" integer NOT NULL,
  "Image" varchar(255) NOT NULL DEFAULT '',
  "Summary" varchar(100) DEFAULT NULL,
  "UserID" integer NOT NULL DEFAULT '0',
  "Time" timestamp DEFAULT NULL,
  PRIMARY KEY ("ID"),
  UNIQUE("GroupID","Image")
);

CREATE TABLE IF NOT EXISTS "currency_conversion_rates" (
  "Currency" char(3) NOT NULL,
  "Rate" decimal(9,4) DEFAULT NULL,
  "Time" timestamp DEFAULT NULL,
  PRIMARY KEY ("Currency")
);

CREATE TABLE IF NOT EXISTS "do_not_upload" (
  "ID" serial,
  "Name" varchar(255) NOT NULL,
  "Comment" varchar(255) NOT NULL,
  "UserID" integer NOT NULL,
  "Time" timestamp NOT NULL DEFAULT now(),
  "Sequence" integer NOT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "donations" (
  "UserID" integer NOT NULL,
  "Amount" decimal(6,2) NOT NULL,
  "Email" varchar(255) NOT NULL,
  "Time" timestamp NOT NULL,
  "Currency" varchar(5) NOT NULL DEFAULT 'USD',
  "Source" varchar(30) NOT NULL DEFAULT '',
  "Reason" text NOT NULL,
  "Rank" integer DEFAULT '0',
  "AddedBy" integer DEFAULT '0',
  "TotalRank" integer DEFAULT '0'
);

CREATE TABLE IF NOT EXISTS "donations_bitcoin" (
  "BitcoinAddress" varchar(34) NOT NULL,
  "Amount" decimal(24,8) NOT NULL
);

CREATE TABLE IF NOT EXISTS "donor_forum_usernames" (
  "UserID" integer NOT NULL DEFAULT '0',
  "Prefix" varchar(30) NOT NULL DEFAULT '',
  "Suffix" varchar(30) NOT NULL DEFAULT '',
  "UseComma" smallint DEFAULT '1',
  PRIMARY KEY ("UserID")
);

CREATE TABLE IF NOT EXISTS "donor_rewards" (
  "UserID" integer NOT NULL DEFAULT '0',
  "IconMouseOverText" varchar(200) NOT NULL DEFAULT '',
  "AvatarMouseOverText" varchar(200) NOT NULL DEFAULT '',
  "CustomIcon" varchar(200) NOT NULL DEFAULT '',
  "SecondAvatar" varchar(200) NOT NULL DEFAULT '',
  "CustomIconLink" varchar(200) NOT NULL DEFAULT '',
  "ProfileInfo1" text NOT NULL,
  "ProfileInfo2" text NOT NULL,
  "ProfileInfo3" text NOT NULL,
  "ProfileInfo4" text NOT NULL,
  "ProfileInfoTitle1" varchar(255) NOT NULL,
  "ProfileInfoTitle2" varchar(255) NOT NULL,
  "ProfileInfoTitle3" varchar(255) NOT NULL,
  "ProfileInfoTitle4" varchar(255) NOT NULL,
  PRIMARY KEY ("UserID")
);

CREATE TABLE IF NOT EXISTS "drives" (
  "DriveID" serial,
  "Name" varchar(50) NOT NULL,
  "Offset" varchar(10) NOT NULL,
  PRIMARY KEY ("DriveID")
);

CREATE TABLE IF NOT EXISTS "dupe_groups" (
  "ID" serial,
  "Comments" text,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "email_blacklist" (
  "ID" serial,
  "UserID" integer NOT NULL,
  "Email" varchar(255) NOT NULL,
  "Time" timestamp NOT NULL,
  "Comment" text NOT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "featured_albums" (
  "GroupID" integer NOT NULL DEFAULT '0',
  "ThreadID" integer NOT NULL DEFAULT '0',
  "Title" varchar(35) NOT NULL DEFAULT '',
  "Started" timestamp NOT NULL DEFAULT now(),
  "Ended" timestamp NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "featured_merch" (
  "ProductID" integer NOT NULL DEFAULT '0',
  "Title" varchar(35) NOT NULL DEFAULT '',
  "Image" varchar(255) NOT NULL DEFAULT '',
  "Started" timestamp NOT NULL DEFAULT now(),
  "Ended" timestamp NOT NULL DEFAULT now(),
  "ArtistID" bigint DEFAULT '0'
);


DROP TYPE IF EXISTS "autolock" CASCADE;
CREATE TYPE "autolock" AS enum('0','1');

CREATE TABLE IF NOT EXISTS "forums" (
  "ID" serial,
  "CategoryID" smallint NOT NULL DEFAULT '0',
  "Sort" bigint NOT NULL,
  "Name" varchar(40) NOT NULL DEFAULT '',
  "Description" varchar(255) DEFAULT '',
  "MinClassRead" integer NOT NULL DEFAULT '0',
  "MinClassWrite" integer NOT NULL DEFAULT '0',
  "MinClassCreate" integer NOT NULL DEFAULT '0',
  "NumTopics" integer NOT NULL DEFAULT '0',
  "NumPosts" integer NOT NULL DEFAULT '0',
  "LastPostID" integer NOT NULL DEFAULT '0',
  "LastPostAuthorID" integer NOT NULL DEFAULT '0',
  "LastPostTopicID" integer NOT NULL DEFAULT '0',
  "LastPostTime" timestamp NOT NULL DEFAULT now(),
  "AutoLock" autolock DEFAULT '1',
  "AutoLockWeeks" bigint NOT NULL DEFAULT '4',
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "forums_categories" (
  "ID" serial,
  "Name" varchar(40) NOT NULL DEFAULT '',
  "Sort" bigint NOT NULL DEFAULT '0',
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "forums_last_read_topics" (
  "UserID" integer NOT NULL,
  "TopicID" integer NOT NULL,
  "PostID" integer NOT NULL,
  PRIMARY KEY ("UserID","TopicID")
);

DROP TYPE IF EXISTS "closed" CASCADE;
CREATE TYPE "closed" AS enum('0','1');

CREATE TABLE IF NOT EXISTS "forums_polls" (
  "TopicID" bigint NOT NULL,
  "Question" varchar(255) NOT NULL,
  "Answers" text NOT NULL,
  "Featured" timestamp NOT NULL DEFAULT now(),
  "Closed" closed NOT NULL DEFAULT '0',
  PRIMARY KEY ("TopicID")
);

CREATE TABLE IF NOT EXISTS "forums_polls_votes" (
  "TopicID" bigint NOT NULL,
  "UserID" bigint NOT NULL,
  "Vote" integer NOT NULL,
  PRIMARY KEY ("TopicID","UserID")
);

CREATE TABLE IF NOT EXISTS "forums_posts" (
  "ID" serial,
  "TopicID" integer NOT NULL,
  "AuthorID" integer NOT NULL,
  "AddedTime" timestamp NOT NULL DEFAULT now(),
  "Body" text,
  "EditedUserID" integer DEFAULT NULL,
  "EditedTime" timestamp DEFAULT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "forums_specific_rules" (
  "ForumID" bigint DEFAULT NULL,
  "ThreadID" integer DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS "forums_topic_notes" (
  "ID" serial,
  "TopicID" integer NOT NULL,
  "AuthorID" integer NOT NULL,
  "AddedTime" timestamp NOT NULL,
  "Body" text,
  PRIMARY KEY ("ID")
);

DROP TYPE IF EXISTS "islocked" CASCADE;
CREATE TYPE "islocked" AS enum('0','1');

DROP TYPE IF EXISTS "issticky" CASCADE;
CREATE TYPE "issticky" AS enum('0','1');

CREATE TABLE IF NOT EXISTS "forums_topics" (
  "ID" serial,
  "Title" varchar(150) NOT NULL,
  "AuthorID" integer NOT NULL,
  "IsLocked" islocked NOT NULL DEFAULT '0',
  "IsSticky" issticky NOT NULL DEFAULT '0',
  "ForumID" integer NOT NULL,
  "NumPosts" integer NOT NULL DEFAULT '0',
  "LastPostID" integer NOT NULL,
  "LastPostTime" timestamp NOT NULL DEFAULT now(),
  "LastPostAuthorID" integer NOT NULL,
  "StickyPostID" integer NOT NULL DEFAULT '0',
  "Ranking" smallint DEFAULT '0',
  "CreatedTime" timestamp NOT NULL DEFAULT now(),
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "friends" (
  "UserID" bigint NOT NULL,
  "FriendID" bigint NOT NULL,
  "Comment" text NOT NULL,
  PRIMARY KEY ("UserID","FriendID")
);

CREATE TABLE IF NOT EXISTS "geoip_country" (
  "StartIP" bigint NOT NULL,
  "EndIP" bigint NOT NULL,
  "Code" varchar(2) NOT NULL,
  PRIMARY KEY ("StartIP","EndIP")
);

CREATE TABLE IF NOT EXISTS "group_log" (
  "ID" serial,
  "GroupID" integer NOT NULL,
  "TorrentID" integer NOT NULL,
  "UserID" integer NOT NULL DEFAULT '0',
  "Info" text,
  "Time" timestamp NOT NULL DEFAULT now(),
  "Hidden" smallint NOT NULL DEFAULT '0',
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "invite_tree" (
  "UserID" integer NOT NULL DEFAULT '0',
  "InviterID" integer NOT NULL DEFAULT '0',
  "TreePosition" integer NOT NULL DEFAULT '1',
  "TreeID" integer NOT NULL DEFAULT '1',
  "TreeLevel" integer NOT NULL DEFAULT '0',
  PRIMARY KEY ("UserID")
);

CREATE TABLE IF NOT EXISTS "invites" (
  "InviterID" integer NOT NULL DEFAULT '0',
  "InviteKey" char(32) NOT NULL,
  "Email" varchar(255) NOT NULL,
  "Expires" timestamp NOT NULL DEFAULT now(),
  "Reason" varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY ("InviteKey")
);

CREATE TABLE IF NOT EXISTS "ip_bans" (
  "ID" serial,
  "FromIP" bigint NOT NULL,
  "ToIP" bigint NOT NULL,
  "Reason" varchar(255) DEFAULT NULL,
  PRIMARY KEY ("ID"),
  UNIQUE("FromIP","ToIP")
);

CREATE TABLE IF NOT EXISTS "label_aliases" (
  "ID" serial,
  "BadLabel" varchar(100) NOT NULL,
  "AliasLabel" varchar(100) NOT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "last_sent_email" (
  "UserID" integer NOT NULL,
  PRIMARY KEY ("UserID")
);

CREATE TABLE IF NOT EXISTS "lastfm_users" (
  "ID" bigint NOT NULL,
  "Username" varchar(20) NOT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "library_contest" (
  "UserID" integer NOT NULL,
  "TorrentID" integer NOT NULL,
  "Points" integer NOT NULL DEFAULT '0',
  PRIMARY KEY ("UserID","TorrentID")
);

DROP TYPE IF EXISTS "enabled" CASCADE;
CREATE TYPE "enabled" AS enum('0','1', '2');

DROP TYPE IF EXISTS "visible" CASCADE;
CREATE TYPE "visible" AS enum('1', '0');

CREATE TABLE IF NOT EXISTS "users_main" (
  "ID" serial,
  "Username" varchar(20) NOT NULL,
  "Email" varchar(255) NOT NULL,
  "PassHash" varchar(60) NOT NULL,
  "Secret" char(32) NOT NULL,
  "IRCKey" char(32) DEFAULT NULL,
  "LastLogin" timestamp NOT NULL DEFAULT now(),
  "LastAccess" timestamp NOT NULL DEFAULT now(),
  "IP" varchar(15) NOT NULL DEFAULT '0.0.0.0',
  "Class" smallint NOT NULL DEFAULT '5',
  "Uploaded" numeric(20) NOT NULL DEFAULT '0',
  "Downloaded" numeric(20) NOT NULL DEFAULT '0',
  "Title" text NOT NULL,
  "Enabled" enabled NOT NULL DEFAULT '0',
  "Paranoia" text,
  "Visible" visible NOT NULL DEFAULT '1',
  "Invites" bigint NOT NULL DEFAULT '0',
  "PermissionID" bigint NOT NULL,
  "CustomPermissions" text,
  "can_leech" smallint NOT NULL DEFAULT '1',
  "torrent_pass" char(32) NOT NULL,
  "RequiredRatio" numeric(10,8) NOT NULL DEFAULT '0.00000000',
  "RequiredRatioWork" numeric(10,8) NOT NULL DEFAULT '0.00000000',
  "ipcc" varchar(2) NOT NULL DEFAULT '',
  "FLTokens" integer NOT NULL DEFAULT '0',
  PRIMARY KEY ("ID"),
  UNIQUE("Username")
);


CREATE TABLE IF NOT EXISTS "locked_accounts" (
  "UserID" bigint NOT NULL,
  "Type" smallint NOT NULL,
  PRIMARY KEY ("UserID"),
  CONSTRAINT "fk_user_id" FOREIGN KEY ("UserID") REFERENCES "users_main" ("ID") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "log" (
  "ID" serial,
  "Message" varchar(400) NOT NULL,
  "Time" timestamp NOT NULL DEFAULT now(),
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "login_attempts" (
  "ID" serial,
  "UserID" bigint NOT NULL,
  "IP" varchar(15) NOT NULL,
  "LastAttempt" timestamp NOT NULL DEFAULT now(),
  "Attempts" bigint NOT NULL,
  "BannedUntil" timestamp NOT NULL DEFAULT now(),
  "Bans" bigint NOT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "new_info_hashes" (
  "TorrentID" integer NOT NULL,
  "InfoHash" bytea DEFAULT NULL,
  PRIMARY KEY ("TorrentID")
);

CREATE TABLE IF NOT EXISTS "news" (
  "ID" serial,
  "UserID" bigint NOT NULL,
  "Title" varchar(255) NOT NULL,
  "Body" text NOT NULL,
  "Time" timestamp NOT NULL DEFAULT now(),
  PRIMARY KEY ("ID")
);


DROP TYPE IF EXISTS "buffer" CASCADE;
CREATE TYPE "buffer" AS enum('users','torrents','snatches','peers');

CREATE TABLE IF NOT EXISTS "ocelot_query_times" (
  "buffer" buffer NOT NULL,
  "starttime" timestamp NOT NULL,
  "ocelotinstance" timestamp NOT NULL,
  "querylength" integer NOT NULL,
  "timespent" integer NOT NULL,
  UNIQUE("starttime")
);

DROP TYPE IF EXISTS "displaystaff" CASCADE;
CREATE TYPE "displaystaff" AS enum('0','1');

CREATE TABLE IF NOT EXISTS "permissions" (
  "ID" serial,
  "Level" bigint NOT NULL,
  "Name" varchar(25) NOT NULL,
  "Values" text NOT NULL,
  "DisplayStaff" displaystaff NOT NULL DEFAULT '0',
  "PermittedForums" varchar(150) NOT NULL DEFAULT '',
  "Secondary" smallint NOT NULL DEFAULT '0',
  PRIMARY KEY ("ID"),
  UNIQUE("Level")
);

CREATE TABLE IF NOT EXISTS "pm_conversations" (
  "ID" serial,
  "Subject" varchar(255) DEFAULT NULL,
  PRIMARY KEY ("ID")
);

DROP TYPE IF EXISTS "ininbox" CASCADE;
CREATE TYPE "ininbox" AS enum('0','1');

DROP TYPE IF EXISTS "insentbox" CASCADE;
CREATE TYPE "insentbox" AS enum('0','1');

DROP TYPE IF EXISTS "unread" CASCADE;
CREATE TYPE "unread" AS enum('0','1');

DROP TYPE IF EXISTS "sticky" CASCADE;
CREATE TYPE "sticky" AS enum('0','1');

CREATE TABLE IF NOT EXISTS "pm_conversations_users" (
  "UserID" integer NOT NULL DEFAULT '0',
  "ConvID" integer NOT NULL DEFAULT '0',
  "InInbox" ininbox NOT NULL,
  "InSentbox" insentbox NOT NULL,
  "SentDate" timestamp NOT NULL DEFAULT now(),
  "ReceivedDate" timestamp NOT NULL DEFAULT now(),
  "UnRead" unread NOT NULL DEFAULT '1',
  "Sticky" sticky NOT NULL DEFAULT '0',
  "ForwardedTo" integer NOT NULL DEFAULT '0',
  PRIMARY KEY ("UserID","ConvID")
);

CREATE TABLE IF NOT EXISTS "pm_messages" (
  "ID" serial,
  "ConvID" integer NOT NULL DEFAULT '0',
  "SentDate" timestamp NOT NULL DEFAULT now(),
  "SenderID" integer NOT NULL DEFAULT '0',
  "Body" text,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "push_notifications_usage" (
  "PushService" varchar(10) NOT NULL,
  "TimesUsed" integer NOT NULL DEFAULT '0',
  PRIMARY KEY ("PushService")
);

DROP TYPE IF EXISTS "status" CASCADE;
CREATE TYPE "status" AS enum('New','InProgress','Resolved');

CREATE TABLE IF NOT EXISTS "reports" (
  "ID" serial,
  "UserID" bigint NOT NULL DEFAULT '0',
  "ThingID" bigint NOT NULL DEFAULT '0',
  "Type" varchar(30) DEFAULT NULL,
  "Comment" text,
  "ResolverID" bigint NOT NULL DEFAULT '0',
  "Status" status DEFAULT 'New',
  "ResolvedTime" timestamp NOT NULL DEFAULT now(),
  "ReportedTime" timestamp NOT NULL DEFAULT now(),
  "Reason" text NOT NULL,
  "ClaimerID" bigint NOT NULL DEFAULT '0',
  "Notes" text NOT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "reports_email_blacklist" (
  "ID" serial,
  "Type" smallint NOT NULL DEFAULT '0',
  "UserID" integer NOT NULL,
  "Time" timestamp NOT NULL DEFAULT now(),
  "Checked" smallint NOT NULL DEFAULT '0',
  "ResolverID" integer DEFAULT '0',
  "Email" varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "reportsv2" (
  "ID" serial,
  "ReporterID" bigint NOT NULL DEFAULT '0',
  "TorrentID" bigint NOT NULL DEFAULT '0',
  "Type" varchar(20) DEFAULT '',
  "UserComment" text,
  "ResolverID" bigint NOT NULL DEFAULT '0',
  "Status" status DEFAULT 'New',
  "ReportedTime" timestamp NOT NULL DEFAULT now(),
  "LastChangeTime" timestamp NOT NULL DEFAULT now(),
  "ModComment" text,
  "Track" text,
  "Image" text,
  "ExtraID" text,
  "Link" text,
  "LogMessage" text,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "requests" (
  "ID" serial,
  "UserID" bigint NOT NULL DEFAULT '0',
  "TimeAdded" timestamp NOT NULL,
  "LastVote" timestamp DEFAULT NULL,
  "CategoryID" integer NOT NULL,
  "Title" varchar(255) DEFAULT NULL,
  "Year" integer DEFAULT NULL,
  "Image" varchar(255) DEFAULT NULL,
  "Description" text NOT NULL,
  "ReleaseType" smallint DEFAULT NULL,
  "CatalogueNumber" varchar(50) NOT NULL,
  "BitrateList" varchar(255) DEFAULT NULL,
  "FormatList" varchar(255) DEFAULT NULL,
  "MediaList" varchar(255) DEFAULT NULL,
  "LogCue" varchar(20) DEFAULT NULL,
  "FillerID" bigint NOT NULL DEFAULT '0',
  "TorrentID" bigint NOT NULL DEFAULT '0',
  "TimeFilled" timestamp NOT NULL DEFAULT now(),
  "Visible" bytea NOT NULL DEFAULT '1',
  "RecordLabel" varchar(80) DEFAULT NULL,
  "GroupID" integer DEFAULT NULL,
  "OCLC" varchar(55) NOT NULL DEFAULT '',
  PRIMARY KEY ("ID")
);

DROP TYPE IF EXISTS "importance" CASCADE;
CREATE TYPE "importance" AS enum('1','2','3','4','5','6','7');

CREATE TABLE IF NOT EXISTS "requests_artists" (
  "RequestID" bigint NOT NULL,
  "ArtistID" integer NOT NULL,
  "AliasID" integer NOT NULL,
  "Importance" importance DEFAULT NULL,
  PRIMARY KEY ("RequestID","AliasID")
);

CREATE TABLE IF NOT EXISTS "requests_tags" (
  "TagID" integer NOT NULL DEFAULT '0',
  "RequestID" integer NOT NULL DEFAULT '0',
  PRIMARY KEY ("TagID","RequestID")
);

CREATE TABLE IF NOT EXISTS "requests_votes" (
  "RequestID" integer NOT NULL DEFAULT '0',
  "UserID" integer NOT NULL DEFAULT '0',
  "Bounty" numeric(20) NOT NULL,
  PRIMARY KEY ("RequestID","UserID")
);

CREATE TABLE IF NOT EXISTS "schedule" (
  "NextHour" integer NOT NULL DEFAULT '0',
  "NextDay" integer NOT NULL DEFAULT '0',
  "NextBiWeekly" integer NOT NULL DEFAULT '0'
);

CREATE TABLE IF NOT EXISTS "site_history" (
  "ID" serial,
  "Title" varchar(255) DEFAULT NULL,
  "Url" varchar(255) NOT NULL DEFAULT '',
  "Category" smallint DEFAULT NULL,
  "SubCategory" smallint DEFAULT NULL,
  "Tags" text,
  "AddedBy" integer DEFAULT NULL,
  "Date" timestamp DEFAULT NULL,
  "Body" text,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "site_options" (
  "ID" serial,
  "Name" varchar(64) NOT NULL,
  "Value" text NOT NULL,
  "Comment" text NOT NULL,
  PRIMARY KEY ("ID"),
  UNIQUE("Name")
);

CREATE TABLE IF NOT EXISTS "sphinx_a" (
  "gid" integer DEFAULT NULL,
  "aname" text
);

CREATE TABLE IF NOT EXISTS "sphinx_delta" (
  "ID" integer NOT NULL,
  "GroupID" integer NOT NULL DEFAULT '0',
  "GroupName" varchar(255) DEFAULT NULL,
  "ArtistName" varchar(2048) DEFAULT NULL,
  "TagList" varchar(728) DEFAULT NULL,
  "Year" integer DEFAULT NULL,
  "CatalogueNumber" varchar(50) DEFAULT NULL,
  "RecordLabel" varchar(50) DEFAULT NULL,
  "CategoryID" smallint DEFAULT NULL,
  "Time" integer DEFAULT NULL,
  "ReleaseType" smallint DEFAULT NULL,
  "Size" bigint DEFAULT NULL,
  "Snatched" integer DEFAULT NULL,
  "Seeders" integer DEFAULT NULL,
  "Leechers" integer DEFAULT NULL,
  "LogScore" integer DEFAULT NULL,
  "Scene" smallint NOT NULL DEFAULT '0',
  "VanityHouse" smallint NOT NULL DEFAULT '0',
  "HasLog" smallint DEFAULT NULL,
  "HasCue" smallint DEFAULT NULL,
  "FreeTorrent" smallint DEFAULT NULL,
  "Media" varchar(255) DEFAULT NULL,
  "Format" varchar(255) DEFAULT NULL,
  "Encoding" varchar(255) DEFAULT NULL,
  "RemasterYear" varchar(50) NOT NULL DEFAULT '',
  "RemasterTitle" varchar(512) DEFAULT NULL,
  "RemasterRecordLabel" varchar(50) DEFAULT NULL,
  "RemasterCatalogueNumber" varchar(50) DEFAULT NULL,
  "FileList" text,
  "Description" text,
  "VoteScore" float NOT NULL DEFAULT '0',
  "LastChanged" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY ("ID")
); 

CREATE TABLE IF NOT EXISTS "sphinx_hash" (
  "ID" integer NOT NULL,
  "GroupName" varchar(255) DEFAULT NULL,
  "ArtistName" varchar(2048) DEFAULT NULL,
  "TagList" varchar(728) DEFAULT NULL,
  "Year" integer DEFAULT NULL,
  "CatalogueNumber" varchar(50) DEFAULT NULL,
  "RecordLabel" varchar(50) DEFAULT NULL,
  "CategoryID" smallint DEFAULT NULL,
  "Time" integer DEFAULT NULL,
  "ReleaseType" smallint DEFAULT NULL,
  "Size" bigint DEFAULT NULL,
  "Snatched" integer DEFAULT NULL,
  "Seeders" integer DEFAULT NULL,
  "Leechers" integer DEFAULT NULL,
  "LogScore" integer DEFAULT NULL,
  "Scene" smallint NOT NULL DEFAULT '0',
  "VanityHouse" smallint NOT NULL DEFAULT '0',
  "HasLog" smallint DEFAULT NULL,
  "HasCue" smallint DEFAULT NULL,
  "FreeTorrent" smallint DEFAULT NULL,
  "Media" varchar(255) DEFAULT NULL,
  "Format" varchar(255) DEFAULT NULL,
  "Encoding" varchar(255) DEFAULT NULL,
  "RemasterYear" integer DEFAULT NULL,
  "RemasterTitle" varchar(512) DEFAULT NULL,
  "RemasterRecordLabel" varchar(50) DEFAULT NULL,
  "RemasterCatalogueNumber" varchar(50) DEFAULT NULL,
  "FileList" text,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "sphinx_index_last_pos" (
  "Type" varchar(16) NOT NULL DEFAULT '',
  "ID" integer DEFAULT NULL,
  PRIMARY KEY ("Type")
);

CREATE TABLE IF NOT EXISTS "sphinx_requests" (
  "ID" bigint NOT NULL,
  "UserID" bigint NOT NULL DEFAULT '0',
  "TimeAdded" bigint NOT NULL,
  "LastVote" bigint NOT NULL,
  "CategoryID" integer NOT NULL,
  "Title" varchar(255) DEFAULT NULL,
  "Year" integer DEFAULT NULL,
  "ArtistList" varchar(2048) DEFAULT NULL,
  "ReleaseType" smallint DEFAULT NULL,
  "CatalogueNumber" varchar(50) NOT NULL,
  "BitrateList" varchar(255) DEFAULT NULL,
  "FormatList" varchar(255) DEFAULT NULL,
  "MediaList" varchar(255) DEFAULT NULL,
  "LogCue" varchar(20) DEFAULT NULL,
  "FillerID" bigint NOT NULL DEFAULT '0',
  "TorrentID" bigint NOT NULL DEFAULT '0',
  "TimeFilled" bigint NOT NULL,
  "Visible" bytea NOT NULL DEFAULT '1',
  "Bounty" numeric(20) NOT NULL DEFAULT '0',
  "Votes" bigint NOT NULL DEFAULT '0',
  "RecordLabel" varchar(80) DEFAULT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "sphinx_requests_delta" (
  "ID" bigint NOT NULL,
  "UserID" bigint NOT NULL DEFAULT '0',
  "TimeAdded" bigint DEFAULT NULL,
  "LastVote" bigint DEFAULT NULL,
  "CategoryID" smallint DEFAULT NULL,
  "Title" varchar(255) DEFAULT NULL,
  "TagList" varchar(728) NOT NULL DEFAULT '',
  "Year" integer DEFAULT NULL,
  "ArtistList" varchar(2048) DEFAULT NULL,
  "ReleaseType" smallint DEFAULT NULL,
  "CatalogueNumber" varchar(50) DEFAULT NULL,
  "BitrateList" varchar(255) DEFAULT NULL,
  "FormatList" varchar(255) DEFAULT NULL,
  "MediaList" varchar(255) DEFAULT NULL,
  "LogCue" varchar(20) DEFAULT NULL,
  "FillerID" bigint NOT NULL DEFAULT '0',
  "TorrentID" bigint NOT NULL DEFAULT '0',
  "TimeFilled" bigint DEFAULT NULL,
  "Visible" bytea NOT NULL DEFAULT '1',
  "Bounty" numeric(20) NOT NULL DEFAULT '0',
  "Votes" bigint NOT NULL DEFAULT '0',
  "RecordLabel" varchar(80) DEFAULT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "sphinx_t" (
  "id" integer NOT NULL,
  "gid" integer NOT NULL,
  "uid" integer NOT NULL,
  "size" bigint NOT NULL,
  "snatched" integer NOT NULL,
  "seeders" integer NOT NULL,
  "leechers" integer NOT NULL,
  "time" integer NOT NULL,
  "logscore" smallint NOT NULL,
  "scene" smallint NOT NULL,
  "haslog" smallint NOT NULL,
  "hascue" smallint NOT NULL,
  "freetorrent" smallint NOT NULL,
  "media" varchar(15) NOT NULL,
  "format" varchar(15) NOT NULL,
  "encoding" varchar(30) NOT NULL,
  "remyear" smallint NOT NULL,
  "remtitle" varchar(80) NOT NULL,
  "remrlabel" varchar(80) NOT NULL,
  "remcnumber" varchar(80) NOT NULL,
  "filelist" text,
  "remident" bigint NOT NULL,
  "description" text,
  PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "sphinx_tg" (
  "id" integer NOT NULL,
  "name" varchar(300) DEFAULT NULL,
  "tags" varchar(500) DEFAULT NULL,
  "year" smallint DEFAULT NULL,
  "rlabel" varchar(80) DEFAULT NULL,
  "cnumber" varchar(80) DEFAULT NULL,
  "catid" smallint DEFAULT NULL,
  "reltype" smallint DEFAULT NULL,
  "vanityhouse" smallint DEFAULT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "staff_answers" (
  "QuestionID" integer NOT NULL,
  "UserID" integer NOT NULL,
  "Answer" text,
  "Date" timestamp NOT NULL,
  PRIMARY KEY ("QuestionID","UserID")
);

CREATE TABLE IF NOT EXISTS "staff_blog" (
  "ID" serial,
  "UserID" bigint NOT NULL,
  "Title" varchar(255) NOT NULL,
  "Body" text NOT NULL,
  "Time" timestamp NOT NULL DEFAULT now(),
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "staff_blog_visits" (
  "UserID" bigint NOT NULL,
  "Time" timestamp NOT NULL DEFAULT now(),
  UNIQUE("UserID"),
  CONSTRAINT "staff_blog_visits_ibfk_1" FOREIGN KEY ("UserID") REFERENCES "users_main" ("ID") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "staff_ignored_questions" (
  "QuestionID" integer NOT NULL,
  "UserID" integer NOT NULL,
  PRIMARY KEY ("QuestionID","UserID")
);

DROP TYPE IF EXISTS "staffpmstatus" CASCADE;
CREATE TYPE "staffpmstatus" AS enum('Open','Unanswered','Resolved');

CREATE TABLE IF NOT EXISTS "staff_pm_conversations" (
  "ID" serial,
  "Subject" text,
  "UserID" integer DEFAULT NULL,
  "Status" staffpmstatus DEFAULT NULL,
  "Level" integer DEFAULT NULL,
  "AssignedToUser" integer DEFAULT NULL,
  "Date" timestamp DEFAULT NULL,
  "Unread" smallint DEFAULT NULL,
  "ResolverID" integer DEFAULT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "staff_pm_messages" (
  "ID" serial,
  "UserID" integer DEFAULT NULL,
  "SentDate" timestamp DEFAULT NULL,
  "Message" text,
  "ConvID" integer DEFAULT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "staff_pm_responses" (
  "ID" serial,
  "Message" text,
  "Name" text,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "styles_backup" (
  "UserID" integer NOT NULL DEFAULT '0',
  "StyleID" integer DEFAULT NULL,
  "StyleURL" varchar(255) DEFAULT NULL,
  PRIMARY KEY ("UserID")
);
DROP TYPE IF EXISTS "defaultstylesheet" CASCADE;
CREATE TYPE "defaultstylesheet" AS enum('0', '1');

CREATE TABLE IF NOT EXISTS "stylesheets" (
  "ID" serial,
  "Name" varchar(255) NOT NULL,
  "Description" varchar(255) NOT NULL,
  "Default" defaultstylesheet NOT NULL DEFAULT '0',
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "tag_aliases" (
  "ID" serial,
  "BadTag" varchar(30) DEFAULT NULL,
  "AliasTag" varchar(30) DEFAULT NULL,
  PRIMARY KEY ("ID")
);

DROP TYPE IF EXISTS "tagtype" CASCADE;
CREATE TYPE "tagtype" AS enum('genre','other');

CREATE TABLE IF NOT EXISTS "tags" (
  "ID" serial,
  "Name" varchar(100) DEFAULT NULL,
  "TagType" tagtype NOT NULL DEFAULT 'other',
  "Uses" integer NOT NULL DEFAULT '1',
  "UserID" integer DEFAULT NULL,
  PRIMARY KEY ("ID"),
  UNIQUE("Name")
);

DROP TYPE IF EXISTS "top10type" CASCADE;
CREATE TYPE "top10type" AS enum('Daily','Weekly');

CREATE TABLE IF NOT EXISTS "top10_history" (
  "ID" serial,
  "Date" timestamp NOT NULL DEFAULT now(),
  "Type" top10type DEFAULT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "top10_history_torrents" (
  "HistoryID" integer NOT NULL DEFAULT '0',
  "Rank" smallint NOT NULL DEFAULT '0',
  "TorrentID" integer NOT NULL DEFAULT '0',
  "TitleString" varchar(150) NOT NULL DEFAULT '',
  "TagString" varchar(100) NOT NULL DEFAULT ''
);

DROP TYPE IF EXISTS "remastered" CASCADE;
CREATE TYPE "remastered" AS enum('0','1');

DROP TYPE IF EXISTS "scene" CASCADE;
CREATE TYPE "scene" AS enum('0','1');

DROP TYPE IF EXISTS "haslog" CASCADE;
CREATE TYPE "haslog" AS enum('0','1');

DROP TYPE IF EXISTS "hascue" CASCADE;
CREATE TYPE "hascue" AS enum('0','1');

DROP TYPE IF EXISTS "freetorrent" CASCADE;
CREATE TYPE "freetorrent" AS enum('0','1','2');

DROP TYPE IF EXISTS "freeleechtype" CASCADE;
CREATE TYPE "freeleechtype" AS enum('0','1','2','3','4','5','6','7');

CREATE TABLE IF NOT EXISTS "torrents" (
  "ID" serial,
  "GroupID" integer NOT NULL,
  "UserID" integer DEFAULT NULL,
  "Media" varchar(20) DEFAULT NULL,
  "Format" varchar(10) DEFAULT NULL,
  "Encoding" varchar(15) DEFAULT NULL,
  "Remastered" remastered NOT NULL DEFAULT '0',
  "RemasterYear" integer DEFAULT NULL,
  "RemasterTitle" varchar(80) NOT NULL DEFAULT '',
  "RemasterCatalogueNumber" varchar(80) NOT NULL DEFAULT '',
  "RemasterRecordLabel" varchar(80) NOT NULL DEFAULT '',
  "Scene" scene NOT NULL DEFAULT '0',
  "HasLog" haslog NOT NULL DEFAULT '0',
  "HasCue" hascue NOT NULL DEFAULT '0',
  "LogScore" integer NOT NULL DEFAULT '0',
  "info_hash" bytea NOT NULL,
  "FileCount" integer NOT NULL,
  "FileList" text NOT NULL,
  "FilePath" varchar(255) NOT NULL DEFAULT '',
  "Size" bigint NOT NULL,
  "Leechers" integer NOT NULL DEFAULT '0',
  "Seeders" integer NOT NULL DEFAULT '0',
  "last_action" timestamp NOT NULL DEFAULT now(),
  "FreeTorrent" freetorrent NOT NULL DEFAULT '0',
  "FreeLeechType" freeleechtype NOT NULL DEFAULT '0',
  "Time" timestamp NOT NULL DEFAULT now(),
  "Description" text,
  "Snatched" bigint NOT NULL DEFAULT '0',
  "balance" bigint NOT NULL DEFAULT '0',
  "LastReseedRequest" timestamp NOT NULL DEFAULT now(),
  "TranscodedFrom" integer NOT NULL DEFAULT '0',
  PRIMARY KEY ("ID"),
  UNIQUE("info_hash")
);

CREATE TABLE IF NOT EXISTS "torrents_artists" (
  "GroupID" integer NOT NULL,
  "ArtistID" integer NOT NULL,
  "AliasID" integer NOT NULL,
  "UserID" bigint NOT NULL DEFAULT '0',
  "Importance" importance NOT NULL DEFAULT '1',
  PRIMARY KEY ("GroupID","ArtistID","Importance")
);

CREATE TABLE IF NOT EXISTS "torrents_bad_files" (
  "TorrentID" integer NOT NULL DEFAULT '0',
  "UserID" integer NOT NULL DEFAULT '0',
  "TimeAdded" timestamp NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "torrents_bad_folders" (
  "TorrentID" integer NOT NULL,
  "UserID" integer NOT NULL,
  "TimeAdded" timestamp NOT NULL,
  PRIMARY KEY ("TorrentID")
);

CREATE TABLE IF NOT EXISTS "torrents_bad_tags" (
  "TorrentID" integer NOT NULL DEFAULT '0',
  "UserID" integer NOT NULL DEFAULT '0',
  "TimeAdded" timestamp NOT NULL DEFAULT now()
);

DROP TYPE IF EXISTS "last_balance" CASCADE;
CREATE TYPE "last_balance" as enum('0','1','2');

CREATE TABLE IF NOT EXISTS "torrents_balance_history" (
  "TorrentID" integer NOT NULL,
  "GroupID" integer NOT NULL,
  "balance" bigint NOT NULL,
  "Time" timestamp NOT NULL,
  "Last" last_balance DEFAULT '0',
  UNIQUE("TorrentID","Time"),
  UNIQUE("TorrentID","balance")
);

CREATE TABLE IF NOT EXISTS "torrents_cassette_approved" (
  "TorrentID" integer NOT NULL DEFAULT '0',
  "UserID" integer NOT NULL DEFAULT '0',
  "TimeAdded" timestamp NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "torrents_files" (
  "TorrentID" integer NOT NULL,
  "File" bytea NOT NULL,
  PRIMARY KEY ("TorrentID")
);

CREATE TABLE IF NOT EXISTS "torrents_group" (
  "ID" serial,
  "ArtistID" integer DEFAULT NULL,
  "CategoryID" integer DEFAULT NULL,
  "Name" varchar(300) DEFAULT NULL,
  "Year" integer DEFAULT NULL,
  "CatalogueNumber" varchar(80) NOT NULL DEFAULT '',
  "RecordLabel" varchar(80) NOT NULL DEFAULT '',
  "ReleaseType" smallint DEFAULT '21',
  "TagList" varchar(500) NOT NULL,
  "Time" timestamp NOT NULL DEFAULT now(),
  "RevisionID" integer DEFAULT NULL,
  "WikiBody" text NOT NULL,
  "WikiImage" varchar(255) NOT NULL,
  "VanityHouse" smallint DEFAULT '0',
  PRIMARY KEY ("ID")
);

DROP TYPE IF EXISTS "adjusted" CASCADE;
CREATE TYPE "adjusted" as enum('1', '0');

DROP TYPE IF EXISTS "notenglish" CASCADE;
CREATE TYPE "notenglish" as enum('1', '0');

CREATE TABLE IF NOT EXISTS "torrents_logs_new" (
  "LogID" serial,
  "TorrentID" integer NOT NULL DEFAULT '0',
  "Log" text NOT NULL,
  "Details" text NOT NULL,
  "Score" integer NOT NULL,
  "Revision" integer NOT NULL,
  "Adjusted" adjusted NOT NULL DEFAULT '0',
  "AdjustedBy" integer NOT NULL DEFAULT '0',
  "NotEnglish" notenglish NOT NULL DEFAULT '0',
  "AdjustmentReason" text,
  PRIMARY KEY ("LogID")
);



CREATE TABLE IF NOT EXISTS "torrents_lossymaster_approved" (
  "TorrentID" integer NOT NULL DEFAULT '0',
  "UserID" integer NOT NULL DEFAULT '0',
  "TimeAdded" timestamp NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "torrents_lossyweb_approved" (
  "TorrentID" integer NOT NULL DEFAULT '0',
  "UserID" integer NOT NULL DEFAULT '0',
  "TimeAdded" timestamp NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS "torrents_peerlists" (
  "TorrentID" integer NOT NULL,
  "GroupID" integer DEFAULT NULL,
  "Seeders" integer DEFAULT NULL,
  "Leechers" integer DEFAULT NULL,
  "Snatches" integer DEFAULT NULL,
  PRIMARY KEY ("TorrentID")
);

CREATE TABLE IF NOT EXISTS "torrents_peerlists_compare" (
  "TorrentID" integer NOT NULL,
  "GroupID" integer DEFAULT NULL,
  "Seeders" integer DEFAULT NULL,
  "Leechers" integer DEFAULT NULL,
  "Snatches" integer DEFAULT NULL,
  PRIMARY KEY ("TorrentID")
);

CREATE TABLE IF NOT EXISTS "torrents_recommended" (
  "GroupID" integer NOT NULL,
  "UserID" integer NOT NULL,
  "Time" timestamp NOT NULL DEFAULT now(),
  PRIMARY KEY ("GroupID")
);

CREATE TABLE IF NOT EXISTS "torrents_tags" (
  "TagID" integer NOT NULL DEFAULT '0',
  "GroupID" integer NOT NULL DEFAULT '0',
  "PositiveVotes" integer NOT NULL DEFAULT '1',
  "NegativeVotes" integer NOT NULL DEFAULT '1',
  "UserID" integer DEFAULT NULL,
  PRIMARY KEY ("TagID","GroupID")
);

CREATE TABLE IF NOT EXISTS "torrents_tags_votes" (
  "GroupID" integer NOT NULL,
  "TagID" integer NOT NULL,
  "UserID" integer NOT NULL,
  "Way" way NOT NULL DEFAULT 'up',
  PRIMARY KEY ("GroupID","TagID","UserID","Way")
);

CREATE TABLE IF NOT EXISTS "torrents_votes" (
  "GroupID" integer NOT NULL,
  "Ups" bigint NOT NULL DEFAULT '0',
  "Total" bigint NOT NULL DEFAULT '0',
  "Score" float NOT NULL DEFAULT '0',
  PRIMARY KEY ("GroupID"),
  CONSTRAINT "torrents_votes_ibfk_1" FOREIGN KEY ("GroupID") REFERENCES "torrents_group" ("ID") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "upload_contest" (
  "TorrentID" bigint NOT NULL,
  "UserID" bigint NOT NULL,
  PRIMARY KEY ("TorrentID"),
  CONSTRAINT "upload_contest_ibfk_1" FOREIGN KEY ("UserID") REFERENCES "users_main" ("ID") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "user_questions" (
  "ID" serial,
  "Question" text NOT NULL,
  "UserID" integer NOT NULL,
  "Date" timestamp NOT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "users_collage_subs" (
  "UserID" integer NOT NULL,
  "CollageID" integer NOT NULL,
  "LastVisit" timestamp DEFAULT NULL,
  PRIMARY KEY ("UserID","CollageID")
);

CREATE TABLE IF NOT EXISTS "users_comments_last_read" (
  "UserID" integer NOT NULL,
  "Page" page NOT NULL,
  "PageID" integer NOT NULL,
  "PostID" integer NOT NULL,
  PRIMARY KEY ("UserID","Page","PageID")
);

CREATE TABLE IF NOT EXISTS "users_donor_ranks" (
  "UserID" integer NOT NULL DEFAULT '0',
  "Rank" smallint NOT NULL DEFAULT '0',
  "DonationTime" timestamp DEFAULT NULL,
  "Hidden" smallint NOT NULL DEFAULT '0',
  "TotalRank" integer NOT NULL DEFAULT '0',
  "SpecialRank" smallint DEFAULT '0',
  "InvitesRecievedRank" smallint DEFAULT '0',
  "RankExpirationTime" timestamp DEFAULT NULL,
  PRIMARY KEY ("UserID")
);

CREATE TABLE IF NOT EXISTS "users_downloads" (
  "UserID" integer NOT NULL,
  "TorrentID" integer NOT NULL,
  "Time" timestamp NOT NULL,
  PRIMARY KEY ("UserID","TorrentID","Time")
);

CREATE TABLE IF NOT EXISTS "users_dupes" (
  "GroupID" bigint NOT NULL,
  "UserID" bigint NOT NULL,
  UNIQUE("UserID"),
  CONSTRAINT "users_dupes_ibfk_1" FOREIGN KEY ("UserID") REFERENCES "users_main" ("ID") ON DELETE CASCADE,
  CONSTRAINT "users_dupes_ibfk_2" FOREIGN KEY ("GroupID") REFERENCES "dupe_groups" ("ID") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "users_enable_recommendations" (
  "ID" integer NOT NULL,
  "Enable" smallint DEFAULT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "users_enable_requests" (
  "ID" serial,
  "UserID" bigint NOT NULL,
  "Email" varchar(255) NOT NULL,
  "IP" varchar(15) NOT NULL DEFAULT '0.0.0.0',
  "UserAgent" text NOT NULL,
  "Timestamp" timestamp NOT NULL,
  "HandledTimestamp" timestamp DEFAULT NULL,
  "Token" char(32) DEFAULT NULL,
  "CheckedBy" bigint DEFAULT NULL,
  "Outcome" smallint DEFAULT NULL,
  PRIMARY KEY ("ID"),
  CONSTRAINT "users_enable_requests_ibfk_1" FOREIGN KEY ("UserID") REFERENCES "users_main" ("ID"),
  CONSTRAINT "users_enable_requests_ibfk_2" FOREIGN KEY ("CheckedBy") REFERENCES "users_main" ("ID")
);

COMMENT ON COLUMN "users_enable_requests"."Outcome" IS '1 for approved, 2 for denied, 3 for discarded';

CREATE TABLE IF NOT EXISTS "users_freeleeches" (
  "UserID" integer NOT NULL,
  "TorrentID" integer NOT NULL,
  "Time" timestamp NOT NULL,
  "Expired" smallint NOT NULL DEFAULT '0',
  "Downloaded" bigint NOT NULL DEFAULT '0',
  "Uses" integer NOT NULL DEFAULT '1',
  PRIMARY KEY ("UserID","TorrentID")
);

CREATE TABLE IF NOT EXISTS "users_geodistribution" (
  "Code" varchar(2) NOT NULL,
  "Users" integer NOT NULL
);

CREATE TABLE IF NOT EXISTS "users_history_emails" (
  "UserID" integer NOT NULL,
  "Email" varchar(255) DEFAULT NULL,
  "Time" timestamp DEFAULT NULL,
  "IP" varchar(15) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS "users_history_ips" (
  "UserID" integer NOT NULL,
  "IP" varchar(15) NOT NULL DEFAULT '0.0.0.0',
  "StartTime" timestamp NOT NULL DEFAULT now(),
  "EndTime" timestamp DEFAULT NULL,
  PRIMARY KEY ("UserID","IP","StartTime")
);

CREATE TABLE IF NOT EXISTS "users_history_passkeys" (
  "UserID" integer NOT NULL,
  "OldPassKey" varchar(32) DEFAULT NULL,
  "NewPassKey" varchar(32) DEFAULT NULL,
  "ChangeTime" timestamp DEFAULT NULL,
  "ChangerIP" varchar(15) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS "users_history_passwords" (
  "UserID" integer NOT NULL,
  "ChangeTime" timestamp DEFAULT NULL,
  "ChangerIP" varchar(15) DEFAULT NULL
);

DROP TYPE IF EXISTS "viewavatars" CASCADE;
CREATE TYPE "viewavatars" AS enum('0','1');

DROP TYPE IF EXISTS "donor" CASCADE;
CREATE TYPE "donor" AS enum('0','1');

DROP TYPE IF EXISTS "artist" CASCADE;
CREATE TYPE "artist" AS enum('0','1');

DROP TYPE IF EXISTS "downloadalt" CASCADE;
CREATE TYPE "downloadalt" AS enum('0','1');

DROP TYPE IF EXISTS "torrentgrouping" CASCADE;
CREATE TYPE "torrentgrouping" AS enum('0','1','2');

DROP TYPE IF EXISTS "showtags" CASCADE;
CREATE TYPE "showtags" AS enum('0','1');

DROP TYPE IF EXISTS "notifyonquote" CASCADE;
CREATE TYPE "notifyonquote" AS enum('0','1','2');

DROP TYPE IF EXISTS "disableavatar" CASCADE;
CREATE TYPE "disableavatar" AS enum('0','1');

DROP TYPE IF EXISTS "disableinvites" CASCADE;
CREATE TYPE "disableinvites" AS enum('0','1');

DROP TYPE IF EXISTS "disableposting" CASCADE;
CREATE TYPE "disableposting" AS enum('0','1');

DROP TYPE IF EXISTS "disableforums" CASCADE;
CREATE TYPE "disableforums" AS enum('0','1');

DROP TYPE IF EXISTS "disableirc" CASCADE;
CREATE TYPE "disableirc" AS enum('0','1');

DROP TYPE IF EXISTS "disabletagging" CASCADE;
CREATE TYPE "disabletagging" AS enum('0','1');

DROP TYPE IF EXISTS "disableupload" CASCADE;
CREATE TYPE "disableupload" AS enum('0','1');

DROP TYPE IF EXISTS "disablewiki" CASCADE;
CREATE TYPE "disablewiki" AS enum('0','1');

DROP TYPE IF EXISTS "disablepm" CASCADE;
CREATE TYPE "disablepm" AS enum('0','1');

DROP TYPE IF EXISTS "banreason" CASCADE;
CREATE TYPE "banreason" AS enum('0','1','2','3','4');

DROP TYPE IF EXISTS "hidecountrychanges" CASCADE;
CREATE TYPE "hidecountrychanges" AS enum('0','1');

DROP TYPE IF EXISTS "disablerequests" CASCADE;
CREATE TYPE "disablerequests" AS enum('0','1');

DROP TYPE IF EXISTS "unseededalerts" CASCADE;
CREATE TYPE "unseededalerts" AS enum('0','1');

CREATE TABLE IF NOT EXISTS "users_info" (
  "UserID" bigint NOT NULL,
  "StyleID" bigint NOT NULL,
  "StyleURL" varchar(255) DEFAULT NULL,
  "Info" text NOT NULL,
  "Avatar" varchar(255) NOT NULL,
  "AdminComment" text NOT NULL,
  "SiteOptions" text NOT NULL,
  "ViewAvatars" viewavatars NOT NULL DEFAULT '1',
  "Donor" donor NOT NULL DEFAULT '0',
  "Artist" artist NOT NULL DEFAULT '0',
  "DownloadAlt" downloadalt NOT NULL DEFAULT '0',
  "Warned" timestamp NOT NULL,
  "SupportFor" varchar(255) NOT NULL,
  "TorrentGrouping" torrentgrouping NOT NULL,
  "ShowTags" showtags NOT NULL DEFAULT '1',
  "NotifyOnQuote" notifyonquote NOT NULL DEFAULT '0',
  "AuthKey" varchar(32) NOT NULL,
  "ResetKey" varchar(32) NOT NULL,
  "ResetExpires" timestamp NOT NULL DEFAULT now(),
  "JoinDate" timestamp NOT NULL DEFAULT now(),
  "Inviter" integer DEFAULT NULL,
  "BitcoinAddress" varchar(34) DEFAULT NULL,
  "WarnedTimes" integer NOT NULL DEFAULT '0',
  "DisableAvatar" disableavatar NOT NULL DEFAULT '0',
  "DisableInvites" disableinvites NOT NULL DEFAULT '0',
  "DisablePosting" disableposting NOT NULL DEFAULT '0',
  "DisableForums" disableforums NOT NULL DEFAULT '0',
  "DisableIRC" disableirc DEFAULT '0',
  "DisableTagging" disabletagging NOT NULL DEFAULT '0',
  "DisableUpload" disableupload NOT NULL DEFAULT '0',
  "DisableWiki" disablewiki NOT NULL DEFAULT '0',
  "DisablePM" disablepm NOT NULL DEFAULT '0',
  "RatioWatchEnds" timestamp NOT NULL DEFAULT now(),
  "RatioWatchDownload" numeric(20) NOT NULL DEFAULT '0',
  "RatioWatchTimes" integer NOT NULL DEFAULT '0',
  "BanDate" timestamp NOT NULL DEFAULT now(),
  "BanReason" banreason NOT NULL DEFAULT '0',
  "CatchupTime" timestamp DEFAULT NULL,
  "LastReadNews" integer NOT NULL DEFAULT '0',
  "HideCountryChanges" hidecountrychanges NOT NULL DEFAULT '0',
  "RestrictedForums" varchar(150) NOT NULL DEFAULT '',
  "DisableRequests" disablerequests NOT NULL DEFAULT '0',
  "PermittedForums" varchar(150) NOT NULL DEFAULT '',
  "UnseededAlerts" unseededalerts NOT NULL DEFAULT '0',
  "LastReadBlog" integer NOT NULL DEFAULT '0',
  "InfoTitle" varchar(255) NOT NULL,
  UNIQUE("UserID")
);

CREATE TABLE IF NOT EXISTS "users_levels" (
  "UserID" bigint NOT NULL,
  "PermissionID" bigint NOT NULL,
  PRIMARY KEY ("UserID","PermissionID")
);

CREATE TABLE IF NOT EXISTS "users_notifications_settings" (
  "UserID" integer NOT NULL DEFAULT '0',
  "Inbox" smallint DEFAULT '1',
  "StaffPM" smallint DEFAULT '1',
  "News" smallint DEFAULT '1',
  "Blog" smallint DEFAULT '1',
  "Torrents" smallint DEFAULT '1',
  "Collages" smallint DEFAULT '1',
  "Quotes" smallint DEFAULT '1',
  "Subscriptions" smallint DEFAULT '1',
  "SiteAlerts" smallint DEFAULT '1',
  "RequestAlerts" smallint DEFAULT '1',
  "CollageAlerts" smallint DEFAULT '1',
  "TorrentAlerts" smallint DEFAULT '1',
  "ForumAlerts" smallint DEFAULT '1',
  PRIMARY KEY ("UserID")
);

DROP TYPE IF EXISTS "excludeva" CASCADE;
CREATE TYPE "excludeva" AS enum('1','0');

DROP TYPE IF EXISTS "newgroupsonly" CASCADE;
CREATE TYPE "newgroupsonly" AS enum('1','0');

CREATE TABLE IF NOT EXISTS "users_notify_filters" (
  "ID" serial,
  "UserID" integer NOT NULL,
  "Label" varchar(128) NOT NULL DEFAULT '',
  "Artists" text NOT NULL,
  "RecordLabels" text NOT NULL,
  "Users" text NOT NULL,
  "Tags" varchar(500) NOT NULL DEFAULT '',
  "NotTags" varchar(500) NOT NULL DEFAULT '',
  "Categories" varchar(500) NOT NULL DEFAULT '',
  "Formats" varchar(500) NOT NULL DEFAULT '',
  "Encodings" varchar(500) NOT NULL DEFAULT '',
  "Media" varchar(500) NOT NULL DEFAULT '',
  "FromYear" integer NOT NULL DEFAULT '0',
  "ToYear" integer NOT NULL DEFAULT '0',
  "ExcludeVA" excludeva NOT NULL DEFAULT '0',
  "NewGroupsOnly" newgroupsonly NOT NULL DEFAULT '0',
  "ReleaseTypes" varchar(500) NOT NULL DEFAULT '',
  PRIMARY KEY ("ID")
);


CREATE TABLE IF NOT EXISTS "users_notify_quoted" (
  "UserID" integer NOT NULL,
  "QuoterID" integer NOT NULL,
  "Page" page NOT NULL,
  "PageID" integer NOT NULL,
  "PostID" integer NOT NULL,
  "UnRead" smallint NOT NULL DEFAULT '1',
  "Date" timestamp NOT NULL DEFAULT now(),
  PRIMARY KEY ("UserID","Page","PostID")
);

CREATE TABLE IF NOT EXISTS "users_notify_torrents" (
  "UserID" integer NOT NULL,
  "FilterID" integer NOT NULL,
  "GroupID" integer NOT NULL,
  "TorrentID" integer NOT NULL,
  "UnRead" smallint NOT NULL DEFAULT '1',
  PRIMARY KEY ("UserID","TorrentID")
);

CREATE TABLE IF NOT EXISTS "users_points" (
  "UserID" integer NOT NULL,
  "GroupID" integer NOT NULL,
  "Points" smallint NOT NULL DEFAULT '1',
  PRIMARY KEY ("UserID","GroupID")
);

CREATE TABLE IF NOT EXISTS "users_points_requests" (
  "UserID" integer NOT NULL,
  "RequestID" integer NOT NULL,
  "Points" smallint NOT NULL DEFAULT '1',
  PRIMARY KEY ("RequestID")
);

CREATE TABLE IF NOT EXISTS "users_push_notifications" (
  "UserID" integer NOT NULL,
  "PushService" smallint NOT NULL DEFAULT '0',
  "PushOptions" text NOT NULL,
  PRIMARY KEY ("UserID")
);

DROP TYPE IF EXISTS "keeplogged" CASCADE;
CREATE TYPE "keeplogged" AS enum('0','1');

CREATE TABLE IF NOT EXISTS "users_sessions" (
  "UserID" integer NOT NULL,
  "SessionID" char(32) NOT NULL,
  "KeepLogged" keeplogged NOT NULL DEFAULT '0',
  "Browser" varchar(40) DEFAULT NULL,
  "OperatingSystem" varchar(13) DEFAULT NULL,
  "IP" varchar(15) NOT NULL,
  "LastUpdate" timestamp NOT NULL,
  "Active" smallint NOT NULL DEFAULT '1',
  "FullUA" text,
  PRIMARY KEY ("UserID","SessionID") 
);


CREATE TABLE IF NOT EXISTS "users_subscriptions" (
  "UserID" integer NOT NULL,
  "TopicID" integer NOT NULL,
  PRIMARY KEY ("UserID","TopicID")
);

CREATE TABLE IF NOT EXISTS "users_subscriptions_comments" (
  "UserID" integer NOT NULL,
  "Page" page NOT NULL,
  "PageID" integer NOT NULL,
  PRIMARY KEY ("UserID","Page","PageID")
);

DROP TYPE IF EXISTS "finished" CASCADE;
CREATE TYPE "finished" AS enum('0','1');

CREATE TABLE IF NOT EXISTS "users_torrent_history" (
  "UserID" bigint NOT NULL,
  "NumTorrents" bigint NOT NULL,
  "Date" bigint NOT NULL,
  "Time" bigint NOT NULL DEFAULT '0',
  "LastTime" bigint NOT NULL DEFAULT '0',
  "Finished" finished NOT NULL DEFAULT '1',
  "Weight" numeric(20) NOT NULL DEFAULT '0',
  PRIMARY KEY ("UserID","NumTorrents","Date")
);


CREATE TABLE IF NOT EXISTS "users_torrent_history_snatch" (
  "UserID" bigint NOT NULL,
  "NumSnatches" bigint NOT NULL DEFAULT '0',
  PRIMARY KEY ("UserID")
);

CREATE TABLE IF NOT EXISTS "users_torrent_history_temp" (
  "UserID" bigint NOT NULL,
  "NumTorrents" bigint NOT NULL DEFAULT '0',
  "SumTime" numeric(20) NOT NULL DEFAULT '0',
  "SeedingAvg" bigint NOT NULL DEFAULT '0',
  PRIMARY KEY ("UserID")
);

CREATE TABLE IF NOT EXISTS "users_votes" (
  "UserID" bigint NOT NULL,
  "GroupID" integer NOT NULL,
  "Type" way DEFAULT NULL,
  "Time" timestamp NOT NULL DEFAULT now(),
  PRIMARY KEY ("UserID","GroupID"),
  CONSTRAINT "users_votes_ibfk_1" FOREIGN KEY ("GroupID") REFERENCES "torrents_group" ("ID") ON DELETE CASCADE,
  CONSTRAINT "users_votes_ibfk_2" FOREIGN KEY ("UserID") REFERENCES "users_main" ("ID") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "users_warnings_forums" (
  "UserID" bigint NOT NULL,
  "Comment" text NOT NULL,
  PRIMARY KEY ("UserID")
);

CREATE TABLE IF NOT EXISTS "wiki_aliases" (
  "Alias" varchar(50) NOT NULL,
  "UserID" integer NOT NULL,
  "ArticleID" integer DEFAULT NULL,
  PRIMARY KEY ("Alias")
);

CREATE TABLE IF NOT EXISTS "wiki_articles" (
  "ID" serial,
  "Revision" integer NOT NULL DEFAULT '1',
  "Title" varchar(100) DEFAULT NULL,
  "Body" text,
  "MinClassRead" integer DEFAULT NULL,
  "MinClassEdit" integer DEFAULT NULL,
  "Date" timestamp DEFAULT NULL,
  "Author" integer DEFAULT NULL,
  PRIMARY KEY ("ID")
);

CREATE TABLE IF NOT EXISTS "wiki_artists" (
  "RevisionID" serial,
  "PageID" integer NOT NULL DEFAULT '0',
  "Body" text,
  "UserID" integer NOT NULL DEFAULT '0',
  "Summary" varchar(100) DEFAULT NULL,
  "Time" timestamp NOT NULL DEFAULT now(),
  "Image" varchar(255) DEFAULT NULL,
  PRIMARY KEY ("RevisionID")
);

CREATE TABLE IF NOT EXISTS "wiki_revisions" (
  "ID" integer NOT NULL,
  "Revision" integer NOT NULL,
  "Title" varchar(100) DEFAULT NULL,
  "Body" text,
  "Date" timestamp DEFAULT NULL,
  "Author" integer DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS "wiki_torrents" (
  "RevisionID" serial,
  "PageID" integer NOT NULL DEFAULT '0',
  "Body" text,
  "UserID" integer NOT NULL DEFAULT '0',
  "Summary" varchar(100) DEFAULT NULL,
  "Time" timestamp NOT NULL DEFAULT now(),
  "Image" varchar(255) DEFAULT NULL,
  PRIMARY KEY ("RevisionID")
);

CREATE TABLE IF NOT EXISTS "xbt_client_whitelist" (
  "id" serial,
  "peer_id" varchar(20) DEFAULT NULL,
  "vstring" varchar(200) DEFAULT '',
  PRIMARY KEY ("id"),
  UNIQUE("peer_id")
);

CREATE TABLE IF NOT EXISTS "xbt_files_users" (
  "uid" integer NOT NULL,
  "active" smallint NOT NULL DEFAULT '1',
  "announced" integer NOT NULL DEFAULT '0',
  "completed" smallint NOT NULL DEFAULT '0',
  "downloaded" bigint NOT NULL DEFAULT '0',
  "remaining" bigint NOT NULL DEFAULT '0',
  "uploaded" bigint NOT NULL DEFAULT '0',
  "upspeed" bigint NOT NULL DEFAULT '0',
  "downspeed" bigint NOT NULL DEFAULT '0',
  "corrupt" bigint NOT NULL DEFAULT '0',
  "timespent" bigint NOT NULL DEFAULT '0',
  "useragent" varchar(51) NOT NULL DEFAULT '',
  "connectable" smallint NOT NULL DEFAULT '1',
  "peer_id" bytea NOT NULL,
  "fid" integer NOT NULL,
  "mtime" integer NOT NULL DEFAULT '0',
  "ip" varchar(15) NOT NULL DEFAULT '',
  PRIMARY KEY ("peer_id","fid","uid")
);

CREATE TABLE IF NOT EXISTS "xbt_snatched" (
  "uid" integer NOT NULL DEFAULT '0',
  "tstamp" integer NOT NULL,
  "fid" integer NOT NULL,
  "IP" varchar(15) NOT NULL
);
/*
CREATE DEFINER="root"@"localhost" FUNCTION "binomial_ci"(p int, n int) RETURNS float
    DETERMINISTIC
    SQL SECURITY INVOKER
RETURN IF(n = 0,0.0,((p + 1.35336) / n - 1.6452 * SQRT((p * (n-p)) / n + 0.67668) / n) / (1 + 2.7067 / n));


SET FOREIGN_KEY_CHECKS = 1;

*/

INSERT INTO permissions ("ID", "Level", "Name", "Values", "DisplayStaff") VALUES (15, 1000, 'Sysop', 'a:100:{s:10:\"site_leech\";i:1;s:11:\"site_upload\";i:1;s:9:\"site_vote\";i:1;s:20:\"site_submit_requests\";i:1;s:20:\"site_advanced_search\";i:1;s:10:\"site_top10\";i:1;s:19:\"site_advanced_top10\";i:1;s:16:\"site_album_votes\";i:1;s:20:\"site_torrents_notify\";i:1;s:20:\"site_collages_create\";i:1;s:20:\"site_collages_manage\";i:1;s:20:\"site_collages_delete\";i:1;s:23:\"site_collages_subscribe\";i:1;s:22:\"site_collages_personal\";i:1;s:28:\"site_collages_renamepersonal\";i:1;s:19:\"site_make_bookmarks\";i:1;s:14:\"site_edit_wiki\";i:1;s:22:\"site_can_invite_always\";i:1;s:27:\"site_send_unlimited_invites\";i:1;s:22:\"site_moderate_requests\";i:1;s:18:\"site_delete_artist\";i:1;s:20:\"site_moderate_forums\";i:1;s:17:\"site_admin_forums\";i:1;s:23:\"site_forums_double_post\";i:1;s:14:\"site_view_flow\";i:1;s:18:\"site_view_full_log\";i:1;s:28:\"site_view_torrent_snatchlist\";i:1;s:18:\"site_recommend_own\";i:1;s:27:\"site_manage_recommendations\";i:1;s:15:\"site_delete_tag\";i:1;s:23:\"site_disable_ip_history\";i:1;s:14:\"zip_downloader\";i:1;s:10:\"site_debug\";i:1;s:17:\"site_proxy_images\";i:1;s:16:\"site_search_many\";i:1;s:20:\"users_edit_usernames\";i:1;s:16:\"users_edit_ratio\";i:1;s:20:\"users_edit_own_ratio\";i:1;s:17:\"users_edit_titles\";i:1;s:18:\"users_edit_avatars\";i:1;s:18:\"users_edit_invites\";i:1;s:22:\"users_edit_watch_hours\";i:1;s:21:\"users_edit_reset_keys\";i:1;s:19:\"users_edit_profiles\";i:1;s:18:\"users_view_friends\";i:1;s:20:\"users_reset_own_keys\";i:1;s:19:\"users_edit_password\";i:1;s:19:\"users_promote_below\";i:1;s:16:\"users_promote_to\";i:1;s:16:\"users_give_donor\";i:1;s:10:\"users_warn\";i:1;s:19:\"users_disable_users\";i:1;s:19:\"users_disable_posts\";i:1;s:17:\"users_disable_any\";i:1;s:18:\"users_delete_users\";i:1;s:18:\"users_view_invites\";i:1;s:20:\"users_view_seedleech\";i:1;s:19:\"users_view_uploaded\";i:1;s:15:\"users_view_keys\";i:1;s:14:\"users_view_ips\";i:1;s:16:\"users_view_email\";i:1;s:18:\"users_invite_notes\";i:1;s:23:\"users_override_paranoia\";i:1;s:12:\"users_logout\";i:1;s:20:\"users_make_invisible\";i:1;s:9:\"users_mod\";i:1;s:13:\"torrents_edit\";i:1;s:15:\"torrents_delete\";i:1;s:20:\"torrents_delete_fast\";i:1;s:18:\"torrents_freeleech\";i:1;s:20:\"torrents_search_fast\";i:1;s:17:\"torrents_hide_dnu\";i:1;s:19:\"torrents_fix_ghosts\";i:1;s:17:\"admin_manage_news\";i:1;s:17:\"admin_manage_blog\";i:1;s:18:\"admin_manage_polls\";i:1;s:19:\"admin_manage_forums\";i:1;s:16:\"admin_manage_fls\";i:1;s:13:\"admin_reports\";i:1;s:26:\"admin_advanced_user_search\";i:1;s:18:\"admin_create_users\";i:1;s:15:\"admin_donor_log\";i:1;s:19:\"admin_manage_ipbans\";i:1;s:9:\"admin_dnu\";i:1;s:17:\"admin_clear_cache\";i:1;s:15:\"admin_whitelist\";i:1;s:24:\"admin_manage_permissions\";i:1;s:14:\"admin_schedule\";i:1;s:17:\"admin_login_watch\";i:1;s:17:\"admin_manage_wiki\";i:1;s:18:\"admin_update_geoip\";i:1;s:21:\"site_collages_recover\";i:1;s:19:\"torrents_add_artist\";i:1;s:13:\"edit_unknowns\";i:1;s:19:\"forums_polls_create\";i:1;s:21:\"forums_polls_moderate\";i:1;s:12:\"project_team\";i:1;s:25:\"torrents_edit_vanityhouse\";i:1;s:23:\"artist_edit_vanityhouse\";i:1;s:21:\"site_tag_aliases_read\";i:1;}', '1'), (11, 800, 'Moderator', 'a:89:{s:26:\"admin_advanced_user_search\";i:1;s:17:\"admin_clear_cache\";i:1;s:18:\"admin_create_users\";i:1;s:9:\"admin_dnu\";i:1;s:15:\"admin_donor_log\";i:1;s:17:\"admin_login_watch\";i:1;s:17:\"admin_manage_blog\";i:1;s:19:\"admin_manage_ipbans\";i:1;s:17:\"admin_manage_news\";i:1;s:18:\"admin_manage_polls\";i:1;s:17:\"admin_manage_wiki\";i:1;s:13:\"admin_reports\";i:1;s:23:\"artist_edit_vanityhouse\";i:1;s:13:\"edit_unknowns\";i:1;s:19:\"forums_polls_create\";i:1;s:21:\"forums_polls_moderate\";i:1;s:12:\"project_team\";i:1;s:17:\"site_admin_forums\";i:1;s:20:\"site_advanced_search\";i:1;s:19:\"site_advanced_top10\";i:1;s:16:\"site_album_votes\";i:1;s:22:\"site_can_invite_always\";i:1;s:20:\"site_collages_create\";i:1;s:20:\"site_collages_delete\";i:1;s:20:\"site_collages_manage\";i:1;s:22:\"site_collages_personal\";i:1;s:21:\"site_collages_recover\";i:1;s:28:\"site_collages_renamepersonal\";i:1;s:23:\"site_collages_subscribe\";i:1;s:18:\"site_delete_artist\";i:1;s:15:\"site_delete_tag\";i:1;s:23:\"site_disable_ip_history\";i:1;s:14:\"site_edit_wiki\";i:1;s:23:\"site_forums_double_post\";i:1;s:10:\"site_leech\";i:1;s:19:\"site_make_bookmarks\";i:1;s:27:\"site_manage_recommendations\";i:1;s:20:\"site_moderate_forums\";i:1;s:22:\"site_moderate_requests\";i:1;s:17:\"site_proxy_images\";i:1;s:18:\"site_recommend_own\";i:1;s:16:\"site_search_many\";i:1;s:27:\"site_send_unlimited_invites\";i:1;s:20:\"site_submit_requests\";i:1;s:21:\"site_tag_aliases_read\";i:1;s:10:\"site_top10\";i:1;s:20:\"site_torrents_notify\";i:1;s:11:\"site_upload\";i:1;s:14:\"site_view_flow\";i:1;s:18:\"site_view_full_log\";i:1;s:28:\"site_view_torrent_snatchlist\";i:1;s:9:\"site_vote\";i:1;s:19:\"torrents_add_artist\";i:1;s:15:\"torrents_delete\";i:1;s:20:\"torrents_delete_fast\";i:1;s:13:\"torrents_edit\";i:1;s:25:\"torrents_edit_vanityhouse\";i:1;s:19:\"torrents_fix_ghosts\";i:1;s:18:\"torrents_freeleech\";i:1;s:17:\"torrents_hide_dnu\";i:1;s:20:\"torrents_search_fast\";i:1;s:18:\"users_delete_users\";i:1;s:17:\"users_disable_any\";i:1;s:19:\"users_disable_posts\";i:1;s:19:\"users_disable_users\";i:1;s:18:\"users_edit_avatars\";i:1;s:18:\"users_edit_invites\";i:1;s:20:\"users_edit_own_ratio\";i:1;s:19:\"users_edit_password\";i:1;s:19:\"users_edit_profiles\";i:1;s:16:\"users_edit_ratio\";i:1;s:21:\"users_edit_reset_keys\";i:1;s:17:\"users_edit_titles\";i:1;s:16:\"users_give_donor\";i:1;s:12:\"users_logout\";i:1;s:20:\"users_make_invisible\";i:1;s:9:\"users_mod\";i:1;s:23:\"users_override_paranoia\";i:1;s:19:\"users_promote_below\";i:1;s:20:\"users_reset_own_keys\";i:1;s:10:\"users_warn\";i:1;s:16:\"users_view_email\";i:1;s:18:\"users_view_friends\";i:1;s:18:\"users_view_invites\";i:1;s:14:\"users_view_ips\";i:1;s:15:\"users_view_keys\";i:1;s:20:\"users_view_seedleech\";i:1;s:19:\"users_view_uploaded\";i:1;s:14:\"zip_downloader\";i:1;}', '1'), (2, 100, 'User', 'a:7:{s:10:\"site_leech\";i:1;s:11:\"site_upload\";i:1;s:9:\"site_vote\";i:1;s:20:\"site_advanced_search\";i:1;s:10:\"site_top10\";i:1;s:14:\"site_edit_wiki\";i:1;s:19:\"torrents_add_artist\";i:1;}', '0'), (3, 150, 'Member', 'a:10:{s:10:\"site_leech\";i:1;s:11:\"site_upload\";i:1;s:9:\"site_vote\";i:1;s:20:\"site_submit_requests\";i:1;s:20:\"site_advanced_search\";i:1;s:10:\"site_top10\";i:1;s:20:\"site_collages_manage\";i:1;s:19:\"site_make_bookmarks\";i:1;s:14:\"site_edit_wiki\";i:1;s:19:\"torrents_add_artist\";i:1;}', '0'), (4, 200, 'Power User', 'a:14:{s:10:\"site_leech\";i:1;s:11:\"site_upload\";i:1;s:9:\"site_vote\";i:1;s:20:\"site_submit_requests\";i:1;s:20:\"site_advanced_search\";i:1;s:10:\"site_top10\";i:1;s:20:\"site_torrents_notify\";i:1;s:20:\"site_collages_create\";i:1;s:20:\"site_collages_manage\";i:1;s:19:\"site_make_bookmarks\";i:1;s:14:\"site_edit_wiki\";i:1;s:14:\"zip_downloader\";i:1;s:19:\"forums_polls_create\";i:1;s:19:\"torrents_add_artist\";i:1;} ', '0'), (5, 250, 'Elite', 'a:18:{s:10:\"site_leech\";i:1;s:11:\"site_upload\";i:1;s:9:\"site_vote\";i:1;s:20:\"site_submit_requests\";i:1;s:20:\"site_advanced_search\";i:1;s:10:\"site_top10\";i:1;s:20:\"site_torrents_notify\";i:1;s:20:\"site_collages_create\";i:1;s:20:\"site_collages_manage\";i:1;s:19:\"site_advanced_top10\";i:1;s:19:\"site_make_bookmarks\";i:1;s:14:\"site_edit_wiki\";i:1;s:15:\"site_delete_tag\";i:1;s:14:\"zip_downloader\";i:1;s:19:\"forums_polls_create\";i:1;s:13:\"torrents_edit\";i:1;s:19:\"torrents_add_artist\";i:1;s:17:\"admin_clear_cache\";i:1;}', '0'), (20, 202, 'Donor', 'a:9:{s:9:\"site_vote\";i:1;s:20:\"site_submit_requests\";i:1;s:20:\"site_advanced_search\";i:1;s:10:\"site_top10\";i:1;s:20:\"site_torrents_notify\";i:1;s:20:\"site_collages_create\";i:1;s:20:\"site_collages_manage\";i:1;s:14:\"zip_downloader\";i:1;s:19:\"forums_polls_create\";i:1;}', '0'), (19, 201, 'Artist', 'a:9:{s:10:\"site_leech\";s:1:\"1\";s:11:\"site_upload\";s:1:\"1\";s:9:\"site_vote\";s:1:\"1\";s:20:\"site_submit_requests\";s:1:\"1\";s:20:\"site_advanced_search\";s:1:\"1\";s:10:\"site_top10\";s:1:\"1\";s:19:\"site_make_bookmarks\";s:1:\"1\";s:14:\"site_edit_wiki\";s:1:\"1\";s:18:\"site_recommend_own\";s:1:\"1\";}', '0');

INSERT INTO stylesheets ("ID", "Name", "Description", "Default") VALUES (9, 'Proton', 'Proton by Protiek', '0'), (2, 'Layer cake', 'Grey stylesheet by Emm', '0'), (21, 'postmod', 'Upgrade on anorex', '1');

INSERT INTO wiki_articles ("ID", "Revision", "Title", "Body", "MinClassRead", "MinClassEdit", "Date", "Author") VALUES (1, 1, 'Wiki', 'Welcome to your new wiki! Hope this works.', 100, 475, NOW(), 1);

INSERT INTO wiki_aliases ("Alias", "UserID", "ArticleID") VALUES ('wiki', 1, 1);

INSERT INTO wiki_revisions ("ID", "Revision", "Title", "Body", "Date", "Author") VALUES (1, 1, 'Wiki', 'Welcome to your new wiki! Hope this works.', NOW(), 1);

INSERT INTO forums ("ID", "CategoryID", "Sort", "Name", "Description", "MinClassRead", "MinClassWrite", "MinClassCreate", "NumTopics", "NumPosts", "LastPostID", "LastPostAuthorID", "LastPostTopicID", "LastPostTime") VALUES (1, 1, 20, 'Your Site', 'Totally rad forum', 100, 100, 100, 0, 0, 0, 0, 0, now()), (2, 5, 30, 'Chat', 'Expect this to fill up with spam', 100, 100, 100, 0, 0, 0, 0, 0, now()), (3, 10, 40, 'Help!', 'I fell down and I cant get up', 100, 100, 100, 0, 0, 0, 0, 0, now()), (4, 20, 100, 'Trash', 'Every thread ends up here eventually', 100, 500, 500, 0, 0, 0, 0, 0, now());

INSERT INTO tags ("ID", "Name", "TagType", "Uses", "UserID") VALUES (1, 'rock', 'genre', 0, 1),(2, 'pop', 'genre', 0, 1),(3, 'female.fronted.symphonic.death.metal', 'genre', 0, 1);

INSERT INTO schedule ("NextHour", "NextDay", "NextBiWeekly") VALUES (0,0,0);

INSERT INTO forums_categories ("ID", "Sort", "Name") VALUES (1,1,'Site');

INSERT INTO forums_categories ("ID", "Sort", "Name") VALUES (5,5,'Community');

INSERT INTO forums_categories ("ID", "Sort", "Name") VALUES (10,10,'Help');

INSERT INTO forums_categories ("ID", "Sort", "Name") VALUES (8,8,'Music');

INSERT INTO forums_categories ("ID", "Sort", "Name") VALUES (20,20,'Trash');
