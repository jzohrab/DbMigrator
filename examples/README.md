# Examples

This folder contains working examples for postgres and mysql.

## Postgres

The postgres example runs the schema and migration files in the
postgres_test on a Postgres database.  See the postgres.py
documentation for notes.

You'll need to configure the connection strings for your postgres
database to run this example.  In that directory, copy
connections.ini.template, and rename it to connections.ini.  Fill in
the details as instructed in that file.

The example is run from the command line, with command-line argument
parsing.  Here is the help output:

````
> python postgres.py -h
usage: postgres.py [-h] [-n] [-s] [-m] [-c] [-d] [-u] [db [db ...]]

Migrate one or more databases (or default database, if one is assigned).

positional arguments:
  db                name of database to manipulate

optional arguments:
  -h, --help        show this help message and exit
  -n, --new         Create new (empty) database(s)
  -s, --schema      Run baseline schema(e)
  -m, --migrations  Run migrations
  -c, --code        Run code (for views, stored procs, etc)
  -d, --data        Load reference (bootstrap) data
  -u, --update      Updates database (runs migrations, code, and data)
````

Note: python.py driver sets the "default database" referred to above
to "postgres_test", the database given in the connection.ini file.

An actual run (-nsu = "create a new database, run the baseline schema
on it, and then update it"):

````
> python postgres.py -nsu
Dropping and recreating postgres_test
Execute Db.sql on postgres_test
Execute 20130427_add_a_size.sql on postgres_test
Execute 20130428_create_Widget.sql on postgres_test
Execute 10_vX.sql on postgres_test
Execute bootstrap_data.sql on postgres_test
````

Once migrations have been run, they are not run again, so repeating an
upgrade skips the migration files (201304*.sql):

````
> python postgres.py -u
Execute 10_vX.sql on postgres_test
Execute bootstrap_data.sql on postgres_test
````

More notes on schema, migrations, code, and data are given in
[Managing Database Changes](../docs/managing_database_changes.md).


## MySQL

The MySQL example is the same as the postgres example above, with
"mysql" substituted for "postgres" in the various filenames and
directories.
