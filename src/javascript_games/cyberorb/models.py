from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class CyberorbPersonalBest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    personal_best = models.IntegerField(validators=[MaxValueValidator(300),MinValueValidator(1)])

class CyberorbHighscore(models.Model):
    username = models.CharField(max_length=100)
    score = models.IntegerField(validators=[MaxValueValidator(300),MinValueValidator(1)])
    date_created = models.DateTimeField(auto_now_add=True)