#!/bin/bash
# Register cms-sso OAuth application in LMS DB so Studio SSO authorize succeeds
set -e
kubectl -n openedx exec -i deploy/lms -- python /openedx/edx-platform/manage.py lms shell <<'PYEOF'
from oauth2_provider.models import Application
from django.contrib.auth.models import User

app, created = Application.objects.get_or_create(
    client_id="cms-sso",
    defaults={
        "user": User.objects.get(username="admin"),
        "client_type": Application.CLIENT_CONFIDENTIAL,
        "authorization_grant_type": Application.GRANT_AUTHORIZATION_CODE,
        "redirect_uris": "https://studio.openedx.10.167.2.175.nip.io:31825/complete/edx-oauth2/",
        "client_secret": "qTpSGAZN3RhHL2gBCeycpKMp",
        "name": "cms-sso",
        "skip_authorization": True,
    },
)
if not created:
    app.redirect_uris = "https://studio.openedx.10.167.2.175.nip.io:31825/complete/edx-oauth2/"
    app.client_secret = "qTpSGAZN3RhHL2gBCeycpKMp"
    app.client_type = Application.CLIENT_CONFIDENTIAL
    app.authorization_grant_type = Application.GRANT_AUTHORIZATION_CODE
    app.skip_authorization = True
    app.save()
print("APP_OK created=%s id=%s" % (created, app.id))
PYEOF
echo OAUTHAPPDONE
