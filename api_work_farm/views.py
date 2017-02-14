# -*- coding: utf-8 -*-
import json
import hashlib
import datetime

from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView, BaseDetailView, SingleObjectTemplateResponseMixin
from django.views.generic.base import TemplateResponseMixin
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.db.models import Q, F
from django.core import serializers

from api_work_farm.tasks import start_task
from api_work_farm import models, forms


def api_login_required(f):
    def wrap(request, *args, **kwargs):
        # -- check session login OR correct api_id
        apiID = request.REQUEST.get('api_id', '')
        user = None
        if apiID:
            api_id = models.UserApiId.objects.filter(api_id=apiID)
            if api_id:
                user = api_id[0].user

        elif request.user.is_authenticated():
            user = request.user

        if not user:
            return HttpResponseRedirect(reverse('auth_login'))        

        return f(request, *args, **kwargs)

    wrap.__doc__=f.__doc__
    wrap.__name__=f.__name__
    return wrap


class ApiLoginRequiredMixin(object):
    @method_decorator(api_login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ApiLoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class JSONResponseMixin(object):
    def render_to_response(self, context):        
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        return HttpResponse(content,
                                 content_type='application/json',
                                 **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        return json.dumps(context)
        

class Profile(ApiLoginRequiredMixin, TemplateView):
    template_name = "index.html"
    """
    Запуск задачи/группы задач воркером
    Проверяются лимиты (в forms.py):
    1) общая длина JSON-параметра <= MAX_JSON
    2) на число одновременно запускаемых задач <= MAX_TASKS
    3) число сообщений для одной задачи <= MAX_MESSAGES
    4) длина каждого сообщения <= MAX_MSG_LEN

    В базе создаются Task на каждую задачу с unique_id задачи.
    Сообщения передаются напрямую воркерам через celery.delay.     
    """

    def get(self, request, **kwargs):
        generate = request.GET.get('generate', '')
    
        api_id = models.UserApiId.objects.filter(user=request.user)[:1].get()        

        if generate == 'new_api_id':
            user = request.user
            uniqueHash = hashlib.md5( "{0}.{1}-{2}".format(user.username, str(datetime.datetime.now()), user.password) ).hexdigest() + \
                     hashlib.md5( "{0}.{1}-{2}".format(datetime.datetime.now(), user.date_joined, user.password) ).hexdigest()
            api_id.api_id = uniqueHash
            api_id.save()

        context = {
            'limits': settings.JSON_VALIDATION,
            'form':   forms.TaskForm(initial={'api_id': api_id.api_id}),
            'api_id': api_id.api_id,
        }
        return self.render_to_response(context)

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(Profile, self).dispatch(*args, **kwargs)


class StartTask(ApiLoginRequiredMixin, JSONResponseMixin, BaseDetailView):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(StartTask, self).dispatch(*args, **kwargs)

    def get(self, request, **kwargs):
        return self.render_to_response({'ok': 0, 'error': 'use only POST'})

    def post(self, request, **kwargs):
        context = {}
        api_id = models.UserApiId.objects.filter(user=request.user)[:1].get()

        form = forms.TaskForm(request.POST)
        if form.is_valid():
            tasks = form.cleaned_data['json']

            ids = []
            for t in tasks['tasks']:
                new_task = models.Task(user=request.user)
                new_task.save()
                messages = t['task']
                res = start_task.delay(new_task.pk, messages)
                row = {'id': new_task.unique_id, 'state': res.state}
                if res.state == 'FAILURE': 
                    new_task.error_msg = res.result
                    row['exception'] = res.result
                    new_task.status = 100

                ids.append(row)

            return HttpResponse(json.dumps({'ok': 1, 'task_ids': ids}), content_type='application/json')   
        else:
            errors = [(k, v[0]) for k, v in form.errors.items()]
            return HttpResponse(json.dumps({'ok': 0, 'form_errors': errors}), content_type='application/json')   


class GetStatus(ApiLoginRequiredMixin, JSONResponseMixin, BaseDetailView):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(GetStatus, self).dispatch(*args, **kwargs)

    def get(self, request, **kwargs):
        unique_ids = request.GET.getlist('unique_id')
        if len(unique_ids) == 0:
            return self.render_to_response({'ok': 0, 'error': 'no id found'})

        res = []
        for ID in unique_ids:
            task = models.Task.objects.filter(unique_id=ID).all()
            if task:             
                res.append({ 'id': task[0].unique_id, 'status': task[0].status, 'estimate': task[0].estimate })
            else:
                res.append({ 'id': ID, 'error': 'no such task' })

        return self.render_to_response(res)


class GetResult(ApiLoginRequiredMixin, JSONResponseMixin, BaseDetailView):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(GetResult, self).dispatch(*args, **kwargs)

    def get(self, request, **kwargs):
        unique_ids = request.GET.getlist('unique_id')
        if len(unique_ids) == 0:
            return self.render_to_response({'ok': 0, 'error': 'no id found'})

        res = []
        for ID in unique_ids:
            task = models.Task.objects.filter(unique_id=ID).all()
            if task:             
                res.append({ 'id': task[0].unique_id, 'status': task[0].status, 'result': task[0].result })
            else:
                res.append({ 'id': ID, 'error': 'no such task' })

        return self.render_to_response(res)


class MyTasks(ApiLoginRequiredMixin, JSONResponseMixin, BaseDetailView):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(MyTasks, self).dispatch(*args, **kwargs)

    def get(self, request, **kwargs):
        show_all = request.GET.get('show_all', '')
        
        q = Q(user=request.user)
        if not show_all:
            q = q & Q(status__in=[0,1])

        tasks = models.Task.objects.filter(q).all()#.values('unique_id', 'user_id', 'status', 'estimate', 'result')
        
        return HttpResponse( serializers.serialize('json', tasks, fields=('unique_id', 'user_id', 'status', 'estimate', 'result')) )

"""
AsyncResult.state[source]
The tasks current state.

Possible values includes:

PENDING - The task is waiting for execution.
STARTED - The task has been started.
RETRY - The task is to be retried, possibly because of failure.
FAILURE - The task raised an exception, or has exceeded the retry limit. The result attribute then contains the exception raised by the task.
SUCCESS - The task executed successfully. The result attribute then contains the tasks return value.

if FAILURE -> result has exception
"""