--
-- MySQL db schema, created by hand
--


CREATE TABLE a (
    id integer
);


CREATE TABLE b (
    id integer
);


CREATE TABLE c (
    id integer
);


CREATE VIEW va AS
 SELECT a.id
   FROM a;


CREATE VIEW va2 AS
 SELECT va.id
   FROM va;


CREATE VIEW vb AS
 SELECT b.id
   FROM b;

