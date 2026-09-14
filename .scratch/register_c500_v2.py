"""Register 800 fresh C500-v2 students (stu_<c>_601..650 x16 courses) through the REAL
registration path (AccountCreationForm + do_create_account + skip-activation).
New account system: auto-activate + AUTOMOUNT auto-enroll + class cohort — no manual enrollment."""
import django, os, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE','lms.envs.tutor.production')
django.setup()
from django.contrib.auth.models import User
from common.djangoapps.student.helpers import do_create_account
from openedx.core.djangoapps.user_authn.views.registration_form import AccountCreationForm
from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.course_groups.cohorts import get_cohort
from opaque_keys.edx.keys import CourseKey

PASS = os.environ.get('STUDENT_PASS', 'AutoTest2026!')
COURSES = ['P1','P2','P3','P4','P5','P6','B1','B2','B3','B4','B5','B6','A1','A2','A3','A4']
START, N = 601, 50
created = skip = fail = 0
failures = []
t0 = time.time()
for c in COURSES:
    for i in range(START, START + N):
        uname = 'stu_%s_%d' % (c.lower(), i)
        if User.objects.filter(username=uname).exists():
            skip += 1
            continue
        params = {'username': uname, 'email': uname.replace('_','-') + '@edu.local',
                  'password': PASS, 'name': 'C500v2 Student %s %d' % (c, i),
                  'terms_of_service': 'true', 'honor_code': 'true',
                  'level_of_education': '', 'gender': '', 'year_of_birth': '',
                  'mailing_address': '', 'city': '', 'country': '', 'goals': ''}
        try:
            form = AccountCreationForm(data=params, tos_required=True, extra_fields={})
            assert form.is_valid(), str(form.errors)[:200]
            user, profile, registration = do_create_account(form, None)
            if not user.is_active:
                registration.activate()
            created += 1
        except Exception as ex:
            fail += 1
            failures.append('%s: %s' % (uname, str(ex)[:120]))
        if created % 100 == 0 and created:
            print('progress created=%d elapsed=%.0fs' % (created, time.time()-t0), flush=True)

print('CREATED=%d SKIPPED=%d FAILED=%d elapsed=%.0fs' % (created, skip, fail, time.time()-t0))
for f in failures[:20]: print('FAILDETAIL', f, flush=True)

# sample verification: first student of P1, B2, A4
ok = 0
for c, expect_cohort in (('P1','p1-class1'), ('B2','b2-class2'), ('A4','a4-class1')):
    u = User.objects.get(username='stu_%s_%d' % (c.lower(), START))
    ck = CourseKey.from_string('course-v1:AIEDU+%s+2026' % c)
    enr = CourseEnrollment.objects.filter(user=u, course_id=ck, is_active=True).exists()
    coh = get_cohort(u, ck, assign=False)
    cname = coh.name if coh else None
    active = u.is_active
    print('SAMPLE stu_%s_%d active=%s enrolled=%s cohort=%s' % (c.lower(), START, active, enr, cname))
    if active and enr and cname == expect_cohort:
        ok += 1
print('SAMPLE_OK=%d/3' % ok)
print('REGISTER_RESULT: created=%d skipped=%d failed=%d sample_ok=%d' % (created, skip, fail, ok))
