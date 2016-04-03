--
-- PostgreSQL database dump
--

-- Dumped from database version 9.3.4
-- Dumped by pg_dump version 9.3.4
-- Started on 2014-04-02 17:16:57

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- TOC entry 176 (class 3079 OID 11750)
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- TOC entry 1958 (class 0 OID 0)
-- Dependencies: 176
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 170 (class 1259 OID 16462)
-- Name: a; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE a (
    id integer
);


ALTER TABLE public.a OWNER TO postgres;

--
-- TOC entry 171 (class 1259 OID 16465)
-- Name: b; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE b (
    id integer
);


ALTER TABLE public.b OWNER TO postgres;

--
-- TOC entry 172 (class 1259 OID 16468)
-- Name: c; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE c (
    id integer
);


ALTER TABLE public.c OWNER TO postgres;

--
-- TOC entry 173 (class 1259 OID 16471)
-- Name: va; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW va AS
 SELECT a.id
   FROM a;


ALTER TABLE public.va OWNER TO postgres;

--
-- TOC entry 174 (class 1259 OID 16475)
-- Name: va2; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW va2 AS
 SELECT va.id
   FROM va;


ALTER TABLE public.va2 OWNER TO postgres;

--
-- TOC entry 175 (class 1259 OID 16479)
-- Name: vb; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW vb AS
 SELECT b.id
   FROM b;


ALTER TABLE public.vb OWNER TO postgres;

--
-- TOC entry 1957 (class 0 OID 0)
-- Dependencies: 5
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2014-04-02 17:16:57

--
-- PostgreSQL database dump complete
--

