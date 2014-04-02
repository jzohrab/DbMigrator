# Managing Database Changes

This tool suggests an approach to database change management where all database-defining files fall into four distinct categories:

1. Baseline schema: baseline schema files should create only schema items that deal with persisted data (tables and indexes) as currently exist in production.
2. Migrations: files which change the database table structure and indexes only.
3. Code: any part of the database that does not define persisted data (e.g., triggers, views, stored procedures, functions, etc.)
4. Reference data: idempotent data files which are "bootstrap data" required for the application to run (e.g., tables of months, postal codes, etc)

The sample migrations used by the [examples](examples.md) and by the postgres unit test `dbMigrator/test/testDatabase/postgres_test` illustrate these categories.  The Migrator class uses a DatabaseSource which should return files in these categories.

## Main points for each file category

Each of the above files should be scripted out into separate directories.  Note that should you choose to not use "code" or "reference data" file types, you just wouldn't use the corresponding Migrator methods (`run_code_definitions` and `run_reference_data`); however, these categories are still recommended -- see below.  The DatabaseSource abstract class defines the interface for how these files should be returned (see the [code overview](code_overview.md)).

### Baseline schema

The baseline schema file should only create tables and views, and should only ever be run on an empty database.  When initially starting a project, the baseline schema may be blank, and the database schema would be created through a series of migration files, or you may choose to commit an initial schema and work from there.  If a project is already underway and will be managed by this tool, the production schema (tables and indexes only) should be scripted out to one or more files.  You may also choose to periodically update this schema with what's currently in production (see "Re-baselining" below).

Other objects, such as views etc., can be included in the baseline scripts, but such objects are better classed as "code" objects (see below).  Sometimes including such objects in the baseline script is expedient when re-baselining.

Other than the initial commit, or re-baselining, the baseline schema should **never be touched**.  Changes to this file would not be applied to production, and would be lost on re-baselining.  Developers should commit their changes as migrations, code, or reference data file changes.

Baseline schema scripts can follow any naming convention, provided they respect file ordering (see "Order of Execution"), and there can be as many scripts as needed for a database.


### Migrations

Migrations are scripts that modify the database's tables and indexes, including data migrations.  These should be straight sql alter/drop/create statements and the like.  When migration scripts are run, they are tracked in a __schema_migrations table in the underlying database, ensuring that they are not re-run.  (These are the only scripts that are tracked in this table.)

Migrations are the most sensitive and critical part of database changes.  If a view isn't defined correctly, it is an inconvenience, but if a migration isn't correct, it can be impossible to recover from.  The use of this tool during development (see "Usage Patterns" below) can quickly find incompatible migrations.

Migrations should follow certain strict design guidelines:

* **They should follow a specific naming convention which gives a deterministic sorting order.**  Migrations can be created by several developers working independently on several distributed code branches.  By specifying a file naming convention such as YYYYMMDD_HHNNSS_description.sql (eg, "20140425_130122_add_Widgets_CalcPrice.sql"), the migrator can deterministically apply the migrations in order to a given database, without relying on another source (such as a "manifest" which tracks files to be applied).

* **They must not be designed to be idempotent.**  Usually, with database change scripts, guards are added around sections to ensure that a given object does or doesn't exist (eg, ````if not exists (... some column ...) then; ... create column ...; end if;````).  Migrations should not follow this practice, as it could allow for inconsistent changes.  For example, if two developers are working on a project, and both submit migrations that add column CalculatedPrice to table Widgets surrounded by "if not exists" guards", then one or the other script will not be run.  This might seem trivial, but they may have radically different ideas about what the column should contain, and have initialized it differently.  Without the "if not exists" guard, one or the other script would fail, which promotes discussion.

* **They must not be edited once they have been run in production.**  The Migrator class keeps track of which scripts have been run, and when database changes are launched to production the DBAs should be archiving any migration scripts applied in production, and also logging them to the table which tracks the migration scripts.  If a migration script is changed, and it is tracked in the __schema_migrations table, it will not be re-run; similarly, DBAs will not note that the script has been changed.

* **The should not depend on a "database version number" or equivalent.**  Some database migration tools have the notion of a version number, with the idea that you "migrate up" from one specific version to another.  This does not work with a distributed version control system such as Git.  Scripts should be runnable to the best of their knowledge (the state of the schema at that time).

* **They should only create tables, and not code objects.**  A migration updates an object using instructions that it knows about, and code objects (views, stored procedures, etc.) are different from tables in that the former cannot be incrementally updated (e.g., there is no way to "add a column to a view", you have to replace the entire view, whereas with tables, you can incrementally update it).

  To illustrate why migrations should not be used for code objects, suppose a given database has a view vListWidgets, and two developers submit migration files for that same view: the view will reflect whichever migration is played last.  While it would be possible to scan the list of incoming migrations to see if there is a clash for code objects, that would be tiresome and error-prone.  Here, the two developers should have worked on a single code definition file, vListWidgets.sql, and their conflicts would have surfaced as merge conflicts.

