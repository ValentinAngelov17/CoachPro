# player/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

from CoachPro import settings


class Player(AbstractUser):
    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('DF', 'Defender'),
        ('MF', 'Midfielder'),
        ('FW', 'Attacker'),
    ]

    DOMINANT_FOOT_CHOICES = [
        ('left', 'Left'),
        ('right', 'Right'),
    ]

    username = None
    email = models.EmailField(unique=True, blank=False)
    age = models.IntegerField(blank=False, null=False)
    position = models.CharField(max_length=2, choices=POSITION_CHOICES)
    height = models.FloatField(blank=False, null=False)
    weight = models.FloatField(blank=False, null=False)
    dominant_foot = models.CharField(max_length=10, choices=DOMINANT_FOOT_CHOICES)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'age', 'position', 'height', 'weight', 'dominant_foot']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class BaselineExercise(models.Model):
    TRAINING_TARGET_CHOICES = [
        ('strength', 'Strength'),
        ('endurance', 'Endurance'),
        ('agility', 'Agility'),
        ('sprint', 'Sprint'),
        ('shooting', 'Shooting'),
        ('passing', 'Passing'),
        ('header', 'Header')
    ]
    EXERCISE_TYPE_CHOICES = [
        ('repetitions', 'Repetitions'),
        ('time', 'Time'),
        ('success_rate', 'Success Rate')
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    tips = models.TextField()
    picture = models.ImageField(upload_to='baseline_exercise_pics/', blank=True, null=True)
    training_target = models.CharField(max_length=100, choices=TRAINING_TARGET_CHOICES)
    type = models.CharField(max_length=20, choices=EXERCISE_TYPE_CHOICES)
    beginner_criteria = models.FloatField(default=0)
    intermediate_criteria = models.FloatField(default=0)
    advanced_criteria = models.FloatField(default=0)

    def __str__(self):
        return self.name


class BaselinePerformance(models.Model):
    player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercise = models.ForeignKey(BaselineExercise, on_delete=models.CASCADE)
    successful_attempts = models.IntegerField(blank=True, null=True)
    time = models.FloatField(blank=True, null=True)
    repetitions = models.IntegerField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=20, blank=True, null=True)
    score = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.player} - {self.exercise.name}"

    def time_str(self):
        minutes = int(self.time // 60)
        seconds = self.time % 60
        return f"{minutes:01d} : {seconds}"

    def successful_attempts_str(self):
        return f"{self.successful_attempts}/{int(self.exercise.advanced_criteria)}"

    def calculate_score_and_level(self):
        if self.exercise.type == 'repetitions':
            self.score = (self.repetitions / self.exercise.advanced_criteria) * 10
            self.level = self.get_level(self.score)

        elif self.exercise.type == 'time':
            self.score = self.calculate_time_score()
            self.level = self.get_level(self.score)

        elif self.exercise.type == 'success_rate':
            self.score = (self.successful_attempts / self.exercise.advanced_criteria) * 10
            self.level = self.get_level(self.score)

        if self.score > 10:
            self.score = 10

    def calculate_time_score(self):
        if self.exercise.advanced_criteria > self.exercise.beginner_criteria:
            # longer time is better (plank)
            if self.time >= self.exercise.advanced_criteria:
                return 10
            elif self.time >= self.exercise.intermediate_criteria:
                return interpolate_score(self.time, self.exercise.intermediate_criteria,
                                         self.exercise.advanced_criteria, 7, 10)
            elif self.time >= self.exercise.beginner_criteria:
                return interpolate_score(self.time, self.exercise.beginner_criteria,
                                         self.exercise.intermediate_criteria, 4, 7)
            else:
                return interpolate_score(self.time, 0, self.exercise.beginner_criteria, 0, 4)
        else:
            # shorter time is better (sprint)
            if self.time <= self.exercise.advanced_criteria:
                return 10
            elif self.time <= self.exercise.intermediate_criteria:
                return interpolate_score(self.time, self.exercise.advanced_criteria,
                                         self.exercise.intermediate_criteria, 10, 7)
            elif self.time <= self.exercise.beginner_criteria:
                return interpolate_score(self.time, self.exercise.intermediate_criteria,
                                         self.exercise.beginner_criteria, 7, 4)
            else:
                return interpolate_score(self.time, self.exercise.beginner_criteria,
                                         self.exercise.beginner_criteria * 2, 4, 0)

    def get_level(self, score):
        if score >= 8:
            return 'advanced'
        elif score >= 5:
            return 'intermediate'
        else:
            return 'beginner'

    def save(self, *args, **kwargs):
        self.calculate_score_and_level()
        super().save(*args, **kwargs)
        ratings, created = PlayerRating.objects.get_or_create(player=self.player)
        ratings.update_player_ratings(self.exercise.training_target)


def interpolate_score(value, min_value, max_value, min_score, max_score):
    if value <= min_value:
        return min_score
    elif value >= max_value:
        return max_score
    else:
        return min_score + ((value - min_value) / (max_value - min_value)) * (max_score - min_score)


class PlayerRating(models.Model):
    player = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    strength = models.FloatField(default=0)
    endurance = models.FloatField(default=0)
    agility = models.FloatField(default=0)
    sprint = models.FloatField(default=0)
    shooting = models.FloatField(default=0)
    passing = models.FloatField(default=0)
    header = models.FloatField(default=0)

    def __str__(self):
        return f"{self.player} Ratings"

    def calculate_total_average(self):
        attributes = [self.strength, self.endurance, self.agility, self.sprint, self.shooting, self.passing,
                      self.header]
        return sum(attributes) / len(attributes)

    def update_player_ratings(self, training_target):
        performances = BaselinePerformance.objects.filter(player=self.player, exercise__training_target=training_target)
        total_score = sum([performance.score for performance in performances])
        average_score = total_score / performances.count() if performances.exists() else 0

        setattr(self, training_target, average_score)
        self.save()



