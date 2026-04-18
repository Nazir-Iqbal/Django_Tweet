from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    THEME_CHOICES = [('light', 'Light'), ('dark', 'Dark')]

    bio = models.TextField(max_length=500, blank=True)
    avatar_color = models.CharField(max_length=7, default='#6366f1')
    theme = models.CharField(max_length=5, choices=THEME_CHOICES, default='dark')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def get_initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()