* **Changes which touch referential data tables should be accompanied by changes to the referential data scripts.**  Sometimes referential tables' structures must change, but the referential data should be kept in a canonical source.  For example, a table of PostalCodes may be augmented with a new DateAdded non-null column.  If the migration script made the accompanying data changes (e.g., "update PostalCodes set DateAdded = 'apr 23, 2014' where Code='abcdef'"), the system code would deteriorate, as the reference data would now be spread across separate files.  In this example, the PostalCodes table should have been augemented with a nullable DateAdded column, a sensible default applied, and then the referential data file should have been re-applied (the referential data file would contain the correct DateAdded for each Code).  This would ensure that the PostalCodes reference data file would be **the** canonical source for this important information.

* **Migrations can and should be used to drop code objects.**  The Migrator class runs code scripts to create views, stored procedures, etc.  Every code script should create one object (it would be possible to create multiple objects in a code script, but that may be hard to follow).  The Migrator class does not take the absence of a code script in the file system as an instruction to delete a code object, should one exist (for example, if code scripts exist for views A and B, and the database contains A, B, and C, then A and B will be updated, but C will be left as-is).

  To drop a code object, a migration script should be created that explicitly drops the object, and then the corresponding code script should be deleted from the file system as well.  In the above example, a migration "<datetime>_drop_A.sql" would be created, and the "A.sql" code script would be deleted.  The Migrator would then drop the A object, and not create it.


### Code

"Code objects" are everything in the database that is not a table or an index.

From a development perspective, these objects are routines that take given inputs (often implicit, such as underlying data in the case of views) and provide given outputs, so the scripts that create these objects should be treated as code - using code branching and merging practices should apply.  An example of why code objects are best created with code object scripts, and not migration scripts, is given above in "Migrations - They should only create tables, and not code objects".

* **Code object scripts should be re-runnable, and should fully drop and re-create the object anew.** Some database platforms like Postgres have syntax like "create or update view".  Other platforms require that the creation be in its own batch.  In the latter case, the single script file should drop the object in one batch, and then recreate the object in a separate batch (the DatabaseHandler for that platform would then split the file up correctly).

* **Some code object files should follow a specific naming convention which gives a deterministic sorting order.**  Some code objects rely on other code objects (e.g., nested views).  Such objects' filenames should determine their execution order.  Other code objects which can be created in any order whatsoever can have sensible filenames.  For example, for a database where vB depends on vA, but vC is independent, the code folder might contain files 10_vA, 20_vB, and vC.sql.  (See "Order of Execution".)

* **Testing, or at least smoke testing, should be added to project CI.**  Several developers may make incompatible changes to a given code object's file.  A quick smoke test ("test_ensure_all_views_actually_execute") can be useful.

### Reference data

Reference data is data that the application needs to run at all.  The delineation between "reference data" and "just plain data" depends on the application - some applications may deal, e.g., specially with certain Supplier entities, so these might be included in a Suppliers.sql reference data file.


* **Reference data scripts must be idempotent.**  The reason for this seemingly arbitrary rule is that reference data should be **the** canonical source of this information, and the reference data scripts should be re-runnable at any point to allow for seeding or re-seeding of the database.  See point "Changes which touch referential data tables should be accompanied by changes to the referential data scripts" in the Migrations section above.

  The idempotency requirement can be met in various ways:

  * Create stored procedures that handle the correct create/update steps.  The reference data files would call these procedures.

  * A three-step process where a temporary table is loaded with the desired reference data, new data is loaded to the final table, and the final table is then updated.  This is the process taken in the test database (dbMigrator/test/testDatabase/postgres_test/reference_data/bootstrap_data.sql).


## Order of Execution

The scripts should be executed in the following order:

1. Baseline schema (if required)
2. Migrations
3. Code
4. Reference data

The **Driver** class (see the [code overview](code_overview.md)) handles the above correctly.  If you code a wrapper, your wrapper should respect the above as well.

Within each category, files are executed in filename-sort order.  In addition, if you are using the tool to migrate several databases (e.g. using the Driver, ````python driver.exe -u db1 db2````), the files in each category are additionally sorted across all database.  This is useful in the case of cross-database dependencies.

For example, suppose db1 has code files 10_vA.sql, 20_vB.sql, and vC.sql, and db2 has 15_vX.sql and 20_vB.sql.  The **Migrator** class would sort them in the following order:

````
10_vA.sql in db1
15_vX.sql in db2
20_vB.sql in db1
20_vB.sql in db2
vC.sql in db1
````

Note that the database name is used as part of the sort key, so db1's 20_vB.sql is run before that of db2.


## Re-baselining

The migration files can grow quickly over time, so it is useful to periodically re-baseline your project's database from production.

To re-baseline, do the following:

1. Script out the current state of the tables and indexes in production.
2. Ensure that any of the migration scripts in the migrations folder have been entered in the __schema_migrations table.
3. Script out the content of the __schema_migrations table (as an appropriate series of insert statements), and commit it to the "baseline schema" directory of your project, such that it will run after the baseline schema (e.g., if the schema is "baseline_schema.sql", then the __schema_migrations file could be named "migrations_applied.sql")
4. Optional: move any applied migrations files to an archive folder.
5. Commit these changes on a branch, and tell developers to update their branches with the new production database baseline schema (which will also archive the applied migrations in their branches).
