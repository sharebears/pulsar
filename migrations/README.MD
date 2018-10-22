# Generic single-database configuration

## Legacy Schema Documentation

Gazelle's schema (in postgres) is documented here for review and development purposes. You can spin up your own instance by setting up a local postgres instance. Then run the SQL file. It should spin up all the tables. The .sql file is as close to the original gazelle.sql file for MariaDB as possible (with FK references added)(https://github.com/WhatCD/Gazelle/blob/63b337026d49b5cf63ce4be20fdabdc880112fa3/gazelle.sql), though the indexes have been left off because we will only use this to grok the Gazelle schema at this time.

## ERD Generation

The ERD has been added to the repo as a PNG for reviewing. It's kind of busy and hard to read, so if you load it yourself using schemaspy it's a lot better because you can follow references and inspect tables in-depth. The instructions on how to build and inspect the schema using schemaspy are as follows:

- Make sure you have a local postgres up and running post sql script with all of your tables inside

- Make sure you have the minimum requirements installed (Java8 and graphviz): https://schemaspy.readthedocs.io/en/latest/installation.html#requirements

- Download the Postgres JDBC driver 4.2 from here: https://jdbc.postgresql.org/download.html

- Download latest release of schemaspy from here (you want the jar file): https://github.com/schemaspy/schemaspy/releases

- create a folder, schemaspy, and move your schemaspy jar file and driver into it. Create a schemaspy.properties file in that folder too. Your schemaspy.properties file should look something like this:

```yml
# type of database. Run with -dbhelp for details
schemaspy.t=pgsql
# database properties: host, port number, name user, password
schemaspy.host=localhost:5432
schemaspy.db=gazelle
schemaspy.u=my_postgres_user_here
schemaspy.p=my_postgres_password_here
# output dir to save generated files
schemaspy.o=/path/to/output/directory
# db scheme for which generate diagrams
schemaspy.s=public
```

- Now run schemaspy

```bash
java -jar schemaspy-6.0.1-SNAPSHOT.jar -hq -imageformat svg -dp ~/Desktop/schemaspy/postgresql-42.2.4 
```

- It should take a couple of minutes to generate for Gazelle. After generation tables and relationships and a bunch of other information are all visible in index.html in the output folder.
