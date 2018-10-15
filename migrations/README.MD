# Generic single-database configuration

## Schema Documentation

Gazelle's schema (in postgres) is documented here for review and development purposes. You can spin up your own instance by setting up a local postgres instance. Then run the SQL file. It should spin up all the tables. The .sql file is as close to the original gazelle.sql file for MariaDB as possible (https://github.com/WhatCD/Gazelle/blob/63b337026d49b5cf63ce4be20fdabdc880112fa3/gazelle.sql), though the indexes have been left off because we will only use this to grok the Gazelle schema at this time.

## ERD Generation

It is possible to generate ERD of the schema after you have spun up the tables from your Postgres instance. Download SQL Power Architect JDBC (http://www.bestofbi.com/page/architect_download_os), add localhost in as a server (with gazelle as the database). Then on the left hand side expand gazelle, you will see the tables. Select all the gazelle tables (the software also brings in the internal postgres tables which we don't particularly care about) and drag them over into the center area. You will get a lot of import errors because this software doesn't support newer PostGRES datatypes. This is OK. Just select "OTHER" for all the types it doesn't recognize and hit ok. After going through several of those boxes you will get the ERD. Once you've generated the ERD, there is a button on the top that looks like a green arrow with some boxes. If you click that SPA will attempt to organize the boxes for you so that they aren't all over the place. Right now it looks pretty ugly even after doing that because there aren't a lot of FK constraints but at least you can see all the tables pretty well. 

