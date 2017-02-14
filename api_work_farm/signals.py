import datetime
import hashlib

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from registration.signals import user_registered
from api_work_farm import models


def superuser_post_save(sender, instance, **kwargs):
	user = instance
	
	existing_api_id = models.UserApiId.objects.filter(user_id=user.id).all()
	if not existing_api_id:
		uniqueHash = hashlib.md5( "{0}.{1}-{2}".format(user.username, str(datetime.datetime.now()), user.password) ).hexdigest() + \
				 hashlib.md5( "{0}.{1}-{2}".format(datetime.datetime.now(), user.date_joined, user.password) ).hexdigest()
		api_id = models.UserApiId(user_id=user.id, api_id=uniqueHash)
		api_id.save()

    
post_save.connect(superuser_post_save, sender=User)
