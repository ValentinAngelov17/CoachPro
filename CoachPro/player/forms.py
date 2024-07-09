# player/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Player, BaselinePerformance, BaselineExercise


class PlayerRegistrationForm(UserCreationForm):
    class Meta:
        model = Player
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2', 'age', 'position', 'height', 'weight',
                  'dominant_foot']


class BaselinePerformanceForm(forms.ModelForm):
    class Meta:
        model = BaselinePerformance
        fields = ['repetitions', 'time', 'successful_attempts']

    def __init__(self, *args, **kwargs):
        exercise_type = kwargs.pop('exercise_type', None)
        super(BaselinePerformanceForm, self).__init__(*args, **kwargs)

        if exercise_type == 'repetitions':
            self.fields.pop('time')
            self.fields.pop('successful_attempts')
        elif exercise_type == 'time':
            self.fields.pop('repetitions')
            self.fields.pop('successful_attempts')
        elif exercise_type == 'success_rate':
            self.fields.pop('repetitions')
            self.fields.pop('time')


class DailyRecommendationForm(forms.Form):
    WORKOUT_TODAY_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No')
    ]

    EXERCISE_COUNT_CHOICES = [(i, str(i)) for i in range(1, 6)]

    workout_today = forms.ChoiceField(choices=WORKOUT_TODAY_CHOICES, widget=forms.RadioSelect,
                                      label='Did you workout today?')
    quality = forms.ChoiceField(choices=BaselineExercise.TRAINING_TARGET_CHOICES, widget=forms.RadioSelect,
                                required=False,
                                label='Do you have specific quality you want to train today?')
    exercise_count = forms.ChoiceField(choices=EXERCISE_COUNT_CHOICES, widget=forms.Select,
                                       label="Do you prefer how many exercises you want to train?", required=False)
