from sanic import Blueprint, response
from sanic_ext import openapi
from datetime import datetime, timezone
import ast, json, re

# Schedule data is loaded into memcached by schedules/memcached-build.py (as
# JSON) and only read here.  Every endpoint takes an API key in the path (or
# an Authorization: Bearer header); a key of '-' or 'session' uses the web
# session instead.

# memcached keys cannot hold whitespace or control characters, and are at
# most 250 bytes; anything else cannot be cached, so it is not found
VALID_KEY = re.compile(r'[^\s\x00-\x1f\x7f]+')

# The standard JSON envelope, with the API key masked in 'endpoint'
def respond(endpoint, success, data, status=200, error=None):
    body = {'success': success, 'sent': datetime.now(timezone.utc).isoformat(), 'endpoint': endpoint, 'data': data}
    if error:
        body['error'] = error
    return response.json(body, status=status)

def decode(data):
    try:
        return json.loads(data)
    except ValueError:
        # Written by memcached-build.py before values were stored as JSON;
        # literal_eval only accepts Python literals (rerun start-encache.sh)
        return ast.literal_eval(data.decode('utf-8'))

# Verify the API key (or session), then return the cached value for key.
# key may be a function of the verified user name (for the "my schedule" routes).
async def query_memcache(request, apikey, endpoint, key, empty=None):
    empty = {} if empty is None else empty
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        return respond(endpoint, False, empty, status=401, error='Invalid API Key')
    if callable(key):
        key = key(rusername)
    if not request.app.config.MEMCACHEAVAIL:
        return respond(endpoint, False, empty, status=503, error='The schedule cache is unavailable.')
    if not VALID_KEY.fullmatch(key) or len(key.encode('utf-8')) > 250:
        return respond(endpoint, False, empty, status=404, error='Not found.')
    try:
        data = await request.app.ctx.mc.get(key.encode('utf-8'))
    except Exception:
        return respond(endpoint, False, empty, status=503, error='The schedule cache is unavailable.')
    if data is None:
        return respond(endpoint, False, empty, status=404, error='Not found.')
    try:
        data = decode(data)
    except (ValueError, TypeError, SyntaxError, RecursionError, UnicodeDecodeError):
        return respond(endpoint, False, empty, status=500, error='The cached value could not be read.')
    return respond(endpoint, True, data)

# Create a sanic api blueprint rooted in /sched
sub_bp = Blueprint("schedules", url_prefix="/")

SCHEDULE = """returns:
{'user': 'XXXX', 'name': 'XXXXX', 'school': 'XXXX', 'type': 'student/instructor', 'department': 'XXXXX',
  'courses': {
    'course##': {'section': XXXX, 'location': 'XXXX', 'time':'XXXX', 'department': 'XXXXX', 'title': 'XXXXX'
      'instructors': {
        'instructorlogin': {'name': 'XXXX', 'pri': 1/0, 'department': 'XXXXX'}
      },
      'students': {
        'studentlogin': 'name'
      }
    }
  }
}"""

COURSE = """returns:
{'school': 'XXXX', 'course': 'XXXX', 'title': 'XXXX', 'department': 'XXXX', 'year': 'XXXX', 'semester': 'XXXX', 'BLOCK': 'XXXX'
  'sections': {
    'section##': {'location': 'XXXX', 'time': 'XXXX',
                  'instructors': {
                      'instlogin': {'name': 'XXXX', 'department': 'XXXX', 'pri': '1/0'}
                  },
                  'students': {
                      'midnlogin': {'name': 'XXXX'}
                  }
   }
}"""

DEPARTMENT_INSTRUCTORS = """returns: {
    "departmentName": {
      "instructorlogin": {
        "name": "XXXX",
        "school": "XXXX"
      }, """

@sub_bp.route("/sched/<apikey>/school/<schoolid>", methods=['GET'])
@openapi.summary("Retrieve current semester information")
@openapi.description("returns: {'year': 'XXXX', 'semester': 'XXXX', 'block': 'XXXX'}")
async def schedules_school(request, apikey, schoolid):
    return await query_memcache(request, apikey, '/sched/<apikey>/school/'+schoolid, 'school:'+schoolid)

@sub_bp.route("/sched/<apikey>/room/<roomnum>", methods=['GET'])
@openapi.summary("Retrieve room utilization")
@openapi.description("""returns:
{
    "dayofweek": {
      "period": {
        "school": "XXXX",
        "course": "XXXX",
        "section": "XXXX",
        "title": "XXXX",
        "department": "XXXX",
        "instructors": {
          "INSTNAME": {
            "department": "XXXX",
            "name": "XXXX",
            "pri": "1/0"
          }
        }
    }
  }
}
""")
async def schedules_room(request, apikey, roomnum):
    return await query_memcache(request, apikey, '/sched/<apikey>/room/'+roomnum, 'room:'+roomnum)

@sub_bp.route("/sched/<apikey>/course/<coursenbr>", methods=['GET'], name='sched_course')
@openapi.summary("List instructors and students in a course")
@openapi.description(COURSE)
async def schedules_course(request, apikey, coursenbr):
    return await query_memcache(request, apikey, '/sched/<apikey>/course/'+coursenbr, 'course:'+coursenbr)

