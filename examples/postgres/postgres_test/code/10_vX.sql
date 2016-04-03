/* View to get large a records. */

create or replace view vX as
select * from a where size > 1
