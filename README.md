# DB Migrator

## Overview

A simple command-line python framework to handle automatic DB migrations and updates, with working examples provided for MySQL and postgres.

This tool was written for particular requirements that existing database migration tools (eg, Redgate, DbUp, etc) don't support:

* cross platform (written in python, can support different database platforms.  Note that the concepts here can be easily ported to another language)
* database scripts are written in sensible platform-specific SQL dialect, not a DSL
* suggests an approach to database change management comprised of baseline schema, migrations, reference files, and "database code" (e.g., views, stored procedures, etc).  See [Managing Database Changes](docs/managing_database_changes.md) for more detail.
* supports a distributed development model

Notes on the code, including unit testing and implementing custom extensions to handle your project's migrations if necessary, are in the [code overview](docs/code_overview.md).

## Examples

The `examples` folder contains some running examples.  See the the
[README](/examples/README.md).

A sample run:

````
> python examples/postgres/postgres.py -nsu
Dropping and recreating postgres_test
Execute Db.sql on postgres_test
Execute 20130427_add_a_size.sql on postgres_test
Execute 20130428_create_Widget.sql on postgres_test
Execute 10_vX.sql on postgres_test
Execute bootstrap_data.sql on postgres_test
````

The examples follows the notes in [Managing Database
Changes](docs/managing_database_changes.md).  If your database project
follows the directory structure of these examples, the code can be
used as-is.

## Testing

Some of the tests manipulate actual databases running on your system.
Start the local mysql and postgres database servers before running
tests.

### User accounts

The tests assume the existence of the following accounts with admin access
to the databases (to create and destroy objects, etc):

|&nbsp;|MySql|Postgres|
|---   |---  |--- |
|host  |localhost|localhost|
|dbname|mysql|postgres|
|admin username|user|postgres|
|admin password|passwd|admin|

### Running tests

cd to the `dbMigrator` subfolder and run the tests:

```
$ cd dbMigrator
$ python -m unittest discover
```

## System Requirements

* Python (only tested on v. 2.7)
* ConfigObj library (only tested with 5.0.6)
* Six library
* Postgres tests and example require Postgres and psycopg2 library
* MySql tests and example require MySql and MySQLdb library

If running the unit tests, you'll need all the libraries.

