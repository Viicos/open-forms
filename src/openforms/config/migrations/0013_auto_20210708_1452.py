# Generated by Django 2.2.20 on 2021-07-08 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("config", "0012_globalconfiguration_allow_empty_initiator"),
    ]

    operations = [
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_begin_text",
            field=models.CharField(
                default="Begin form",
                help_text="The text that will be displayed at the start of the form to indicate the user can begin to fill in the form",
                max_length=50,
                verbose_name="Form Begin Text",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_change_text",
            field=models.CharField(
                default="Change",
                help_text="The text that will be displayed in the overview page to change a certain step",
                max_length=50,
                verbose_name="Form Change Text",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_confirm_text",
            field=models.CharField(
                default="Confirm",
                help_text="The text that will be displayed in the overview page to confirm the form is filled in correctly",
                max_length=50,
                verbose_name="Form Confirm Text",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_previous_text",
            field=models.CharField(
                default="Previous page",
                help_text="The text that will be displayed in the overview page to go to the previous step",
                max_length=50,
                verbose_name="Form Previous Text",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_step_next_text",
            field=models.CharField(
                default="Next",
                help_text="The text that will be displayed in the form step to go to the next step",
                max_length=50,
                verbose_name="Form Step Next Text",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_step_previous_text",
            field=models.CharField(
                default="Previous page",
                help_text="The text that will be displayed in the form step to go to the previous step",
                max_length=50,
                verbose_name="Form Step Previous Text",
            ),
        ),
        migrations.AddField(
            model_name="globalconfiguration",
            name="form_step_save_text",
            field=models.CharField(
                default="Save current information",
                help_text="The text that will be displayed in the form step to save the current information",
                max_length=50,
                verbose_name="Form Step Save Text",
            ),
        ),
    ]
