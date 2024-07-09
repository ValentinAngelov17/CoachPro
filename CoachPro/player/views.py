import os
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import PlayerRegistrationForm, BaselinePerformanceForm, DailyRecommendationForm
from .models import BaselinePerformance, PlayerRating, BaselineExercise, Player
import openai
from django.urls import reverse

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@login_required
def get_training_recommendations(request):
    player = get_object_or_404(Player, id=request.user.id)
    player_ratings = get_object_or_404(PlayerRating, player=player)

    player_info = f"""
    Player Information:
    - First Name: {player.first_name}
    - Last Name: {player.last_name}
    - Age: {player.age}
    - Position: {player.get_position_display()}
    - Height: {player.height} cm
    - Weight: {player.weight} kg
    - Dominant Foot: {player.get_dominant_foot_display()}

    Stats Ratings:
    - Agility: {player_ratings.agility}
    - Endurance: {player_ratings.endurance}
    - Header: {player_ratings.header}
    - Passing: {player_ratings.passing}
    - Shooting: {player_ratings.shooting}
    - Sprint: {player_ratings.sprint}
    - Strength: {player_ratings.strength}
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "We are a highly knowledgeable professional football coaches."},
            {"role": "user",
             "content": f"This football player completed baseline exercise and based on his performance he has rating"
                        f" for every quality. The rating system is from 0 to 10 and level rating is: - 0-5 beginner,"
                        f" 5-8 intermediate and  8-10 advanced. Give him tips and talk like you are his personal "
                        f"knowledgeable football coach. Based on the following player information, provide personalized"
                        f" training recommendations  :\n\n{player_info}. Focus also on his player position to give the"
                        f" best advices. End the message with something motivating"
                        f" and regards from CoachPro."}
        ],
        max_tokens=500
    )

    recommendations = response.choices[0].message.content

    return render(request, 'recommendations.html', {'recommendations': recommendations})


def register(request):
    if request.method == 'POST':
        form = PlayerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('login')
    else:
        form = PlayerRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


def home_page(request):
    return render(request, 'index.html')


@login_required
def profile(request):
    player = request.user
    ratings = PlayerRating.objects.get(player=player)
    average_rating = ratings.calculate_total_average()

    if average_rating <= 5:
        level = 'beginner'
    elif average_rating < 8:
        level = 'intermediate'
    else:
        level = 'advanced'

    context = {
        'player': player,
        'ratings': ratings,
        'average_rating': average_rating,
        'level': level,
    }
    return render(request, 'profile.html', context)


@login_required
def view_baseline_exercises(request):
    exercises = BaselineExercise.objects.all()

    return render(request, 'view_baseline_exercises.html', {'exercises': exercises})


@login_required
def add_baseline_performance(request, exercise_id):
    exercise = get_object_or_404(BaselineExercise, pk=exercise_id)

    if request.method == 'POST':
        form = BaselinePerformanceForm(request.POST, exercise_type=exercise.type)
        if form.is_valid():
            performance = form.save(commit=False)
            performance.player = request.user
            performance.exercise = exercise

            performance.save()

            return redirect('view_player_baseline_performances')
    else:
        form = BaselinePerformanceForm(exercise_type=exercise.type)

    return render(request, 'add_baseline_performance.html', {'form': form, 'exercise': exercise})


@login_required
def view_player_baseline_performances(request):
    performances = BaselinePerformance.objects.filter(player=request.user).order_by('-date')

    return render(request, 'view_player_baseline_performances.html',
                  {'performances': performances})


@login_required
def daily_recommendations(request):
    if request.method == 'POST':
        form = DailyRecommendationForm(request.POST)
        if form.is_valid():
            workout_today = form.cleaned_data['workout_today']
            quality = form.cleaned_data['quality']
            exercise_count = int(form.cleaned_data['exercise_count'])
            player = get_object_or_404(Player, id=request.user.id)
            player_ratings = get_object_or_404(PlayerRating, player=player)

            if quality:
                exercises = BaselineExercise.objects.filter(training_target=quality)
            else:
                exercises = BaselineExercise.objects.all()

            exercise_info = []
            for exercise in exercises:
                exercise_info.append({
                    'name': exercise.name,
                    'description': exercise.description,
                    'beginner_criteria': exercise.beginner_criteria,
                    'intermediate_criteria': exercise.intermediate_criteria,
                    'advanced_criteria': exercise.advanced_criteria,
                    'type': exercise.type,
                    'id': exercise.id
                })

            chat_input = f"""
                        We are a highly knowledgeable professional football coaches. Based on the following player
                         information, ratings and exercise preferences, provide personalized training recommendations 
                         for today. The player has {'worked out' if workout_today == 'yes' else 'not worked out'} today, 
                        {'prefers to train ' if quality else "does not have a specific quality to train"} for 
                        {quality if quality else ""}, and wants {exercise_count} exercises. Recommend him every exercise
                         first set to be with maximum performance and 2 more  easy sets if he train, and 3 more easy 
                         sets if he doesn't train. Create full split for the training with exercises, sets and rest
                          between every set. Choose exercises from the given Exercises information. Write like you are
                           talking to him face to face. End the message with regards from CoachPro.

                        Player Information:
                        - First Name: {player.first_name}
                        - Last Name: {player.last_name}
                        - Age: {player.age}
                        - Position: {player.get_position_display()}
                        - Height: {player.height} cm
                        - Weight: {player.weight} kg
                        - Dominant Foot: {player.get_dominant_foot_display()}
                        
                        Player ratings:
                        - Strength: {player_ratings.strength}
                        - Agility - {player_ratings.agility}
                        - Endurance - {player_ratings.endurance}
                        - Header - {player_ratings.header}
                        - Passing - {player_ratings.passing}
                        - Shooting - {player_ratings.shooting}
                        - Spring - {player_ratings.sprint}

                        Exercises Information:
                        """

            for exercise in exercise_info:
                chat_input += (f"\n- {exercise['name']}\n  {exercise['description']}\n"
                               f"  Beginner: {exercise['beginner_criteria']} {exercise['type']}\n"
                               f"  Intermediate: {exercise['intermediate_criteria']} {exercise['type']}\n"
                               f"  Advanced: {exercise['advanced_criteria']} {exercise['type']}\n")

            # Call the OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "We are a highly knowledgeable professional football coaches."},
                    {"role": "user", "content": chat_input}
                ],
                max_tokens=500
            )

            recommendations = response.choices[0].message.content

            recommended_exercise_names = [exercise.name for exercise in exercises if exercise.name in recommendations]

            selected_exercises = BaselineExercise.objects.filter(name__in=recommended_exercise_names)

            selected_exercise_ids = list(selected_exercises.values_list('id', flat=True))

            request.session['selected_exercises'] = selected_exercise_ids

            return render(request, 'daily_recommendations_result.html', {
                'recommendations': recommendations,
                'log_url': reverse('log_recommended_exercises')
            })

    else:
        form = DailyRecommendationForm()
        request.session['selected_exercises'] = []

    return render(request, 'daily_recommendations.html', {'form': form})


@login_required
def log_recommended_exercises(request):
    selected_exercise_ids = request.session.get('selected_exercises', [])
    exercises = BaselineExercise.objects.filter(id__in=selected_exercise_ids)

    if request.method == 'POST':
        forms = [
            (BaselinePerformanceForm(request.POST, exercise_type=exercise.type, prefix=str(exercise.id)), exercise)
            for exercise in exercises
        ]

        if all(form.is_valid() for form, exercise in forms):
            for form, exercise in forms:
                performance = form.save(commit=False)
                performance.player = request.user
                performance.exercise = exercise
                performance.calculate_score_and_level()
                performance.save()

            return redirect('view_player_baseline_performances')
    else:
        forms = [
            (BaselinePerformanceForm(exercise_type=exercise.type, prefix=str(exercise.id)), exercise)
            for exercise in exercises
        ]

    return render(request, 'log_recommended_exercises.html', {'forms': forms})


