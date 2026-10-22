# modular-sanic-schedules: Repository Review

Reviewed: `main` at `d5e353c` (2026-10-22), against the current Modular Sanic (`main` at `c347e8d`: sanic-session v0.10.0, `.env` configuration, hashed API keys).

This review covers bugs, likely runtime errors, security, design and performance. Each finding is tagged:

- **[verified]**: reproduced with modular-sanic `main`, MariaDB and memcached, using a small schedule plus a synthetic one with 1,500 students.
- **[measured]**: has numbers.
- **[reasoned]**: from reading the code.

**Everything needed to run on the current framework is fixed on branch `framework-update`, in its PR.** The table in §4 says which findings that PR covers; the rest are recommendations.

## 1. What the repository does

```
sched_* tables (MySQL)  --schedules/memcached-build.py-->  memcached keys  --api/schedules/schedules.py-->  GET /sched/<apikey>/...
  (loaded by a site-specific script,                        school:, student:, instructor:,
   e.g. modular-sanic-usna)                                 user:, course:, room:, department:
```

- **`setup/sched_tables.sql`:** seven `sched_*` tables (school, course, student, instructor, section, section instructors, enrolment).
- **`schedules/memcached-build.py`:** run from cron (`start-encache.sh`). It reads the tables through `db6.py`, builds one JSON-like document per student, instructor, course, room and department, and writes it to memcached with no expiry. `start-decache.sh` removes them again by re-running the builder without its `mcache.set` lines.
- **`api/schedules/schedules.py`:** 16 GET endpoints. Each checks the API key with `auth.verifyapi` and returns one memcached value.
- **`html/start.html`:** a page listing the endpoints.

## 2. Checks run

| Check | Result |
|---|---|
| Original `memcached-build.py` on the current stack | **Fails:** `ModuleNotFoundError: No module named 'config'`. With a `config.py` added it then fails with `No module named 'MySQLdb'`, because the framework no longer installs mysqlclient or mysql-connector [verified]. |
| Original API on modular-sanic `main` | **Fails to load:** `from sanic_ext import openapi` raises `ModuleNotFoundError: pydantic`. The framework's last batch removed `pydantic`, which sanic-ext needs without declaring it. That is fixed in modular-sanic by **restore-pydantic**, which brings `/docs` back too [verified]. With pydantic, the API loads and serves the old-format values. |
| `framework-update` branch: the scripts plus the API on modular-sanic `main` | **Builder:** loads 41 keys from the sample tables, and `start-decache.sh` removes them. **API probe: 32/32 checks** (with the modular-sanic-usna checks): <ul><li>Bearer key, key in the path, and the web session (`-`);</li><li>401, 404 and 503 responses;</li><li>keys memcached can't hold;</li><li>old-format values;</li><li>an `eval` payload is not run.</li></ul> |
| Builder cost, synthetic 1,500 students / 60 instructors / 150 sections | **9,574 queries, 9.6 s** [measured]. |
| `ruff --select E9,F` | Clean. |

## 3. Findings

### CRITICAL

#### C-1. The API runs whatever is stored in memcached (`eval`) **[verified]**

`api/schedules/schedules.py:13,397` call `eval(data)` on every value read from memcached. The builder stores Python `repr()` strings, because pymemcache stores `str(dict)` when it has no serializer.

memcached has no authentication. It is shared with the framework's sessions, and anything that can reach port 11211 can write a key. That includes any process on the host, or any container on the Docker network.

Once someone writes, for example, `school:X` = `__import__('os').system('...')`, the next `GET /sched/<key>/school/X` runs it inside the API server, with its database credentials.

Reproduced on the original code: storing `__import__('os').system('touch /tmp/sched-pwned-old')` under `school:EVIL` and requesting `/sched/x/school/EVIL` created the file (and returned 200).

**Fixed in the PR:**
- the builder stores JSON;
- the API reads it with `json.loads`, falling back to `ast.literal_eval` only for values the old builder cached;
- a value that is neither gives a JSON 500.

The probe stores an `os.system` payload and checks that it doesn't run.

### HIGH

#### H-1. Any API key can read every student's schedule, every course roster and every instructor's sections **[verified]**

Every endpoint only checks that the key is valid. Any logged-on user can therefore read:
- any student's courses, sections, rooms and times (`/student/<user>`, `/user/<user>`);
- the full student roster, with names, of every course and section;
- every instructor's schedule.

Student schedules and rosters are education records. At most schools only the student, their instructors and staff with a need should see them.

