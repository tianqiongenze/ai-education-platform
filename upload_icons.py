# -*- coding: utf-8 -*-
"""Upload 16 course icons into contentstore and set course_image fields."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cms.envs.production')
import django
django.setup()

from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey
from xmodule.contentstore.django import contentstore
from django.core.files.uploadedfile import SimpleUploadedFile

from django.contrib.auth.models import User

COURSES = ["P1","P2","P3","P4","P5","P6","B1","B2","B3","B4","B5","B6","A1","A2","A3","A4"]

UID = User.objects.filter(is_superuser=True).first()
print("Using admin:", UID)

ms = modulestore()
cs = contentstore()

for num in COURSES:
    ck = CourseKey.from_string('course-v1:AIEDU+%s+2026' % num)
    course = ms.get_course(ck)
    if course is None:
        print('MISSING course', ck); continue
    png = open('/tmp/icons/%s.png' % num, 'rb').read()
    fname = '%s_course_image.png' % num.lower()
    from opaque_keys.edx.locator import AssetLocator
    asset_loc = AssetLocator(ck.for_branch(None), 'asset', fname)
    from xmodule.contentstore.content import StaticContent
    content = StaticContent(asset_loc, fname, 'image/png', png)
    cs.save(content)
    # update course fields
    course.course_image = fname
    course.banner_image = fname
    course.thumbnail_image = fname
    course.hero_image = fname
    ms.update_item(course, UID.id)
    print('OK', ck, '->', fname)
print("ALL DONE")
