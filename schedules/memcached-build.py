DEBUG_ALLOW = True

from config import db_settings, memcached_settings
import os, time, sys, json, copy

###############################################################################
from db6 import db as mysql
print(time.asctime(time.localtime(time.time())), "Connected to MySQL")

###############################################################################
from pymemcache.client import base as mcachesrv
mcache = mcachesrv.Client((memcached_settings['MEMCACHED_SERVER'], memcached_settings['MEMCACHED_PORT']))
print(time.asctime(time.localtime(time.time())), "Connected to MemCached")

###############################################################################
# Delete MemCached Schedules
print(time.asctime(time.localtime(time.time())), 'Processing Schedule Data to populate and clean MemCached')

###############################################################################
print(time.asctime(time.localtime(time.time())), 'Processing school:<schoolid>')
# api:  /semester/<school>
# returns: {'year': 'XXXX', 'semester': 'XXXX', 'block': 'XXXX'}
SCHOOL_INFO = {}
query = 'SELECT * FROM sched_current'
data, error, warning = mysql.query_dict(query)
if error != '' or warning is not None:
    print(' -', ['DEBUG:', error, warning])
for row in data:
    key = 'school:'+row['school']
    value = {'year': row['year'], 'semester': row['semester'], 'block': row['block']}
    mcache.delete(key)
    mcache.set(key, value)
    SCHOOL_INFO[row['school']] = value

###############################################################################
print(time.asctime(time.localtime(time.time())), 'Processing student:<username> and student:<username>:<course>')
# api: /student/<username>/[course]
# returns:
# {'user': 'XXXX', 'name': 'XXXXX', 'school': 'XXXX'
#   'courses': {
#     'course##': {'section': XXXX, 'location': 'XXXX', 'time':'XXXX', 'department': 'XXXXX', 'title': 'XXXXX'
#       'instructors': {
#         'instructorlogin': {'name': 'XXXX', 'pri': 1/0, 'department': 'XXXXX'}
#       }
#     }
#   }
# }
if DEBUG_ALLOW:
    query = 'SELECT * FROM sched_student'
    data, error, warning = mysql.query_dict(query)
    if error != '' or warning is not None:
        print(' -', ['DEBUG:', error, warning])
    for row in data:
        school = row['school']
        username = row['student']
        key = 'student:'+username
        name = row['name']
        results = {'user': username,
                   'name': name,
                   'school': school,
                   'year': SCHOOL_INFO[school]['year'], 'semester': SCHOOL_INFO[school]['semester'], 'block': SCHOOL_INFO[school]['block'],
                   'courses':{}}
        query = 'SELECT course, section, location, time, department, title FROM sched_semester LEFT JOIN sched_section USING (school, course, section) LEFT JOIN sched_course USING (school, course) WHERE student=%s'
        values = (username,)
        sdata, error, warning = mysql.query_dict(query, values)
        if error != '' or warning is not None:
            print(' -', ['DEBUG:', error, warning])
        for srow in sdata:
            course = srow['course']
            section = srow['section']
            del(srow['course'])
            srow['instructors'] = {}
            results['courses'][course] = srow
            iquery = 'SELECT instructor, name, department, pri FROM sched_section_instructors LEFT JOIN sched_instructor USING (school, instructor) WHERE course = %s AND section = %s AND school = %s'
            ivalues = (course, section, school, )
            idata, error, warning = mysql.query_dict(iquery, ivalues)
            if error != '' or warning is not None:
                print(' -', ['DEBUG:', error, warning])
            for irow in idata:
                instructor = irow['instructor']
                del(irow['instructor'])
                srow['instructors'][instructor] = irow
            results['courses'][course] = srow
        mcache.delete(key)
        mcache.set(key, results)
        for c in results['courses']:
            nresults = {'user': username, 'name': name, 'school': school, 'year': SCHOOL_INFO[school]['year'], 'semester': SCHOOL_INFO[school]['semester'], 'block': SCHOOL_INFO[school]['block'], 'courses': {}}
            nresults['courses'][c] = results['courses'][c]
            nkey = 'student:'+username+':'+c
            mcache.delete(nkey)
            mcache.set(nkey, nresults)

