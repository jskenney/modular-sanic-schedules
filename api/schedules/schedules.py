from sanic import Blueprint, response
from sanic_ext import openapi
import asyncio, aiomysql
import time

# Memcache Query Function
async def query_memcache(key, endpoint, request):
    key = key.encode('utf-8')
    data = await request.app.ctx.mc.get(key)
    if data is None:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'data': {}})
    else:
        data = eval(data)
        res = response.json({'success': True,  'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'data': data})
    return res

# Create a sanic api blueprint rooted in /sched
sub_bp = Blueprint("schedules", url_prefix="/")

@sub_bp.route("/<apikey>/sched/school/<schoolid>", methods=['GET'])
@openapi.summary("Provide current semester information")
@openapi.description("returns: {'year': 'XXXX', 'semester': 'XXXX', 'block': 'XXXX'}")
async def schedules_school(request, apikey, schoolid):
    endpoint = '/<apikey>/sched/school/'+schoolid
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'school:'+ schoolid
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route("/<apikey>/sched/room/<roomnum>", methods=['GET'])
@openapi.summary("Provide room utilization")
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
    endpoint = '/<apikey>/sched/room/'+roomnum
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'room:'+ roomnum
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route("/<apikey>/sched/course/<coursenbr>", methods=['GET'], name='sched_course')
@openapi.summary("List instructors and students in a course")
@openapi.description("""returns:
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
}""")
async def schedules_school(request, apikey, coursenbr):
    endpoint = '/<apikey>/sched/course/'+coursenbr
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'course:'+ coursenbr
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route("/<apikey>/sched/course/<coursenbr>/<instructor>", methods=['GET'], name='sched_course_instructor')
@openapi.summary("List students in a course taught by a specific instructor")
@openapi.description("""returns:
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
}""")
async def schedules_school(request, apikey, coursenbr, instructor):
    endpoint = '/<apikey>/sched/course/'+coursenbr+'/'+instructor
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'course:'+ coursenbr +':'+instructor
    res = await query_memcache(key, endpoint, request)
    return res

# # api: /api/sched/student/<username>/[course]
# student:<username> and student:<username>:<course>
@sub_bp.route('/<apikey>/sched/student/<username>', methods=['GET'], name='sched_student')
@openapi.summary("List a students schedule and associated instructors")
@openapi.description("""returns:
{'user': 'XXXX', 'name': 'XXXXX', 'school': 'XXXX'
  'courses': {
    'course##': {'section': XXXX, 'location': 'XXXX', 'time':'XXXX', 'department': 'XXXXX', 'title': 'XXXXX'
      'instructors': {
        'instructorlogin': {'name': 'XXXX', 'pri': 1/0, 'department': 'XXXXX'}
      }
    }
  }
}""")
async def schedule_student(request, apikey, username):
    endpoint = '/<apikey>/sched/student/'+username
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'student:'+ username
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route('/<apikey>/sched/student/<username>/<course>', methods=['GET'], name='sched_student_course')
@openapi.summary("List a students schedule and associated instructors for a specific course")
@openapi.description("""returns:
{'user': 'XXXX', 'name': 'XXXXX', 'school': 'XXXX'
  'courses': {
    'course##': {'section': XXXX, 'location': 'XXXX', 'time':'XXXX', 'department': 'XXXXX', 'title': 'XXXXX'
      'instructors': {
        'instructorlogin': {'name': 'XXXX', 'pri': 1/0, 'department': 'XXXXX'}
      }
    }
  }
}""")
async def schedule_student_course(request, apikey, username, course):
    endpoint = '/<apikey>/sched/student/'+username+'/'+course
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'student:'+ username +':'+course
    res = await query_memcache(key, endpoint, request)
    return res

# # api: /api/sched/instructor/<username>/[course]/[section]
@sub_bp.route('/<apikey>/sched/instructor/<username>', methods=['GET'], name='sched_instructor')
@openapi.summary("List an instructors schedule and associated students")
@openapi.description("""returns:
{'user': 'XXXX', 'name': 'XXXX', 'department': 'XXXX', 'school': 'XXXX', 'year': 'XXXX', 'semester': 'XXXX', 'BLOCK': 'XXXX'
  'courses': {
    'course##': {'department': 'XXXX', 'title': 'XXXX'
      'sections': {'location': 'XXXX', 'time': 'XXXX', 'pri': '1/0',
        'students': {
          'studentlogon': 'studentname'
        }
      }
    }
  }
}""")
async def schedule_instructor(request, apikey, username):
    endpoint = '/<apikey>/sched/instructor/'+username
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'instructor:'+ username
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route('/<apikey>/sched/instructor/<username>/<course>', methods=['GET'], name='sched_instructor_course')
@openapi.summary("List an instructors schedule and associated students for a specific course")
@openapi.description("""returns:
{'user': 'XXXX', 'name': 'XXXX', 'department': 'XXXX', 'school': 'XXXX', 'year': 'XXXX', 'semester': 'XXXX', 'BLOCK': 'XXXX'
  'courses': {
    'course##': {'department': 'XXXX', 'title': 'XXXX'
      'sections': {'location': 'XXXX', 'time': 'XXXX', 'pri': '1/0',
        'students': {
          'studentlogon': 'studentname'
        }
      }
    }
  }
}""")
async def schedule_instructor_course(request, apikey, username, course):
    endpoint = '/<apikey>/sched/instructor/'+username+'/'+course
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'instructor:'+ username + ':' + course
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route('/<apikey>/sched/instructor/<username>/<course>/<section>', methods=['GET'], name='sched_instructor_course_section')
@openapi.summary("List an instructors schedule and associated students for a specific section")
@openapi.description("""returns:
{'user': 'XXXX', 'name': 'XXXX', 'department': 'XXXX', 'school': 'XXXX', 'year': 'XXXX', 'semester': 'XXXX', 'BLOCK': 'XXXX'
  'courses': {
    'course##': {'department': 'XXXX', 'title': 'XXXX'
      'sections': {'location': 'XXXX', 'time': 'XXXX', 'pri': '1/0',
        'students': {
          'studentlogon': 'studentname'
        }
      }
    }
  }
}""")
async def schedule_instructor_course(request, apikey, username, course, section):
    endpoint = '/<apikey>/sched/instructor/'+username+'/'+course+'/'+section
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'instructor:'+ username + ':' + course +':' + section
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route('/<apikey>/sched/department/instructor/<school>', methods=['GET'], name='schedule_department_instructor')
@openapi.summary("List all instructors at a school")
@openapi.description("""returns: {
    "departmentName": {
      "instructorlogin": {
        "name": "XXXX",
        "school": "XXXX"
      }, """)
async def schedule_department_instructor(request, apikey, school):
    endpoint = '/<apikey>/sched/department/instructor/'+school
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'department:instructors:'+school
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route('/<apikey>/sched/department/<school>', methods=['GET'], name='schedule_department')
@openapi.summary("List all departments at a school")
@openapi.description("""returns: ["DEPT1", "DEPT2", ...] """)
async def schedule_department(request, apikey, school):
    endpoint = '/<apikey>/sched/department/'+school
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'department:'+school
    key = key.encode('utf-8')
    data = await request.app.ctx.mc.get(key)
    if data is None:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'data': []})
    else:
        data = eval(data)
        res = response.json({'success': True,  'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'data': data})
    return res
