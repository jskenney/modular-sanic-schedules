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

@sub_bp.route("/sched/<apikey>/school/<schoolid>", methods=['GET'])
@openapi.summary("Retrieve current semester information")
@openapi.description("returns: {'year': 'XXXX', 'semester': 'XXXX', 'block': 'XXXX'}")
async def schedules_school(request, apikey, schoolid):
    endpoint = '/sched/<apikey>/school/'+schoolid
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'school:'+ schoolid
    res = await query_memcache(key, endpoint, request)
    return res

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
    endpoint = '/sched/<apikey>/room/'+roomnum
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'room:'+ roomnum
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route("/sched/<apikey>/course/<coursenbr>", methods=['GET'], name='sched_course')
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
    endpoint = '/sched/<apikey>/course/'+coursenbr
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'course:'+ coursenbr
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route("/sched/<apikey>/course/<coursenbr>/<instructor>", methods=['GET'], name='sched_course_instructor')
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
    endpoint = '/sched/<apikey>/course/'+coursenbr+'/'+instructor
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'course:'+ coursenbr +':'+instructor
    res = await query_memcache(key, endpoint, request)
    return res

# # api: /api/sched/user
@sub_bp.route('/sched/<apikey>/user', methods=['GET'], name='sched_user_direct')
@openapi.summary("List specific student/instructor schedule with associated instructor information")
@openapi.description("""returns:
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
}""")
async def schedule_user_direct(request, apikey):
    endpoint = '/sched/<apikey>/user'
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'user:'+ rusername
    res = await query_memcache(key, endpoint, request)
    return res

# # api: /api/sched/student/<username>/[course]
# student:<username> and student:<username>:<course>
@sub_bp.route('/sched/<apikey>/student/<username>', methods=['GET'], name='sched_student')
@openapi.summary("List specific student schedule with associated instructor information")
@openapi.description("""returns:
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
}""")
async def schedule_student(request, apikey, username):
    endpoint = '/sched/<apikey>/student/'+username
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'student:'+ username
    res = await query_memcache(key, endpoint, request)
    return res

# # api: /api/sched/student/<username>/[course]
# student:<username> and student:<username>:<course>
@sub_bp.route('/sched/<apikey>/student', methods=['GET'], name='sched_student_direct')
@openapi.summary("List specific student schedule with associated instructor information")
@openapi.description("""returns:
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
}""")
async def schedule_student_direct(request, apikey):
    endpoint = '/sched/<apikey>/student'
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'student:'+ rusername
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route('/sched/<apikey>/student/<username>/<course>', methods=['GET'], name='sched_student_course')
@openapi.summary("List specific student schedule with associated instructor information for a specific course")
@openapi.description("""returns:
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
}""")
async def schedule_student_course(request, apikey, username, course):
    endpoint = '/sched/<apikey>/student/'+username+'/'+course
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'student:'+ username +':'+course
    res = await query_memcache(key, endpoint, request)
    return res

# # api: /api/sched/instructor/<username>/[course]/[section]
@sub_bp.route('/sched/<apikey>/instructor/<username>', methods=['GET'], name='sched_instructor')
@openapi.summary("List an instructors schedule with associated students")
@openapi.description("""returns:
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
}""")
async def schedule_instructor(request, apikey, username):
    endpoint = '/sched/<apikey>/instructor/'+username
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'instructor:'+ username
    res = await query_memcache(key, endpoint, request)
    return res

# # api: /api/sched/instructor/<username>/[course]/[section]
@sub_bp.route('/sched/<apikey>/instructor', methods=['GET'], name='sched_instructor_direct')
@openapi.summary("List an instructors schedule with associated students")
@openapi.description("""returns:
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
}""")
async def schedule_instructor_direct(request, apikey):
    endpoint = '/sched/<apikey>/instructor/'
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'instructor:'+ rusername
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route('/sched/<apikey>/instructor/<username>/<course>', methods=['GET'], name='sched_instructor_course')
@openapi.summary("List an instructors schedule with associated students for a specific course")
@openapi.description("""returns:
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
}""")
async def schedule_instructor_course(request, apikey, username, course):
    endpoint = '/sched/<apikey>/instructor/'+username+'/'+course
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'instructor:'+ username + ':' + course
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route('/sched/<apikey>/instructor/<username>/<course>/<section>', methods=['GET'], name='sched_instructor_course_section')
@openapi.summary("List an instructors schedule with associated students for a specific section")
@openapi.description("""returns:
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
}""")
async def schedule_instructor_course(request, apikey, username, course, section):
    endpoint = '/sched/<apikey>/instructor/'+username+'/'+course+'/'+section
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'instructor:'+ username + ':' + course +':' + section
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route('/sched/<apikey>/department/instructor/<school>', methods=['GET'], name='schedule_department_instructor')
@openapi.summary("List all instructors within a school")
@openapi.description("""returns: {
    "departmentName": {
      "instructorlogin": {
        "name": "XXXX",
        "school": "XXXX"
      }, """)
async def schedule_department_instructor(request, apikey, school):
    endpoint = '/sched/<apikey>/department/instructor/'+school
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'department:instructors:'+school
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route('/sched/<apikey>/department/instructor/<school>/<department>', methods=['GET'], name='schedule_department_instructor_department')
@openapi.summary("List all instructors within a school's department")
@openapi.description("""returns: {
    "departmentName": {
      "instructorlogin": {
        "name": "XXXX",
        "school": "XXXX"
      }, """)
async def schedule_department_instructor_department(request, apikey, school, department):
    endpoint = '/sched/<apikey>/department/instructor/'+school+'/'+department.lower().replace(' ','_').replace('%20', '_')
    ok, rusername, rapikey, access, info = await request.app.ctx.auth.verifyapi(request, apikey)
    if not ok:
        res = response.json({'success': False, 'sent': time.asctime(time.localtime(time.time())), 'endpoint':endpoint, 'message': 'Invalid API Key', 'data': {}})
        return res
    key = 'department:instructors:'+school+':'+department.lower().replace(' ','_').replace('%20', '_')
    res = await query_memcache(key, endpoint, request)
    return res

@sub_bp.route('/sched/<apikey>/department/<school>', methods=['GET'], name='schedule_department')
@openapi.summary("List all departments within a school")
@openapi.description("""returns: ["DEPT1", "DEPT2", ...] """)
async def schedule_department(request, apikey, school):
    endpoint = '/sched/<apikey>/department/'+school
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
