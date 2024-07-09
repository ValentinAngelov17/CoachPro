from django.contrib import admin
from .models import BaselineExercise, BaselinePerformance, Player, PlayerRating

admin.site.register(Player)
admin.site.register(BaselineExercise)
admin.site.register(BaselinePerformance)
admin.site.register(PlayerRating)