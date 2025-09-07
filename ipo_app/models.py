# ipo_app/models.py
from django.db import models

class UserAccount(models.Model):
    name = models.CharField(max_length=100)
    dp_id = models.CharField(max_length=20)
    boid = models.CharField(max_length=16)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)   # store encrypted in real use
    crn = models.CharField(max_length=20)
    lot_size = models.IntegerField(default=10)

    def __str__(self):
        return self.name
