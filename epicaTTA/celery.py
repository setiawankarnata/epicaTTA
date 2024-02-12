import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'epicaTTA.settings')

app = Celery('epicaTTA')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.conf.enable_utc = False
app.conf.update(timezone='Asia/Jakarta')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# Celery beat settings
app.conf.beat_schedule = {
    'send-mail-everyday-at-06-00': {
        'task': 'pica.tasks.send_activity_duedate_notifications',
        'schedule': crontab(hour='13', minute='50', day_of_week='1,2,3,4,5')
    }
}
