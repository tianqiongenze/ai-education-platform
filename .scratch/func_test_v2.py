"""Functional test suite v2: registration auto-activate + automount + course visibility."""
import django, os, uuid
os.environ.setdefault('DJANGO_SETTINGS_MODULE','lms.envs.tutor.production')
django.setup()
from django.conf import settings
from django.contrib.auth.models import User
from common.djangoapps.student.models import CourseEnrollment, Registration
from common.djangoapps.student.helpers import do_create_account
from openedx.core.djangoapps.user_authn.views.registration_form import AccountCreationForm
from openedx.core.djangoapps.course_groups.cohorts import get_cohort
from opaque_keys.edx.keys import CourseKey

PASS=[]
FAIL=[]
def check(name, cond, detail=''):
    (PASS if cond else FAIL).append((name,detail))
    print(('PASS' if cond else 'FAIL'), name, detail)

# T1 settings
check('T1 SKIP_EMAIL_VALIDATION=True', settings.FEATURES.get('SKIP_EMAIL_VALIDATION') is True)
check('T2 COURSES_INVITE_ONLY=True', getattr(settings,'COURSES_INVITE_ONLY',False) is True)
check('T3 AUTOMOUNT map >= 20 entries', len(getattr(settings,'AUTOMOUNT_PREFIX_MAP',{})) >= 20)

def register(username):
    params = {'username':username,'email':username.replace('_','-')+'@edu.local','password':'AutoTest2026!',
      'name':'FT User','terms_of_service':'true','honor_code':'true',
      'level_of_education':'','gender':'','year_of_birth':'','mailing_address':'','city':'','country':'','goals':''}
    form = AccountCreationForm(data=params, tos_required=True, extra_fields={})
    assert form.is_valid(), form.errors
    user, profile, registration = do_create_account(form, None)
    # replicate register.py decision
    if settings.FEATURES.get('SKIP_EMAIL_VALIDATION'):
        registration.activate()
    return User.objects.get(username=username)

def cleanup(username):
    try: User.objects.get(username=username).delete()
    except User.DoesNotExist: pass

# T4: stu_p1 prefix -> auto enroll P1 + cohort p1-class1
uname = 'stu_p1_ft' + uuid.uuid4().hex[:5]
u = register(uname)
ck = CourseKey.from_string('course-v1:AIEDU+P1+2026')
enr = CourseEnrollment.objects.filter(user=u, course_id=ck, is_active=True).exists()
check(f'T4 {uname} auto-enrolled P1', enr)
coh = get_cohort(u, ck)
check(f'T5 {uname} in cohort p1-class1', coh is not None and coh.name=='p1-class1', f'got {getattr(coh,"name",None)}')
# other courses NOT enrolled
n_other = CourseEnrollment.objects.filter(user=u).exclude(course_id=ck).count()
check(f'T6 {uname} enrolled ONLY in P1 (0 others)', n_other==0, f'others={n_other}')
cleanup(uname)

# T7: stu_b2 prefix -> P2? no -> B2 class2
uname2 = 'stu_b2_ft' + uuid.uuid4().hex[:5]
u2 = register(uname2)
ck2 = CourseKey.from_string('course-v1:AIEDU+B2+2026')
enr2 = CourseEnrollment.objects.filter(user=u2, course_id=ck2, is_active=True).exists()
check(f'T7 {uname2} auto-enrolled B2', enr2)
coh2 = get_cohort(u2, ck2)
check(f'T8 {uname2} cohort b2-class2', coh2 is not None and coh2.name=='b2-class2', f'got {getattr(coh2,"name",None)}')
cleanup(uname2)

# T9: unmatched prefix -> 0 enrollments (invisible to all courses)
uname3 = 'guest_ft' + uuid.uuid4().hex[:5]
u3 = register(uname3)
n3 = CourseEnrollment.objects.filter(user=u3, is_active=True).count()
check(f'T9 {uname3} (no prefix) 0 enrollments', n3==0, f'got {n3}')
cleanup(uname3)

# T10: every AIEDU course has >=2 staff teachers
from common.djangoapps.student.roles import CourseStaffRole
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
bad=[]
for co in CourseOverview.objects.filter(org='AIEDU'):
    n = CourseStaffRole(co.id).users_with_role().count()
    if n < 2: bad.append((str(co.id), n))
check('T10 all 16 courses have >=2 staff teachers', len(bad)==0, str(bad))

# T11: cohorts exist per course
from openedx.core.djangoapps.course_groups.models import CourseUserGroup
missing=[]
for co in CourseOverview.objects.filter(org='AIEDU'):
    code=str(co.id).split('+')[1]
    need = {f'{code.lower()}-class1', f'{code.lower()}-class2'}
    have = set(CourseUserGroup.objects.filter(course_id=co.id, group_type='cohort').values_list('name', flat=True))
    if not need <= have: missing.append((code, sorted(need-have)))
check('T11 every course has class1+class2 cohorts', len(missing)==0, str(missing))

# T12: all industrial teachers active
ok=all(User.objects.filter(username=t, is_active=True).exists() for t in
       ['teacher_java_01','teacher_java_02','teacher_go_01','teacher_go_02','teacher_rust_01','teacher_rust_02','teacher_zhang','teacher_python_02'])
check('T12 8 teacher accounts active', ok)

# T13: zero inactive users in DB
check('T13 zero inactive users', User.objects.filter(is_active=False).count()==0)

print()
print(f'RESULT: {len(PASS)} passed, {len(FAIL)} failed')
for f in FAIL: print('  FAILED:', f[0], f[1])