###############################################################################
print(time.asctime(time.localtime(time.time())), 'Processing instructor:<username>, instructor:<username>:<course>, and instructor:<username>:<course>:<section>')
# api: /instructor/<username>/[course]/[section]
# returns:
# {'user': 'XXXX', 'name': 'XXXX', 'department': 'XXXX', 'school': 'XXXX', 'year': 'XXXX', 'semester': 'XXXX', 'BLOCK': 'XXXX'
#   'courses': {
#     'course##': {'department': 'XXXX', 'title': 'XXXX'
#       'sections': {'location': 'XXXX', 'time': 'XXXX', 'pri': '1/0',
#         'students': {
#           'studentlogon': 'studentname'
#         }
#       }
#     }
#   }
# }
if DEBUG_ALLOW:
    query = 'SELECT * FROM sched_instructor'
    data, error, warning = mysql.query_dict(query)
    if error != '' or warning is not None:
        print(' -', ['DEBUG:', error, warning])
    for row in data:
        school = row['school']
        key = 'instructor:'+row['instructor']
        results = {'user': row['instructor'],
                   'name': row['name'],
                   'department': row['department'],
                   'school': row['school'],
                   'year': SCHOOL_INFO[school]['year'], 'semester': SCHOOL_INFO[school]['semester'], 'block': SCHOOL_INFO[school]['block'],
                   'courses': {}
                  }
        query = 'SELECT course, section, pri, title, department, location, time FROM sched_section_instructors LEFT JOIN sched_course USING (school, course) LEFT JOIN sched_section USING (school, course, section) WHERE instructor=%s'
        values = (row['instructor'],)
        sdata, error, warning = mysql.query_dict(query, values)
        for srow in sdata:
            course = srow['course']
            section = srow['section']
            pri = srow['pri']
            location = srow['location']
            mtg = srow['time']
            del(srow['course'])
            del(srow['section'])
            del(srow['pri'])
            del(srow['time'])
            del(srow['location'])
            if course not in results['courses']:
                results['courses'][course] = srow
                results['courses'][course]['sections'] = {}
            results['courses'][course]['sections'][section] = {'location': location, 'time': mtg, 'pri': pri, 'students': {}}
            query = 'SELECT student, name FROM sched_semester LEFT JOIN sched_student USING (school, student) WHERE school=%s AND course=%s AND section=%s'
            values = (school, course, section, )
            cdata, error, warning = mysql.query_dict(query, values)
            for crow in cdata:
                results['courses'][course]['sections'][section]['students'][crow['student']] = crow['name']
        mcache.delete(key)
        mcache.set(key, results)
        for c in results['courses']:
            nresults = {'user': results['user'], 'name': results['name'], 'department': results['department'], 'school': results['school'], 'year': SCHOOL_INFO[school]['year'], 'semester': SCHOOL_INFO[school]['semester'], 'block': SCHOOL_INFO[school]['block'], 'courses': {}}
            nkey = key+':'+c
            nresults['courses'][c] = results['courses'][c]
            mcache.delete(nkey)
            mcache.set(nkey, nresults)
        for c in results['courses']:
            oc = results['courses'][c]
            for s in oc['sections']:
                nresults = {'user': results['user'], 'name': results['name'], 'department': results['department'], 'school': results['school'], 'year': SCHOOL_INFO[school]['year'], 'semester': SCHOOL_INFO[school]['semester'], 'block': SCHOOL_INFO[school]['block'], 'courses': {}}
                nresults['courses'][c] = {'title': oc['title'], 'department':oc['department'], 'sections': {}}
                nresults['courses'][c]['sections'][s] = oc['sections'][s]
                nkey = key+':'+c+':'+s
                mcache.delete(nkey)
                mcache.set(nkey, nresults)

