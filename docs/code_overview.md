# Code

## migrator module

The **migrator** module contains the migration library classes.  The central **Migrator** class (Facade pattern) reads the appropriate database files from disk using an impementation of the abstract class **DatabaseSource**, and passes them to a **QueuedScriptCollection** which sorts the scripts into the correct execution order.  The scripts are passed in order to a **ScriptRunner** instance, which calls an implementation of the abstract class **DatabaseHandler** as required by the target database platform.  The **ScriptRunner** determines if scripts should be run or not (it creates and manages a table of previously run migrations in a tracking table in the database).

The **DatabaseSource** and **DatabaseHandler** are abstract to allow for the **Migrator** to be re-used in different projects that have different directory structures, and different database platforms.

The [postgres example](../examples/README.md) illustrates these classes, and some sensible defaults.


## Unit and Integration Testing

Tests are in `./test`.  They ran be run from project root with `make test`.

The database tests destructively test their databases (destroy and recreate, etc.).


## Using the Framework

As mentioned in the Overview, this tool does not handle all database migrations out-of-the-box, unless you follow the same layout given in the Postgres or MySQL examples.  The main **Migrator** class handles the migrations, but it needs to understand your particular project and database platform, and it needs a wrapper that satisfies your automation requirements.  You must implement some abstract classes and a wrapper/driver class (sensible defaults are also provided, which may either be used outright, or as the basis for custom code):

1. Implement abstract class **migrator.DatabaseSource**.  This class pulls database migration files from disk, as required for your project's directory structure.  A **DefaultDatabaseSource** is included, which can be used if your project's database files are laid out as described in that class's documentation.

2. Implement abstract class **migrator.DatabaseHandler**.  This class should be implemented and tested for your database platform.  The **PostgresDatabaseHandler** is provided for postgres databases.

3. Implement a wrapper class, callable from the command line, which calls the appropriate **Migrator** methods.  The **Driver** class can either be reused for your project, or as sample code (note that the **Driver** class is used by the examples).

The [examples](../examples) show working examples which use the defaults.  You can choose if custom coding or project structure changes would be easier to introduce into your workflow.