# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import sys

this_file_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(this_file_path, '..')))

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_work_farm.settings')

app = Celery('api_work_farm')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))