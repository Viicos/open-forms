# Generated by Django 3.2.16 on 2022-11-01 14:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0065_submission_language_code"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="submissionvaluevariable",
            name="language",
        ),
    ]
