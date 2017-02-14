#-*- coding: utf-8 -*-
import datetime
import hashlib
import random

from django.db import models
from django.conf import settings

from django.contrib.auth.models import User


class Worker(models.Model):
	name = models.CharField(max_length=32)
	status = models.IntegerField('status', null=False, default=0)
	last_active = models.DateTimeField()
	started = models.DateTimeField('Started', editable=False, auto_now_add=True)


class Task(models.Model):
    PENDING = 0
    STARTED = 1
    FINISHED = 2
    ERROR = 100
    STATUSES = (
        (PENDING, 'PENDING'),
        (STARTED, 'STARTED'),
        (FINISHED, 'FINISHED'),
        (ERROR, 'ERROR'),
    )

    user = models.ForeignKey(User, related_name='owner')
    unique_id = models.CharField(null=False, default='', max_length=32)
    worker = models.ForeignKey('Worker', null=True)
    status = models.SmallIntegerField('status', null=False, default=0, choices=STATUSES)
    created = models.DateTimeField('Creation time', editable=False, auto_now_add=True)
    result = models.CharField(null=False, default='', max_length=100)
    estimate = models.IntegerField(null=False, default=0)
    error_msg = models.CharField(null=False, default='', max_length=1024)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.unique_id = hashlib.md5( "{0}.{1}-{2}".format( random.random(), str(datetime.datetime.now()), random.random()) ).hexdigest()
        super(Task, self).save(*args, **kwargs)

    def __unicode__(self):
        return '%d: %s | User: %d | Status: %d' % (self.id, self.unique_id, self.user.id, self.status)


class UserApiId(models.Model):
    user = models.OneToOneField(User, related_name='user')
    api_id = models.CharField(null=False, max_length=64, unique=True)

    def __unicode__(self):
        return 'User: %d | api_ID: %s' % (self.user.id, self.api_id)