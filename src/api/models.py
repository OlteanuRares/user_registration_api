from django.db import models


class ApiUser(models.Model):
    email = models.CharField(max_length=50,  null=True)
    password = models.CharField(max_length=1024, null=True)
    token = models.CharField(max_length=4, null=True)
    activated = models.BooleanField(default=False)
    token_sent_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

    objects = models.Manager()