###############################################################################
print(time.asctime(time.localtime(time.time())), 'Processing course:<course> and course:<course>:<instructor>')
# api: /course/[course]/[instructor]
# returns:
# {'school': 'XXXX', 'course': 'XXXX', 'title': 'XXXX', 'department': 'XXXX', 'year': 'XXXX', 'semester': 'XXXX', 'BLOCK': 'XXXX'
#   'sections': {
#     'section##': {'location': 'XXXX', 'time': 'XXXX',
#                   'instructors': {
#                       'instlogin': {'name': 'XXXX', 'department': 'XXXX', 'pri': '1/0'}
#                   },
#                   'students': {
#                       'midnlogin': {'name': 'XXXX'}
#                   }
#    }
# }
if DEBUG_ALLOW:
    query = 'SELECT * FROM sched_course'
    data, error, warning = mysql.query_dict(query)
    if error != '' or warning is not None:
        print(' -', ['DEBUG:', error, warning])
    for row in data:
        courseCache = {}
        school = row['school']
        course = row['course']
        title = row['title']
        department = row['department']
        key = 'course:'+course
        results = {'school': school,
                   'course': course,
                   'title': title,
                   'department': department,
                   'year': SCHOOL_INFO[school]['year'], 'semester': SCHOOL_INFO[school]['semester'], 'block': SCHOOL_INFO[school]['block'],
                   'sections': {}
               }
        squery = 'SELECT section, instructor, pri, name, department, location, time FROM sched_section_instructors LEFT JOIN sched_instructor USING (school, instructor) LEFT JOIN sched_section USING (school, course, section) WHERE school=%s AND course=%s'
        svalues = (school, course,)
        sdata, error, warning = mysql.query_dict(squery, svalues)
        if error != '' or warning is not None:
            print(' -', ['DEBUG:', error, warning])
        for srow in sdata:
            section = srow['section']
            instructor = srow['instructor']
            if instructor not in courseCache:
                courseCache[instructor] = {'school': school,
                           'course': course,
                           'title': title,
                           'department': department,
                           'year': SCHOOL_INFO[school]['year'], 'semester': SCHOOL_INFO[school]['semester'], 'block': SCHOOL_INFO[school]['block'],
                           'sections': {}
                       }
            if section not in results['sections']:
                results['sections'][section] = {'location': srow['location'], 'time': srow['time'], 'instructors': {}, 'students': {}}
            if section not in courseCache[instructor]['sections']:
                courseCache[instructor]['sections'][section] = {'location': srow['location'], 'time': srow['time'], 'instructors': {}, 'students': {}}
            results['sections'][section]['instructors'][srow['instructor']] = {'name': srow['name'], 'department': srow['department'], 'pri': srow['pri']}
            courseCache[instructor]['sections'][section]['instructors'][srow['instructor']] = {'name': srow['name'], 'department': srow['department'], 'pri': srow['pri']}
            vquery = 'SELECT student, name FROM sched_semester LEFT JOIN sched_student USING (school, student) WHERE school=%s and course=%s and section=%s'
            vvalues = (school, course, section,)
            vdata, error, warning = mysql.query_dict(vquery, vvalues)
            if error != '' or warning is not None:
                print(' -', ['DEBUG:', error, warning])
            for vrow in vdata:
                results['sections'][section]['students'][vrow['student']] = {'name': vrow['name']}
                courseCache[instructor]['sections'][section]['students'][vrow['student']] = {'name': vrow['name']}
        mcache.delete(key)
        mcache.set(key, results)
        for instructor in courseCache:
            ikey = key+':'+instructor
            mcache.delete(ikey)
            mcache.set(ikey, courseCache[instructor])

###############################################################################
print(time.asctime(time.localtime(time.time())), 'Processing room:<location>')
# api: /room/<location>
# returns:
# {
#     "dayofweek": {
#       "period": {
#         "school": "XXXX",
#         "course": "XXXX",
#         "section": "XXXX",
#         "title": "XXXX",
#         "department": "XXXX",
#         "instructors": {
#           "choi": {
#             "department": "XXXX",
#             "name": "XXXX",
#             "pri": "1/0"
#           }
#         }
#     }
#   }
# }
if DEBUG_ALLOW:
    query = 'SELECT school, course, section, title, sched_course.department as cdepartment, sched_instructor.department as idepartment, name, instructor, pri, location, time FROM sched_section LEFT JOIN sched_course USING (school, course) LEFT JOIN sched_section_instructors USING (school, course, section) LEFT JOIN sched_instructor USING (school, instructor)'
    data, error, warning = mysql.query_dict(query)
    if error != '' or warning is not None:
        print(' -', ['DEBUG:', error, warning])
    roomData = {}
    for row in data:
        school = row['school']
        room = row['location'].split(',')
        mtg = row['time'].split(',')
        for i in range(len(room)):
            thisroom = room[i]
            thismtg = mtg[i]
            if thisroom not in ('None', '', 'TBA BY ARRANGEMENT', 'TBD BY ARRANGEMENT', 'TBA', 'TBD'):
                period = thismtg[-1]
                for dow in thismtg[:-1]:
                    if thisroom not in roomData:
                        roomData[thisroom] = {}
                    if dow not in roomData[thisroom]:
                        roomData[thisroom][dow] = {}
                    if period not in roomData[thisroom][dow]:
                         roomData[thisroom][dow][period] = {'school': school,
                                                   'course': row['course'],
                                                   'section': row['section'],
                                                   'title': row['title'],
                                                   'department': row['cdepartment'],
                                                   'instructors': {}
                                               }
                    roomData[thisroom][dow][period]['instructors'][row['instructor']] = {'department': row['idepartment'], 'name': row['name'], 'pri': row['pri']}
    for room in roomData:
        key = 'room:'+ room
        mcache.delete(key)
        mcache.set(key, roomData[room])

