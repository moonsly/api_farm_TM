from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required

from api_work_farm.views import Profile, StartTask, GetStatus, GetResult, MyTasks

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
        
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^$', Profile.as_view(), name='index'), 
    url(r'^start_task/', StartTask.as_view(), name='start-task'),
    url(r'^get_status/', GetStatus.as_view(), name='get-status'),
    url(r'^get_result/', GetResult.as_view(), name='get-result'),
    url(r'^my_tasks/', MyTasks.as_view(), name='my-tasks'),
    
    url(r'^admin/', include(admin.site.urls)),
         
)
