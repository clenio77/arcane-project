web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 30 --keep-alive 2 --log-level info
worker: celery -A core worker -l info --concurrency=2
release: python manage.py migrate --settings=core.settings_heroku_simple
