CREATE TABLE public.sites (
	id SERIAL,
	"name" varchar NOT NULL,
	"enabled" bool NOT NULL,
	test_url varchar NOT NULL,
	regex varchar NULL,
	CONSTRAINT sites_pk PRIMARY KEY (id)
);

CREATE TABLE public.site_status (
	site_id int4 NOT NULL,
	reachable bool NOT NULL,
	latency float4 NULL,
	status_code int4 NULL,
	content_valid bool NULL,
	last_update timestamp(0) NOT NULL,

	CONSTRAINT site_status_pk PRIMARY KEY (site_id),
	CONSTRAINT site_status_fk FOREIGN KEY (site_id) REFERENCES public.sites(id)
);

CREATE TABLE public.site_reports (
	site_id int4 NOT NULL,
	"timestamp" timestamp(0) NOT NULL,
	reachable boolean NOT NULL,
	status_code int4 NULL,
	content_valid bool NULL,
	latency float4 NULL,
	CONSTRAINT site_reports_pk PRIMARY KEY (site_id,"timestamp"),
	CONSTRAINT site_reports_fk FOREIGN KEY (site_id) REFERENCES public.sites(id)
);
