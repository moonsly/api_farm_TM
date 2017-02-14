# -*- coding: utf-8 -*-
from __future__ import absolute_import

import random
import time

from celery import Celery, shared_task
from django.conf import settings
from django.utils.timezone import now
from django.db.models import Q, F
from django.template.loader import get_template
from django.template import Context
from api_work_farm import models


@shared_task(serializer='json')
def start_task(task_id, messages):
    """
    Запуск задачи воркером:
    спим случайное кол-во секунд + обновляем estimate окончания в базе каждую секунду
    """
    task = models.Task.objects.filter(pk=task_id)[0]
    task.status = models.Task.STARTED
    estimate = int((random.random()*100)/2)
    task.estimate = estimate
    task.save()

    slept = 0
    while slept < estimate:
        time.sleep(1)
        slept += 1
        task.estimate = estimate - slept
        task.save()

    task.status = models.Task.FINISHED
    task.result = "Successfully slept for %d seconds" % slept
    task.save()
   
    return {'result': True}