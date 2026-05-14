--
-- PostgreSQL database dump
--

\restrict UMzDm5WALb5gevWM1UIpdS4i6DAsuWeh52d1NVlytNUQuBWrJavxpy5s1ThsocN

-- Dumped from database version 16.13 (Debian 16.13-1.pgdg13+1)
-- Dumped by pg_dump version 16.13 (Debian 16.13-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: trace_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO trace_user;

--
-- Name: files; Type: TABLE; Schema: public; Owner: trace_user
--

CREATE TABLE public.files (
    id integer NOT NULL,
    storage_path character varying(500) NOT NULL,
    content_type character varying(50) NOT NULL,
    size_bytes integer NOT NULL,
    sha256 character varying(64) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.files OWNER TO trace_user;

--
-- Name: files_id_seq; Type: SEQUENCE; Schema: public; Owner: trace_user
--

CREATE SEQUENCE public.files_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.files_id_seq OWNER TO trace_user;

--
-- Name: files_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trace_user
--

ALTER SEQUENCE public.files_id_seq OWNED BY public.files.id;


--
-- Name: labeled_jobs; Type: TABLE; Schema: public; Owner: trace_user
--

CREATE TABLE public.labeled_jobs (
    id integer NOT NULL,
    status character varying(20) NOT NULL,
    kind character varying(20) NOT NULL,
    raw_trace_id integer NOT NULL,
    group_id integer NOT NULL,
    requested_by integer NOT NULL,
    t_from timestamp with time zone,
    t_to timestamp with time zone,
    tool_info character varying(200),
    error_text character varying(2000),
    created_at timestamp with time zone DEFAULT now(),
    started_at timestamp with time zone,
    finished_at timestamp with time zone
);


ALTER TABLE public.labeled_jobs OWNER TO trace_user;

--
-- Name: labeled_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: trace_user
--

CREATE SEQUENCE public.labeled_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.labeled_jobs_id_seq OWNER TO trace_user;

--
-- Name: labeled_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trace_user
--

ALTER SEQUENCE public.labeled_jobs_id_seq OWNED BY public.labeled_jobs.id;


--
-- Name: labeled_trace_sources; Type: TABLE; Schema: public; Owner: trace_user
--

CREATE TABLE public.labeled_trace_sources (
    id integer NOT NULL,
    labeled_trace_id integer NOT NULL,
    raw_trace_id integer NOT NULL
);


ALTER TABLE public.labeled_trace_sources OWNER TO trace_user;

--
-- Name: labeled_trace_sources_id_seq; Type: SEQUENCE; Schema: public; Owner: trace_user
--

CREATE SEQUENCE public.labeled_trace_sources_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.labeled_trace_sources_id_seq OWNER TO trace_user;

--
-- Name: labeled_trace_sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trace_user
--

ALTER SEQUENCE public.labeled_trace_sources_id_seq OWNED BY public.labeled_trace_sources.id;


--
-- Name: labeled_traces; Type: TABLE; Schema: public; Owner: trace_user
--

CREATE TABLE public.labeled_traces (
    id integer NOT NULL,
    kind character varying(32) NOT NULL,
    group_id integer NOT NULL,
    file_id integer NOT NULL,
    description_file_id integer,
    software_desc character varying(255),
    t_from timestamp with time zone,
    t_to timestamp with time zone,
    created_by integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.labeled_traces OWNER TO trace_user;

--
-- Name: labeled_traces_id_seq; Type: SEQUENCE; Schema: public; Owner: trace_user
--

CREATE SEQUENCE public.labeled_traces_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.labeled_traces_id_seq OWNER TO trace_user;

--
-- Name: labeled_traces_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trace_user
--

ALTER SEQUENCE public.labeled_traces_id_seq OWNED BY public.labeled_traces.id;


--
-- Name: raw_groups; Type: TABLE; Schema: public; Owner: trace_user
--

CREATE TABLE public.raw_groups (
    id integer NOT NULL,
    org character varying(50) NOT NULL,
    data_character character varying(200) NOT NULL,
    capture_start timestamp with time zone NOT NULL,
    capture_end timestamp with time zone NOT NULL,
    hardware_desc character varying(300) NOT NULL,
    software_desc character varying(300) NOT NULL,
    processing_degree character varying(300) NOT NULL,
    capture_points integer NOT NULL,
    schema_file_id integer,
    description_file_id integer,
    created_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.raw_groups OWNER TO trace_user;

--
-- Name: raw_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: trace_user
--

CREATE SEQUENCE public.raw_groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.raw_groups_id_seq OWNER TO trace_user;

--
-- Name: raw_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trace_user
--

ALTER SEQUENCE public.raw_groups_id_seq OWNED BY public.raw_groups.id;


--
-- Name: raw_traces; Type: TABLE; Schema: public; Owner: trace_user
--

CREATE TABLE public.raw_traces (
    id integer NOT NULL,
    group_id integer NOT NULL,
    point character varying(10) NOT NULL,
    file_id integer NOT NULL,
    t_min timestamp with time zone,
    t_max timestamp with time zone,
    packets_count integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    capture_series character varying(255),
    part_index integer
);


ALTER TABLE public.raw_traces OWNER TO trace_user;

--
-- Name: raw_traces_id_seq; Type: SEQUENCE; Schema: public; Owner: trace_user
--

CREATE SEQUENCE public.raw_traces_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.raw_traces_id_seq OWNER TO trace_user;

--
-- Name: raw_traces_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trace_user
--

ALTER SEQUENCE public.raw_traces_id_seq OWNED BY public.raw_traces.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: trace_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    login character varying(8) NOT NULL,
    password_hash character varying(255) NOT NULL,
    last_name character varying(50) NOT NULL,
    first_name character varying(50) NOT NULL,
    organization character varying(50) NOT NULL,
    email character varying(50) NOT NULL,
    role character varying(10) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.users OWNER TO trace_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: trace_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO trace_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: trace_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: files id; Type: DEFAULT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.files ALTER COLUMN id SET DEFAULT nextval('public.files_id_seq'::regclass);


--
-- Name: labeled_jobs id; Type: DEFAULT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_jobs ALTER COLUMN id SET DEFAULT nextval('public.labeled_jobs_id_seq'::regclass);


--
-- Name: labeled_trace_sources id; Type: DEFAULT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_trace_sources ALTER COLUMN id SET DEFAULT nextval('public.labeled_trace_sources_id_seq'::regclass);


--
-- Name: labeled_traces id; Type: DEFAULT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_traces ALTER COLUMN id SET DEFAULT nextval('public.labeled_traces_id_seq'::regclass);


--
-- Name: raw_groups id; Type: DEFAULT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.raw_groups ALTER COLUMN id SET DEFAULT nextval('public.raw_groups_id_seq'::regclass);


--
-- Name: raw_traces id; Type: DEFAULT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.raw_traces ALTER COLUMN id SET DEFAULT nextval('public.raw_traces_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: trace_user
--

COPY public.alembic_version (version_num) FROM stdin;
bebe52434fef
\.


--
-- Data for Name: files; Type: TABLE DATA; Schema: public; Owner: trace_user
--

COPY public.files (id, storage_path, content_type, size_bytes, sha256, created_at) FROM stdin;
\.


--
-- Data for Name: labeled_jobs; Type: TABLE DATA; Schema: public; Owner: trace_user
--

COPY public.labeled_jobs (id, status, kind, raw_trace_id, group_id, requested_by, t_from, t_to, tool_info, error_text, created_at, started_at, finished_at) FROM stdin;
\.


--
-- Data for Name: labeled_trace_sources; Type: TABLE DATA; Schema: public; Owner: trace_user
--

COPY public.labeled_trace_sources (id, labeled_trace_id, raw_trace_id) FROM stdin;
\.


--
-- Data for Name: labeled_traces; Type: TABLE DATA; Schema: public; Owner: trace_user
--

COPY public.labeled_traces (id, kind, group_id, file_id, description_file_id, software_desc, t_from, t_to, created_by, created_at) FROM stdin;
\.


--
-- Data for Name: raw_groups; Type: TABLE DATA; Schema: public; Owner: trace_user
--

COPY public.raw_groups (id, org, data_character, capture_start, capture_end, hardware_desc, software_desc, processing_degree, capture_points, schema_file_id, description_file_id, created_by, created_at) FROM stdin;
\.


--
-- Data for Name: raw_traces; Type: TABLE DATA; Schema: public; Owner: trace_user
--

COPY public.raw_traces (id, group_id, point, file_id, t_min, t_max, packets_count, created_at, capture_series, part_index) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: trace_user
--

COPY public.users (id, login, password_hash, last_name, first_name, organization, email, role, created_at) FROM stdin;
1	admin000	$2b$12$P6pXX4R2fWGZSgyq/2nVFOA8pMWWaEdzVybasy377tRiCvlWkDd1.	Haidei	Mariia	MSU	st02220069@gse.cs.msu.ru	admin	2026-05-13 19:14:20.593607+00
\.


--
-- Name: files_id_seq; Type: SEQUENCE SET; Schema: public; Owner: trace_user
--

SELECT pg_catalog.setval('public.files_id_seq', 1, false);


--
-- Name: labeled_jobs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: trace_user
--

SELECT pg_catalog.setval('public.labeled_jobs_id_seq', 1, false);


--
-- Name: labeled_trace_sources_id_seq; Type: SEQUENCE SET; Schema: public; Owner: trace_user
--

SELECT pg_catalog.setval('public.labeled_trace_sources_id_seq', 1, false);


--
-- Name: labeled_traces_id_seq; Type: SEQUENCE SET; Schema: public; Owner: trace_user
--

SELECT pg_catalog.setval('public.labeled_traces_id_seq', 1, false);


--
-- Name: raw_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: trace_user
--

SELECT pg_catalog.setval('public.raw_groups_id_seq', 1, false);


--
-- Name: raw_traces_id_seq; Type: SEQUENCE SET; Schema: public; Owner: trace_user
--

SELECT pg_catalog.setval('public.raw_traces_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: trace_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: files files_pkey; Type: CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_pkey PRIMARY KEY (id);


--
-- Name: files files_storage_path_key; Type: CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_storage_path_key UNIQUE (storage_path);


--
-- Name: labeled_jobs labeled_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_jobs
    ADD CONSTRAINT labeled_jobs_pkey PRIMARY KEY (id);


--
-- Name: labeled_trace_sources labeled_trace_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_trace_sources
    ADD CONSTRAINT labeled_trace_sources_pkey PRIMARY KEY (id);


--
-- Name: labeled_traces labeled_traces_pkey; Type: CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_traces
    ADD CONSTRAINT labeled_traces_pkey PRIMARY KEY (id);


--
-- Name: raw_groups raw_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.raw_groups
    ADD CONSTRAINT raw_groups_pkey PRIMARY KEY (id);


--
-- Name: raw_traces raw_traces_pkey; Type: CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.raw_traces
    ADD CONSTRAINT raw_traces_pkey PRIMARY KEY (id);


--
-- Name: labeled_trace_sources uq_labeled_trace_source_pair; Type: CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_trace_sources
    ADD CONSTRAINT uq_labeled_trace_source_pair UNIQUE (labeled_trace_id, raw_trace_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_labeled_trace_sources_labeled_trace_id; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_labeled_trace_sources_labeled_trace_id ON public.labeled_trace_sources USING btree (labeled_trace_id);


--
-- Name: ix_labeled_trace_sources_raw_trace_id; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_labeled_trace_sources_raw_trace_id ON public.labeled_trace_sources USING btree (raw_trace_id);


--
-- Name: ix_labeled_traces_file_id; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE UNIQUE INDEX ix_labeled_traces_file_id ON public.labeled_traces USING btree (file_id);


--
-- Name: ix_labeled_traces_group_id; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_labeled_traces_group_id ON public.labeled_traces USING btree (group_id);


--
-- Name: ix_labeled_traces_kind; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_labeled_traces_kind ON public.labeled_traces USING btree (kind);


--
-- Name: ix_raw_groups_capture_end; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_raw_groups_capture_end ON public.raw_groups USING btree (capture_end);


--
-- Name: ix_raw_groups_capture_points; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_raw_groups_capture_points ON public.raw_groups USING btree (capture_points);


--
-- Name: ix_raw_groups_capture_start; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_raw_groups_capture_start ON public.raw_groups USING btree (capture_start);


--
-- Name: ix_raw_groups_data_character; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_raw_groups_data_character ON public.raw_groups USING btree (data_character);


--
-- Name: ix_raw_groups_org; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_raw_groups_org ON public.raw_groups USING btree (org);


--
-- Name: ix_raw_traces_capture_series; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_raw_traces_capture_series ON public.raw_traces USING btree (capture_series);


--
-- Name: ix_raw_traces_file_id; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_raw_traces_file_id ON public.raw_traces USING btree (file_id);


--
-- Name: ix_raw_traces_group_id; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_raw_traces_group_id ON public.raw_traces USING btree (group_id);


--
-- Name: ix_raw_traces_part_index; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_raw_traces_part_index ON public.raw_traces USING btree (part_index);


--
-- Name: ix_raw_traces_t_max; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_raw_traces_t_max ON public.raw_traces USING btree (t_max);


--
-- Name: ix_raw_traces_t_min; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE INDEX ix_raw_traces_t_min ON public.raw_traces USING btree (t_min);


--
-- Name: ix_users_login; Type: INDEX; Schema: public; Owner: trace_user
--

CREATE UNIQUE INDEX ix_users_login ON public.users USING btree (login);


--
-- Name: labeled_jobs labeled_jobs_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_jobs
    ADD CONSTRAINT labeled_jobs_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.raw_groups(id);


--
-- Name: labeled_jobs labeled_jobs_raw_trace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_jobs
    ADD CONSTRAINT labeled_jobs_raw_trace_id_fkey FOREIGN KEY (raw_trace_id) REFERENCES public.raw_traces(id);


--
-- Name: labeled_jobs labeled_jobs_requested_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_jobs
    ADD CONSTRAINT labeled_jobs_requested_by_fkey FOREIGN KEY (requested_by) REFERENCES public.users(id);


--
-- Name: labeled_trace_sources labeled_trace_sources_labeled_trace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_trace_sources
    ADD CONSTRAINT labeled_trace_sources_labeled_trace_id_fkey FOREIGN KEY (labeled_trace_id) REFERENCES public.labeled_traces(id) ON DELETE CASCADE;


--
-- Name: labeled_trace_sources labeled_trace_sources_raw_trace_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_trace_sources
    ADD CONSTRAINT labeled_trace_sources_raw_trace_id_fkey FOREIGN KEY (raw_trace_id) REFERENCES public.raw_traces(id) ON DELETE CASCADE;


--
-- Name: labeled_traces labeled_traces_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_traces
    ADD CONSTRAINT labeled_traces_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: labeled_traces labeled_traces_description_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_traces
    ADD CONSTRAINT labeled_traces_description_file_id_fkey FOREIGN KEY (description_file_id) REFERENCES public.files(id) ON DELETE SET NULL;


--
-- Name: labeled_traces labeled_traces_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_traces
    ADD CONSTRAINT labeled_traces_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.files(id) ON DELETE CASCADE;


--
-- Name: labeled_traces labeled_traces_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.labeled_traces
    ADD CONSTRAINT labeled_traces_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.raw_groups(id) ON DELETE CASCADE;


--
-- Name: raw_groups raw_groups_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.raw_groups
    ADD CONSTRAINT raw_groups_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: raw_groups raw_groups_description_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.raw_groups
    ADD CONSTRAINT raw_groups_description_file_id_fkey FOREIGN KEY (description_file_id) REFERENCES public.files(id) ON DELETE SET NULL;


--
-- Name: raw_groups raw_groups_schema_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.raw_groups
    ADD CONSTRAINT raw_groups_schema_file_id_fkey FOREIGN KEY (schema_file_id) REFERENCES public.files(id) ON DELETE SET NULL;


--
-- Name: raw_traces raw_traces_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.raw_traces
    ADD CONSTRAINT raw_traces_file_id_fkey FOREIGN KEY (file_id) REFERENCES public.files(id) ON DELETE CASCADE;


--
-- Name: raw_traces raw_traces_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: trace_user
--

ALTER TABLE ONLY public.raw_traces
    ADD CONSTRAINT raw_traces_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.raw_groups(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict UMzDm5WALb5gevWM1UIpdS4i6DAsuWeh52d1NVlytNUQuBWrJavxpy5s1ThsocN

