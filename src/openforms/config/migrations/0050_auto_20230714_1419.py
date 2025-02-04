# Generated by Django 3.2.20 on 2023-07-14 12:19

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("config", "0049_auto_20230615_1507"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_map_default_latitude",
            field=models.FloatField(
                default=52.1326332,
                validators=[
                    django.core.validators.MinValueValidator(-180.0),
                    django.core.validators.MaxValueValidator(180.0),
                ],
                verbose_name="The default latitude for the leaflet map.",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_map_default_longitude",
            field=models.FloatField(
                default=5.291266,
                validators=[
                    django.core.validators.MinValueValidator(-90.0),
                    django.core.validators.MaxValueValidator(90.0),
                ],
                verbose_name="The default longitude for the leaflet map.",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_map_default_zoom_level",
            field=models.IntegerField(
                default=13,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(13),
                ],
                verbose_name="The default zoom level for the leaflet map.",
            ),
        ),
    ]