###############################################################################
print(time.asctime(time.localtime(time.time())), 'Processing department:instructors:<school>')
if DEBUG_ALLOW:
    for school in SCHOOL_INFO:
        query = 'SELECT * FROM sched_instructor WHERE school=%s'
        values = (school,)
        data, error, warning = mysql.query_dict(query, values)
        if error != '' or warning is not None:
            print(' -', ['DEBUG:', error, warning])
        results = {}
        for row in data:
            if row['department'] not in results:
                results[row['department']] = {}
            results[row['department']][row['instructor']] = {'name': row['name'], 'school': row['school']}
        key = 'department:instructors:'+school
        mcache.delete(key)
        mcache.set(key, results)

###############################################################################
print(time.asctime(time.localtime(time.time())), 'Processing department:<school>')
if DEBUG_ALLOW:
    for school in SCHOOL_INFO:
        query = 'SELECT DISTINCT department FROM sched_instructor WHERE school=%s ORDER BY department'
        values = (school,)
        data, error, warning = mysql.query_dict(query, values)
        if error != '' or warning is not None:
            print(' -', ['DEBUG:', error, warning])
        results = []
        for row in data:
            results.append(row['department'])
        key = 'department:'+school
        mcache.delete(key)
        mcache.set(key, results)

###############################################################################
print(time.asctime(time.localtime(time.time())), 'Processing course:<school>')
if DEBUG_ALLOW:
    for school in SCHOOL_INFO:
        query = 'SELECT course, title, department FROM sched_course WHERE school=%s ORDER BY course'
        values = (school,)
        data, error, warning = mysql.query_dict(query, values)
        if error != '' or warning is not None:
            print(' -', ['DEBUG:', error, warning])
        results = {}
        for row in data:
            results[row['course']] = {'title': row['title'], 'department': row['department']}
        key = 'course:'+school
        mcache.delete(key)
        mcache.set(key, results)

###############################################################################
print(time.asctime(time.localtime(time.time())), 'Processing student:<school>')
if DEBUG_ALLOW:
    for school in SCHOOL_INFO:
        query = 'SELECT student, name FROM sched_student WHERE school=%s ORDER BY student'
        values = (school,)
        data, error, warning = mysql.query_dict(query, values)
        if error != '' or warning is not None:
            print(' -', ['DEBUG:', error, warning])
        results = {}
        for row in data:
            results[row['student']] = {'name': row['name']}
        key = 'student:'+school
        mcache.delete(key)
        mcache.set(key, results)

###############################################################################
print(time.asctime(time.localtime(time.time())), 'Processing instructor:<school>')
if DEBUG_ALLOW:
    for school in SCHOOL_INFO:
        query = 'SELECT instructor, name, department FROM sched_instructor WHERE school=%s ORDER BY instructor'
        values = (school,)
        data, error, warning = mysql.query_dict(query, values)
        if error != '' or warning is not None:
            print(' -', ['DEBUG:', error, warning])
        results = {}
        for row in data:
            results[row['instructor']] = {'name': row['name'], 'department': row['department']}
        key = 'instructor:'+school
        mcache.delete(key)
        mcache.set(key, results)

print(time.asctime(time.localtime(time.time())), 'Complete...')
