web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --worker-class gevent --worker-connections 1000 --max-requests 1000 --timeout 30 --keep-alive 2 --log-level info
worker: celery -A core worker -l info --concurrency=2
beat: celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
release: python manage.py migrate --settings=core.settings_production
