"""Delete empty auto-created default cohorts (默认组) on AIEDU courses."""
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','lms.envs.tutor.production')
django.setup()
from openedx.core.djangoapps.course_groups.models import CourseUserGroup, CourseCohort
DELETED=0
for cc in CourseCohort.objects.filter(course_user_group__name__in=['Default Group','默认组']):
    g = cc.course_user_group
    n = g.users.count()
    if n == 0:
        print("DELETING empty default cohort", g.course_id, g.id, g.name)
        cc.delete(); g.delete(); DELETED+=1
    else:
        print("KEEP non-empty default cohort", g.course_id, g.id, g.name, "members:", n)
print("DELETED_COUNT", DELETED)
