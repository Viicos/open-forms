# Generated by Django 2.2.24 on 2021-07-30 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0026_submission_last_register_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="registration_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending (not registered yet)"),
                    ("in_progress", "In Progress (not registered yet)"),
                    ("success", "Success"),
                    ("failed", "Failed"),
                ],
                default="pending",
                help_text="Indication whether the registration in the configured backend was successful.",
                max_length=50,
                verbose_name="registration backend status",
            ),
        ),
    ]