@sub_bp.route("/sched/<apikey>/course/<coursenbr>/<instructor>", methods=['GET'], name='sched_course_instructor')
@openapi.summary("List students in a course taught by a specific instructor")
@openapi.description(COURSE)
async def schedules_course_instructor(request, apikey, coursenbr, instructor):
    return await query_memcache(request, apikey, '/sched/<apikey>/course/'+coursenbr+'/'+instructor,
                                'course:'+coursenbr+':'+instructor)

# # api: /api/sched/user
@sub_bp.route('/sched/<apikey>/user', methods=['GET'], name='sched_user_direct')
@openapi.summary("List specific student/instructor schedule with associated instructor information")
@openapi.description(SCHEDULE)
async def schedule_user_direct(request, apikey):
    return await query_memcache(request, apikey, '/sched/<apikey>/user', lambda user: 'user:'+user)

# # api: /api/sched/user
@sub_bp.route('/sched/<apikey>/user/<user>', methods=['GET'], name='sched_user_direct_byname')
@openapi.summary("List specific student/instructor schedule with associated instructor information")
@openapi.description(SCHEDULE)
async def schedule_user_direct_byname(request, apikey, user):
    return await query_memcache(request, apikey, '/sched/<apikey>/user/'+user, 'user:'+user)

# # api: /api/sched/student/<username>/[course]
# student:<username> and student:<username>:<course>
@sub_bp.route('/sched/<apikey>/student/<username>', methods=['GET'], name='sched_student')
@openapi.summary("List specific student schedule with associated instructor information")
@openapi.description(SCHEDULE)
async def schedule_student(request, apikey, username):
    return await query_memcache(request, apikey, '/sched/<apikey>/student/'+username, 'student:'+username)

@sub_bp.route('/sched/<apikey>/student', methods=['GET'], name='sched_student_direct')
@openapi.summary("List specific student schedule with associated instructor information")
@openapi.description(SCHEDULE)
async def schedule_student_direct(request, apikey):
    return await query_memcache(request, apikey, '/sched/<apikey>/student', lambda user: 'student:'+user)

@sub_bp.route('/sched/<apikey>/student/<username>/<course>', methods=['GET'], name='sched_student_course')
@openapi.summary("List specific student schedule with associated instructor information for a specific course")
@openapi.description(SCHEDULE)
async def schedule_student_course(request, apikey, username, course):
    return await query_memcache(request, apikey, '/sched/<apikey>/student/'+username+'/'+course,
                                'student:'+username+':'+course)

# # api: /api/sched/instructor/<username>/[course]/[section]
@sub_bp.route('/sched/<apikey>/instructor/<username>', methods=['GET'], name='sched_instructor')
@openapi.summary("List an instructors schedule with associated students")
@openapi.description(SCHEDULE)
async def schedule_instructor(request, apikey, username):
    return await query_memcache(request, apikey, '/sched/<apikey>/instructor/'+username, 'instructor:'+username)

@sub_bp.route('/sched/<apikey>/instructor', methods=['GET'], name='sched_instructor_direct')
@openapi.summary("List an instructors schedule with associated students")
@openapi.description(SCHEDULE)
async def schedule_instructor_direct(request, apikey):
    return await query_memcache(request, apikey, '/sched/<apikey>/instructor/', lambda user: 'instructor:'+user)

@sub_bp.route('/sched/<apikey>/instructor/<username>/<course>', methods=['GET'], name='sched_instructor_course')
@openapi.summary("List an instructors schedule with associated students for a specific course")
@openapi.description(SCHEDULE)
async def schedule_instructor_course(request, apikey, username, course):
    return await query_memcache(request, apikey, '/sched/<apikey>/instructor/'+username+'/'+course,
                                'instructor:'+username+':'+course)

@sub_bp.route('/sched/<apikey>/instructor/<username>/<course>/<section>', methods=['GET'], name='sched_instructor_course_section')
@openapi.summary("List an instructors schedule with associated students for a specific section")
@openapi.description(SCHEDULE)
async def schedule_instructor_course_section(request, apikey, username, course, section):
    return await query_memcache(request, apikey, '/sched/<apikey>/instructor/'+username+'/'+course+'/'+section,
                                'instructor:'+username+':'+course+':'+section)

@sub_bp.route('/sched/<apikey>/department/instructor/<school>', methods=['GET'], name='schedule_department_instructor')
@openapi.summary("List all instructors within a school")
@openapi.description(DEPARTMENT_INSTRUCTORS)
async def schedule_department_instructor(request, apikey, school):
    return await query_memcache(request, apikey, '/sched/<apikey>/department/instructor/'+school,
                                'department:instructors:'+school)

@sub_bp.route('/sched/<apikey>/department/instructor/<school>/<department>', methods=['GET'], name='schedule_department_instructor_department')
@openapi.summary("List all instructors within a school's department")
@openapi.description(DEPARTMENT_INSTRUCTORS)
async def schedule_department_instructor_department(request, apikey, school, department):
    department = department.lower().replace(' ','_').replace('%20', '_')
    return await query_memcache(request, apikey, '/sched/<apikey>/department/instructor/'+school+'/'+department,
                                'department:instructors:'+school+':'+department)

@sub_bp.route('/sched/<apikey>/department/<school>', methods=['GET'], name='schedule_department')
@openapi.summary("List all departments within a school")
@openapi.description("""returns: ["DEPT1", "DEPT2", ...] """)
async def schedule_department(request, apikey, school):
    return await query_memcache(request, apikey, '/sched/<apikey>/department/'+school, 'department:'+school, empty=[])
