# SiteMon

A minimalistic website monitoring system based on Faust, Kafka, and Postgres

Faust handles most of the plumping and kafka connectivity.

The writer (recording monitoring reports to the db ) is implemented as a Faust agent. Once all the dependcies are installed, it can be with the following command `faust -A sitemon.main worker -l info`

The monitor (gather site metrics) is implemented with Faust `command` and can be invoked with `faust -A sitemon.app -l info monitor-sites`

A `sitemon` script is defined as part of the package and can be used in place of `faust -A sitemon.main` in the above commands.


# Building the container image

A container image can be built with the following command:

```
docker build -t sitemon .
```

# Local Demo

A demo of the system can be started locally by using `docker-compose`. First, start up the storage/db components

```
docker-compose -f docker-compose.local.yaml up -d zookeeper kafka db
```

Give the a little time to settle (in particular the postgres db), then the rest can be started.

```
docker-compose -f docker-compose.local.yaml up -d
```

The monitor will only start correctly once some sites have been added to the database (it is exposed on the default postgres port).

# Configuration

## General

The configuration for both the monitor and writers is passed in through environment variables. (Using `.env` file is also supported.)

At minima, the following variables must be defined to specify the Kafka broker and postgres endpoints.

```
KAFKA_BROKER=kafka://kafka_host:kafka_port
POSTGRES_DSN=postgres://user:pass@db_host:port/db_name
```

If SSL/TLS is required for Kafka, the following three extra variable must be defined and point to the relevant files
```
KAFKA_AUTH_CA=/path/to/ca.crt
KAFKA_ACCESS_KEY=/path/to/access.key
KAFKA_ACCESS_CRT=/path/to/access.crt
```

For Postgres requiring SSL/TLS can be passed as argument to in the DSN (as ssl=require/verify-ca/verify-full):

```
POSTGRES_DSN=postgres://user:pass@db_host:port/db_name?ssl=require
```

The last configuration option is the interval between site scans:

```
SCAN_INTERVAL=60
```

## Sites

The sites to be scanned are stores in the `sites` database table, which contains the following fields:

 * *id*: Numerical id uniquely identifying the site (default: `nextval('sites_id_seq')`)
 * *name*: A human-readable name for the site
 * *enabled*: Flag determining if to include the site in scans
 * *test_url*: The url to perform the scan on
 * *regex*: An optional regular expression which will be searched within the body of the response to validate the reponse.

A sample configuration could like like:

| id | name      | enabled | test_url               | regex     |
|----|-----------|---------|------------------------|-----------|
|  1 | Example   | TRUE    | https://example.com    |           |
|  2 | Google    | FALSE   | https://google.com     | Google    |
|  3 | Microsoft | FALSE   | https://microsoft.com  | Microsoft |
| ...| ...       | ...     | ...                    | ...       |

# Future Improvements and other Unfinished Business

 - [ ] Add mechanism to wait for db to come up at start up
 - [ ] Timing currently measures whole request, including DNS resolution, make this more fine grained
 - [ ] Clean up and align nomenclature between db/records
 - [ ] Time based availability stats, these should be easily implemented with Faust tables
 - [ ] Site specific time intervals, could simply be implemented by:
    * Adding an `interval` column to the `sites` to the table
    * Spinning up independent looping tasks per site
 - [ ] Dynamic configuration of sites at runtime
 - [ ] An API ...
 - [ ] ... and A fancy web UI
