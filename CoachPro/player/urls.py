from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('', views.home_page, name='home page'),
    path('profile/', views.profile, name='profile'),
    path('baseline_exercises/', views.view_baseline_exercises, name='view_baseline_exercises'),
    path('baseline_performance/add/<int:exercise_id>/', views.add_baseline_performance,
         name='add_baseline_performance'),
    path('baseline_performances/', views.view_player_baseline_performances, name='view_player_baseline_performances'),
    path('get_training_recommendations/', views.get_training_recommendations, name='training recommendations'),
    path('daily_recommendations/', views.daily_recommendations, name='daily_recommendations'),
    path('log_recommended_exercises/', views.log_recommended_exercises, name='log_recommended_exercises'),
    path('add_baseline_performance/<int:exercise_id>/', views.add_baseline_performance, name='add_baseline_performance'),


]
