# Generated by Django 3.2.20 on 2023-07-18 14:29

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import openforms.appointments.fields


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0076_alter_submission_form_url"),
        ("appointments", "0009_appointmentsconfig_limit_to_location"),
    ]

    operations = [
        migrations.CreateModel(
            name="Appointment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "plugin",
                    openforms.appointments.fields.AppointmentBackendChoiceField(
                        help_text="The plugin active at the time of creation. This determines the context to interpret the submitted data.",
                        max_length=100,
                        verbose_name="plugin",
                    ),
                ),
                (
                    "location",
                    models.CharField(
                        help_text="Identifier of the location in the selected plugin.",
                        max_length=128,
                        verbose_name="location ID",
                    ),
                ),
                (
                    "datetime",
                    models.DateTimeField(
                        help_text="Date and time of the appointment",
                        verbose_name="appointment time",
                    ),
                ),
                (
                    "contact_details_meta",
                    models.JSONField(
                        default=list,
                        help_text="Contact detail field definitions, depending on the required fields in the selected plugin. Recorded for historical purposes.",
                        verbose_name="contact details meta",
                    ),
                ),
                (
                    "contact_details",
                    models.JSONField(
                        default=dict,
                        help_text="Additional contact detail field values.",
                        verbose_name="contact details",
                    ),
                ),
                (
                    "submission",
                    models.OneToOneField(
                        help_text="The submission that made the appointment",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="appointment",
                        to="submissions.submission",
                    ),
                ),
            ],
            options={
                "verbose_name": "appointment",
                "verbose_name_plural": "appointments",
            },
        ),
        migrations.CreateModel(
            name="AppointmentProduct",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "product_id",
                    models.CharField(
                        help_text="Identifier of the product in the selected plugin.",
                        max_length=128,
                        verbose_name="product ID",
                    ),
                ),
                (
                    "amount",
                    models.PositiveSmallIntegerField(
                        help_text="Number of times (amount of people) the product is ordered",
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="amount",
                    ),
                ),
                (
                    "appointment",
                    models.ForeignKey(
                        help_text="Appointment for this product order.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="appointments.appointment",
                        verbose_name="appointment",
                    ),
                ),
            ],
            options={
                "verbose_name": "appointment product",
                "verbose_name_plural": "appointment products",
            },
        ),
    ]
