from django.db import models
from django.contrib.auth.models import User

class Workout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.CharField(max_length=200)
    duration = models.IntegerField(help_text="Duration in minutes")
    date = models.DateField()

    def __str__(self):
        return f"{self.activity} - {self.duration} min on {self.date}"

class UserProfile(models.Model):
    # OneToOneField means one user has exactly one profile
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    weekly_goal = models.IntegerField(default=150)  # 150 mins default

    def __str__(self):
        return f"{self.user.username}'s profile"