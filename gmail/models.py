from django.db import models
from django.contrib.auth.models import User

class GmailToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username
