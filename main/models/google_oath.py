from django.contrib.auth.models import User
from django.db import models


class TokenStorageModel(models.Model):
    id = models.ForeignKey(User, primary_key=True, related_name='google_id')
    token = models.TextField()

    class Meta:
        app_label = 'main'