from oauth2_provider.models import Application
from django.contrib.auth import get_user_model

U = get_user_model()
admin = U.objects.get(email='admin@openedx.local')

# Create JupyterHub OAuth client
app, created = Application.objects.get_or_create(
    name='jupyterhub-sso',
    defaults={
        'user': admin,
        'client_type': Application.CLIENT_CONFIDENTIAL,
        'authorization_grant_type': Application.GRANT_AUTHORIZATION_CODE,
        'redirect_uris': 'https://10.167.2.175:31825/hub/oauth_callback',
        'skip_authorization': False,
    }
)
print('CLIENT_ID:', app.client_id)
print('CREATED:', created)
print('REDIRECT_URIS:', app.redirect_uris)
