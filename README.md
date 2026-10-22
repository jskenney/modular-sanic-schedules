# Modular Sanic (Schedules API)

This repo contains the API endpoints necessary to handle current semester course information along with scripts necessary to populate the data in memcache.

In general, a cron job should be use to reload scheduled periodically, and your application can make use of the work here.

# Important Note

This repo includes the API enpoints and methods for caching the information, methods necessary to load course information into MySQL will be up to the end user as schools will have unique schemas and database designs.

# Installing into Modular Sanic

Requires the current [Modular Sanic](https://github.com/jskenney/modular-sanic) (configured with a `.env` file, with memcached and MySQL/MariaDB).

1. Create the tables: `mysql dbname < setup/sched_tables.sql` (this drops existing `sched_*` tables).
2. Load your school's data into the `sched_*` tables (see the note above).
3. Load the tables into memcached with `schedules/start-encache.sh` (from cron, after each load).  The scripts read the database and memcached settings from modular-sanic's `.env`, see [schedules/README](schedules/README).
4. Add the directory holding `api/schedules` to `API_LOCATIONS` in modular-sanic's `.env`, for example `API_LOCATIONS=api/auth/general,...,external/schedules/api/schedules`, and restart the server.
5. Optionally copy `html/start.html` into modular-sanic's HTML directory: it lists the endpoints with links that use your web session.

Every endpoint is a GET under `/sched/<apikey>/...`.  Send the API key in the path or in an `Authorization: Bearer <key>` header; use `-` (or `session`) as `<apikey>` to use the logged on web session instead.  Responses use Modular Sanic's JSON envelope (`success`, `sent`, `endpoint`, `data`, and `error` on failure), with status 401 for an invalid key, 404 when nothing is cached under that name, and 503 when memcached is unavailable.

Behind a reverse proxy (such as modular-sanic-docker's nginx), forward `/sched` to Sanic as well.