**Fix:** decide who may see what, then check it with the access the framework already provides (`access` from `verifyapi`). For example:
- the `/user`, `/student` and `/instructor` routes without a name return the caller's own data;
- `sched/read` access is needed for other people's schedules and rosters;
- instructors get their own sections' rosters.

The PR doesn't change this, because it is a policy decision.

#### H-2. Doesn't run on the current framework **[verified]**

| Old dependency | Status on the current framework |
|---|---|
| `config.py` | Gone; settings are in `.env`. |
| `mysql.connector` / `MySQLdb` | Not installed any more. |
| `uikit` assets (`html/start.html`) | Not shipped any more. |
| `/auth/logon/*.html` pages | Moved to `/logon/`. |
| API key shown by `/auth/key` | Keys are hashed, so it can't be shown any more. |

The API also needs sanic-ext (pydantic, see §2).

**Fixed in the PR:**
- `sanic_env.py` reads modular-sanic's `.env`;
- `db6.py` uses PyMySQL;
- the shell scripts run from any directory, with `VENV`;
- `start.html` updated;
- README install steps.

#### H-3. Data removed from the tables stays in memcached for ever **[reasoned]**

The builder writes each key with no expiry. It only deletes and rewrites the keys for rows that are **still** in the tables. When a student drops a course, a section is cancelled, or a semester ends, the old keys keep serving the old data indefinitely: `student:<user>:<course>`, `course:<course>:<instructor>`, `room:<room>`, and a whole `student:<user>` for someone no longer enrolled. `start-decache.sh` has the same blind spot.

**Fix:** pick one:
- write every key with an expiry a little longer than the cron interval (for example 2 × interval), so anything not rewritten disappears;
- write under a versioned prefix (`sched:<n>:...`) and switch a `sched:current` pointer once the build is complete;
- record the key list of each build, and delete the previous build's leftovers.

The second also removes the window between `delete` and `set`, where the API returns 404 for data that exists.

#### H-4. Keys collide: a course, student or instructor named like a school overwrites, or is overwritten by, the school list **[reasoned]**

These pairs share key spaces:

| Per-school list | Per-item key |
|---|---|
| `course:<school>` (course list) | `course:<course>` |
| `student:<school>` | `student:<user>` |
| `instructor:<school>` | `instructor:<user>` |

Whichever is written last wins. `start.html` even documents `/course/<schoolname>` and `/student/<schoolname>`, which are the same routes as a course or student lookup.

Separately, `user:<username>:<course>` is written for both students and instructors.

**Fix:** give the lists their own prefix (for example `courses:<school>`, `students:<school>`, `instructors:<school>`) and their own routes.

### MEDIUM

#### M-1. The room builder crashes on real data and misfiles multi-period meetings **[verified]**

`memcached-build.py`, the room section:
- `mtg[i]` assumes `location` and `time` list the same number of entries. A section with more rooms than meeting times raises `IndexError` and **aborts the rest of the build** (departments, course lists, student lists) [verified].
- `period = thismtg[-1]` and `for dow in thismtg[:-1]` treat every character but the last as a day. `T34` (Tuesday, periods 3 and 4) is stored under day `"3"` period `4`, and period 3 is lost [verified].
- The `'None'` check only works because `db6` turns NULL into the string `'None'`.

**Fix:** parse meeting times with a real pattern, such as days `[MTWRFSU]+` followed by digits. Skip and log rows whose room and time counts differ instead of crashing.

#### M-2. Builder performance: one query per student, per course and per section **[measured]**

For each student, the builder makes 1 query plus 1 per course. For each instructor it makes 2 per section. For each course it queries every section once per instructor, so team-taught sections are read repeatedly.

The synthetic 1,500 students / 150 sections made **9,574 queries in 9.6 s**. At USNA's size (about 4,500 midshipmen plus NAPS, about 1,500 sections) that is roughly 30,000 to 40,000 queries.

`sched_semester` has no index on `student`, and `sched_section_instructors` none on `instructor` (M-4), so each of those lookups scans the table, and the total grows quadratically.

**Fix:** read the six tables once (six queries) into dictionaries, and build every document in memory. That takes seconds at any realistic size.

#### M-3. Failures are invisible to cron **[reasoned]**

- **Database errors:** these are printed as `DEBUG:` and the build continues, writing partial documents.
- **memcached write errors:** pymemcache's default `noreply=True` means a failed `set` (for example a value over memcached's item size limit) isn't reported at all.
- **Exit status:** the script exits 0 whatever happened.

**Fix:**
- stop on the first database error;
- use `noreply=False` (or check `set` results);
- exit non-zero, so cron mails someone.

#### M-4. Schema: `setup/sched_tables.sql` drops the tables, has no secondary indexes, and compares user names case-insensitively **[reasoned]**

