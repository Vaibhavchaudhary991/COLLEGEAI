#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Auto-set Django Site domain to match Render hostname (fixes Google OAuth redirect_uri_mismatch)
if [ -n "$RENDER_EXTERNAL_HOSTNAME" ]; then
  python manage.py shell -c "
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = '$RENDER_EXTERNAL_HOSTNAME'
site.name = 'College AI'
site.save()
print(f'Updated Site domain to: {site.domain}')
"
fi
