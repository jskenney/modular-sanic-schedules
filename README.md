# Modular Sanic (Schedules API)

This repo contains the API endpoints necessary to handle current semester course information along with scripts necessary to populate the data in memcache.

In general, a cron job should be use to reload scheduled periodically, and your application can make use of the work here.

# Important Note

This repo includes the API enpoints and methods for caching the information, methods necessary to load course information into MySQL will be up to the end user as schools will have unique schemas and database designs.
