# -*- coding: utf-8 -*-

import json

from django import forms
from django.conf import settings


class TaskForm(forms.Form):
    api_id = forms.CharField(label=u'API_ID', max_length=64, required=True, widget=forms.TextInput(attrs={'size':70, 'maxlength':64}))
    json = forms.CharField(max_length=102400, required=True, widget=forms.Textarea(attrs={'cols': 80, 'rows': 10}), \
                           initial="""{"tasks": [ { "task": ["message1_1", "message1_2"] } ] }""")

    def clean_json(self):
        field = self.cleaned_data.get('json')

        try:
            tasks = json.loads(field)
        except Exception, e:
            raise forms.ValidationError(u'Bad JSON: %s' % str(e))        

        if len(field) > settings.JSON_VALIDATION['MAX_JSON']:
            raise forms.ValidationError(u'Too long JSON, MAX length: %d' % settings.JSON_VALIDATION['MAX_JSON'])

        if 'tasks' in tasks and len(tasks['tasks']):
            if len(tasks['tasks']) > settings.JSON_VALIDATION['MAX_TASKS']:
                raise forms.ValidationError(u'Too many tasks, MAX number of tasks: %d' % settings.JSON_VALIDATION['MAX_TASKS'])

            for t in tasks['tasks']:
                if len(t['task']) > settings.JSON_VALIDATION['MAX_MESSAGES']:
                    raise forms.ValidationError(u'Too many messages in task, MAX message count per task: %d' % \
                                                settings.JSON_VALIDATION['MAX_MESSAGES'])
                for msg in t['task']:
                    if len(msg) > settings.JSON_VALIDATION['MAX_MSG_LEN']:
                        raise forms.ValidationError(u'Too long message in task, MAX message length: %d' % \
                                                      settings.JSON_VALIDATION['MAX_MSG_LEN'])

        return tasks
