# Generated by Django 5.0.6 on 2024-07-04 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0004_baselineexercise_advanced_criteria_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baselineexercise',
            name='max_success_rate',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