- **Destructive re-run:** re-running setup deletes all schedule data (`DROP TABLE IF EXISTS` first).
- **No indexes for the builder's lookups:** it queries by `sched_semester.student` and `sched_section_instructors.instructor` (M-2).
- **Case mismatch:** user columns use the default (case-insensitive) collation, while the framework's `sanic_info.user` is case-sensitive (`utf8mb4_bin`). So `M261234` and `m261234` are one student here and two users there.

**Fix:**
- `CREATE TABLE IF NOT EXISTS`, plus a separate reset file (as modular-sanic does);
- `KEY (school, student)` and `KEY (school, instructor)`;
- `utf8mb4_bin` on user columns.

#### M-5. Error responses and status codes didn't follow the framework **[verified]**

Every failure returned 200 with `success: false` and a `message` field. A key memcached can't hold (a space, or over 250 bytes) raised `ValidationException`, which gives the framework's HTML 500 page. With no memcached, `request.app.ctx.mc` doesn't exist (`AttributeError`, 500).

**Fixed in the PR:**
- the framework's envelope (`error`, an ISO `sent` time), with the key still masked in `endpoint`;
- 401 for an invalid key, 404 for nothing cached, 503 for memcached unavailable;
- 404 for keys memcached can't hold;
- duplicate handler names (three `schedules_school`, two `schedule_instructor_course`) removed.

#### M-6. `/sched` isn't reachable behind modular-sanic-docker **[reasoned]**

The Docker stack's nginx forwards only `/api`, `/auth` and `/docs` to Sanic, so every `/sched/...` request gets nginx's 404.

**Fix:** forward `/sched` in modular-sanic-docker's `default.conf` (that repo's open M-5), or move the routes under `/api/sched`. The PR's README notes it.

### LOW

| ID | Where | Issue | Fix |
|---|---|---|---|
| L-1 | `schedules/db6.py` | A general-purpose "GRADING" helper library. Unused helpers build SQL by string concatenation (`SHOW FIELDS IN `+table). `print_results_bycols` calls `str(...).string()` (AttributeError). `row_to_dict` turns every value into a string, so the API returns `pri: "1"`, `"None"` for missing rooms, and so on. | Keep `query`/`query_dict` only. Return real types and `null` once consumers are ready (the PR keeps strings for compatibility). |
| L-2 | `start-decache.sh` | Purges by deleting every line containing `mcache.set` from a copy of the builder. A `set` call split over two lines, or any other line mentioning it, breaks the purge script. `DEBUG_ALLOW` does nothing. | A `--purge` flag in the builder (or H-3's versioned keys). |
| L-3 | `api/schedules/schedules.py` | Department names are matched as `lower()` with spaces replaced by `_`, and a literal `%20` replaced too (Sanic already decodes paths). Two departments differing only in case or `_`/space collide. | Key departments by a code, or by the exact name, URL-encoded. |
| L-4 | `html/start.html` | Inserted the `/auth/key` JSON with `innerHTML`, so user data containing HTML would run there. It also rewrote links with the API key, which is no longer returned. | **Fixed in the PR:** `textContent`; the examples use `-` (the web session). |
| L-5 | OpenAPI descriptions | The documented shapes don't match the data. Examples: `BLOCK` vs `block`; `students` shown as objects but stored as `{login: name}`; course `sections` missing from the user schedule. | Generate the descriptions from one example per document type. |
| L-6 | `.gitignore` | Generic; doesn't ignore `config.py`, `.env` or `memcached-purge.py` (written next to the scripts). | Add them. |

## 4. Prioritized top 10

| # | Item | Action | In the PR |
|---|---|---|---|
| 1 | C-1 | Stop `eval`-ing memcached values. | **fixed** |
| 2 | H-2 | Run on the current framework: `.env`, PyMySQL, sanic-ext. | **fixed** (plus modular-sanic restore-pydantic) |
| 3 | H-1 | Decide and enforce who may read whose schedule and rosters. | open, policy |
| 4 | H-3 | Make stale data expire: expiry or versioned keys. | open |
| 5 | H-4 | Separate the per-school list keys from the per-item keys. | open |
| 6 | M-1 | Fix the room parser crash and the multi-period parsing. | open |
| 7 | M-3 | Fail loudly: stop on errors, check writes, exit non-zero. | open |
| 8 | M-2, M-4 | Build in memory from six queries; add indexes; case-sensitive user columns. | open |
| 9 | M-5 | Framework envelope and status codes; JSON errors. | **fixed** |
| 10 | M-6 | Forward `/sched` in modular-sanic-docker's nginx. | documented |
