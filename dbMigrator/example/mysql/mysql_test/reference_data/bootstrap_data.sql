/* Idempotent data script. */
/* NOTE: THIS SCRIPT MUST BE REPEATEDLY RE-RUNNABLE. */

-- Below is possible method to idempotently load reference data.  Summary:
--   1) load temp table with full data set
--   2) insert new data in the temp table into the final table
--   3) update the final table with the data from the temp table.

-- Should drop temp_a before starting (not included here!)

create temporary table temp_a(id int, size int);

-- 1) Load full set of referential data:
insert into temp_a(id, size) values
(1, 2),
(2, 3),
(4, 42),
(5, 555);

-- 2) Load final table with any missing records (note this example uses the ID,
-- in real life a business key would be preferable):
insert into a (id, size)
select id, size from temp_a
where temp_a.id not in (select id from a);

-- 3) Update table with final data (matching on business key):
update a
join temp_a on temp_a.id = a.id
set a.size=temp_a.size;

drop table temp_a;
