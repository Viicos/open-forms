# Generated by Django 2.2.24 on 2021-09-03 10:42
import colorsys
import functools
import re
from io import StringIO

import django.contrib.postgres.fields.jsonb
import django.core.validators
import django.db.migrations.operations.special
import django.db.models.deletion
from django.core.management import call_command
from django.db import migrations, models

import colorfield.fields
import django_better_admin_arrayfield.models.fields
import tinymce.models

import openforms.utils.fields
import openforms.utils.translations


def load_cookiegroups(*args):
    call_command("loaddata", "cookie_consent", stdout=StringIO())


# default colors from CKEditor source code (in CSS HSL format)
# via https://github.com/ckeditor/ckeditor5/blob/master/packages/ckeditor5-font/src/fontcolor/fontcolorediting.js
default_cke_values = [
    {"color": "hsl(0, 0%, 0%)", "label": "Black"},
    {"color": "hsl(0, 0%, 30%)", "label": "Dim grey"},
    {"color": "hsl(0, 0%, 60%)", "label": "Grey"},
    {"color": "hsl(0, 0%, 90%)", "label": "Light grey"},
    {
        "color": "hsl(0, 0%, 100%)",
        "label": "White",
    },
    {"color": "hsl(0, 75%, 60%)", "label": "Red"},
    {"color": "hsl(30, 75%, 60%)", "label": "Orange"},
    {"color": "hsl(60, 75%, 60%)", "label": "Yellow"},
    {"color": "hsl(90, 75%, 60%)", "label": "Light green"},
    {"color": "hsl(120, 75%, 60%)", "label": "Green"},
    {"color": "hsl(150, 75%, 60%)", "label": "Aquamarine"},
    {"color": "hsl(180, 75%, 60%)", "label": "Turquoise"},
    {"color": "hsl(210, 75%, 60%)", "label": "Light blue"},
    {"color": "hsl(240, 75%, 60%)", "label": "Blue"},
    {"color": "hsl(270, 75%, 60%)", "label": "Purple"},
]


def hsl_to_rgbhex(hsl_css_color):
    exp = "^hsl\((\d+), (\d+)%, (\d+)%\)$"
    m = re.match(exp, hsl_css_color)
    if m:
        h = int(m.group(1))
        s = int(m.group(2))
        l = int(m.group(3))

        # conversion algorithm via https://stackoverflow.com/questions/41403936/converting-hsl-to-hex-in-python3
        rgb = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
        hex = "#%02x%02x%02x" % (
            round(rgb[0] * 255),
            round(rgb[1] * 255),
            round(rgb[2] * 255),
        )
        return hex


def add_colors(apps, schema_editor):
    RichTextColor = apps.get_model("config", "RichTextColor")

    for elem in default_cke_values:
        hex_color = hsl_to_rgbhex(elem["color"])
        if not hex_color:
            continue
        RichTextColor.objects.create(label=elem["label"], color=hex_color)


def remove_colors(apps, schema_editor):
    RichTextColor = apps.get_model("config", "RichTextColor")
    RichTextColor.objects.all().delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("cookie_consent", "0002_auto__add_logitem"),
    ]

    operations = [
        migrations.RunPython(
            code=load_cookiegroups,
            reverse_code=migrations.operations.special.RunPython.noop,
        ),
        migrations.CreateModel(
            name="RichTextColor",
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
                    "color",
                    colorfield.fields.ColorField(
                        default="#FFFFFF",
                        help_text="Color in RGB hex format (#RRGGBB)",
                        image_field=None,
                        max_length=18,
                        samples=None,
                        verbose_name="color",
                    ),
                ),
                (
                    "label",
                    models.CharField(
                        help_text="Human readable label for reference",
                        max_length=64,
                        verbose_name="label",
                    ),
                ),
            ],
            options={
                "verbose_name": "text editor color preset",
                "verbose_name_plural": "text editor color presets",
                "ordering": ("label",),
            },
        ),
        migrations.RunPython(code=add_colors, reverse_code=remove_colors),
        migrations.CreateModel(
            name="CSPSetting",
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
                    "directive",
                    models.CharField(
                        choices=[
                            ("default-src", "default-src"),
                            ("script-src", "script-src"),
                            ("script-src-attr", "script-src-attr"),
                            ("script-src-elem", "script-src-elem"),
                            ("img-src", "img-src"),
                            ("object-src", "object-src"),
                            ("prefetch-src", "prefetch-src"),
                            ("media-src", "media-src"),
                            ("frame-src", "frame-src"),
                            ("font-src", "font-src"),
                            ("connect-src", "connect-src"),
                            ("style-src", "style-src"),
                            ("style-src-attr", "style-src-attr"),
                            ("style-src-elem", "style-src-elem"),
                            ("base-uri", "base-uri"),
                            ("child-src", "child-src"),
                            ("frame-ancestors", "frame-ancestors"),
                            ("navigate-to", "navigate-to"),
                            ("form-action", "form-action"),
                            ("sandbox", "sandbox"),
                            ("report-uri", "report-uri"),
                            ("report-to", "report-to"),
                            ("manifest-src", "manifest-src"),
                            ("worker-src", "worker-src"),
                            ("plugin-types", "plugin-types"),
                            ("require-sri-for", "require-sri-for"),
                        ],
                        help_text="CSP header directive",
                        max_length=64,
                        verbose_name="directive",
                    ),
                ),
                (
                    "value",
                    models.CharField(
                        help_text="CSP header value",
                        max_length=128,
                        verbose_name="value",
                    ),
                ),
            ],
            options={
                "ordering": ("directive", "value"),
            },
        ),
        # keep this as last entry so django has it easier to optimize operations during
        # squashing.
        migrations.CreateModel(
            name="GlobalConfiguration",
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
                    "email_template_netloc_allowlist",
                    django_better_admin_arrayfield.models.fields.ArrayField(
                        base_field=models.CharField(max_length=1000),
                        blank=True,
                        default=list,
                        help_text="Provide a list of allowed domains (without 'https://www').Hyperlinks in a (confirmation) email are removed, unless the domain is provided here.",
                        size=None,
                        verbose_name="allowed email domain names",
                    ),
                ),
                (
                    "default_test_bsn",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="When provided, submissions that are started will have this BSN set as default for the session. Useful to test/demo prefill functionality.",
                        max_length=9,
                        verbose_name="default test BSN",
                    ),
                ),
                (
                    "display_sdk_information",
                    models.BooleanField(
                        default=False,
                        help_text="When enabled, information about the used SDK is displayed.",
                        verbose_name="display SDK information",
                    ),
                ),
                (
                    "default_test_kvk",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="When provided, submissions that are started will have this KvK Number set as default for the session. Useful to test/demo prefill functionality.",
                        max_length=9,
                        verbose_name="default test KvK Number",
                    ),
                ),
                (
                    "submission_confirmation_template",
                    tinymce.models.HTMLField(
                        default="Thank you for submitting this form.",
                        help_text="The content of the submission confirmation page. It can contain variables that will be templated from the submitted form data.",
                        verbose_name="submission confirmation template",
                    ),
                ),
                (
                    "allow_empty_initiator",
                    models.BooleanField(
                        default=False,
                        help_text="When enabled and the submitter is not authenticated, a case is created without any initiator. Otherwise, a fake initiator is added with BSN 111222333.",
                        verbose_name="allow empty initiator",
                    ),
                ),
                (
                    "form_begin_text",
                    models.CharField(
                        default=functools.partial(
                            openforms.utils.translations.get_default,
                            *("Begin form",),
                            **{}
                        ),
                        help_text="The text that will be displayed at the start of the form to indicate the user can begin to fill in the form",
                        max_length=50,
                        verbose_name="begin text",
                    ),
                ),
                (
                    "form_change_text",
                    models.CharField(
                        default=functools.partial(
                            openforms.utils.translations.get_default, *("Change",), **{}
                        ),
                        help_text="The text that will be displayed in the overview page to change a certain step",
                        max_length=50,
                        verbose_name="change text",
                    ),
                ),
                (
                    "form_confirm_text",
                    models.CharField(
                        default=functools.partial(
                            openforms.utils.translations.get_default,
                            *("Confirm",),
                            **{}
                        ),
                        help_text="The text that will be displayed in the overview page to confirm the form is filled in correctly",
                        max_length=50,
                        verbose_name="confirm text",
                    ),
                ),
                (
                    "form_previous_text",
                    models.CharField(
                        default=functools.partial(
                            openforms.utils.translations.get_default,
                            *("Previous page",),
                            **{}
                        ),
                        help_text="The text that will be displayed in the overview page to go to the previous step",
                        max_length=50,
                        verbose_name="back to form text",
                    ),
                ),
                (
                    "form_step_next_text",
                    models.CharField(
                        default=functools.partial(
                            openforms.utils.translations.get_default, *("Next",), **{}
                        ),
                        help_text="The text that will be displayed in the form step to go to the next step",
                        max_length=50,
                        verbose_name="step next text",
                    ),
                ),
                (
                    "form_step_previous_text",
                    models.CharField(
                        default=functools.partial(
                            openforms.utils.translations.get_default,
                            *("Previous page",),
                            **{}
                        ),
                        help_text="The text that will be displayed in the form step to go to the previous step",
                        max_length=50,
                        verbose_name="previous step text",
                    ),
                ),
                (
                    "form_step_save_text",
                    models.CharField(
                        default=functools.partial(
                            openforms.utils.translations.get_default,
                            *("Save current information",),
                            **{}
                        ),
                        help_text="The text that will be displayed in the form step to save the current information",
                        max_length=50,
                        verbose_name="step save text",
                    ),
                ),
                (
                    "admin_session_timeout",
                    models.PositiveIntegerField(
                        default=60,
                        help_text="Amount of time in minutes the admin can be inactive for before being logged out",
                        validators=[django.core.validators.MinValueValidator(5)],
                        verbose_name="admin session timeout",
                    ),
                ),
                (
                    "form_session_timeout",
                    models.PositiveIntegerField(
                        default=15,
                        help_text="Amount of time in minutes a user filling in a form can be inactive for before being logged out",
                        validators=[
                            django.core.validators.MinValueValidator(5),
                            django.core.validators.MaxValueValidator(
                                15,
                                message="Due to DigiD requirements this value has to be less than or equal to %(limit_value)s minutes.",
                            ),
                        ],
                        verbose_name="form session timeout",
                    ),
                ),
                (
                    "design_token_values",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Values of various style parameters, such as border radii, background colors... Note that this is advanced usage. Any available but un-specified values will use fallback default values. See https://open-forms.readthedocs.io/en/latest/installation/form_hosting.html#run-time-configuration for documentation.",
                        verbose_name="design token values",
                    ),
                ),
                (
                    "main_website",
                    models.URLField(
                        blank=True,
                        help_text="URL to the main website. Used for the 'back to municipality website' link.",
                        verbose_name="main website link",
                    ),
                ),
                (
                    "logo",
                    openforms.utils.fields.SVGOrImageField(
                        blank=True,
                        help_text="Upload the municipality logo, visible to users filling out forms. We advise dimensions around 150px by 75px. SVG's are allowed.",
                        upload_to="logo/",
                        verbose_name="municipality logo",
                    ),
                ),
                (
                    "enable_demo_plugins",
                    models.BooleanField(
                        default=False,
                        help_text="If enabled, the admin allows selection of demo backend plugins.",
                        verbose_name="enable demo plugins",
                    ),
                ),
                (
                    "all_submissions_removal_limit",
                    models.PositiveIntegerField(
                        default=90,
                        help_text="Amount of days when all submissions will be permanently deleted",
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="all submissions removal limit",
                    ),
                ),
                (
                    "errored_submissions_removal_limit",
                    models.PositiveIntegerField(
                        default=30,
                        help_text="Amount of days errored submissions will remain before being removed",
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="errored submission removal limit",
                    ),
                ),
                (
                    "errored_submissions_removal_method",
                    models.CharField(
                        choices=[
                            ("delete_permanently", "Submissions will be deleted"),
                            (
                                "make_anonymous",
                                "Sensitive data within the submissions will be deleted",
                            ),
                        ],
                        default="delete_permanently",
                        help_text="How errored submissions will be removed after the",
                        max_length=50,
                        verbose_name="errored submissions removal method",
                    ),
                ),
                (
                    "incomplete_submissions_removal_limit",
                    models.PositiveIntegerField(
                        default=7,
                        help_text="Amount of days incomplete submissions will remain before being removed",
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="incomplete submission removal limit",
                    ),
                ),
                (
                    "incomplete_submissions_removal_method",
                    models.CharField(
                        choices=[
                            ("delete_permanently", "Submissions will be deleted"),
                            (
                                "make_anonymous",
                                "Sensitive data within the submissions will be deleted",
                            ),
                        ],
                        default="delete_permanently",
                        help_text="How incomplete submissions will be removed after the limit",
                        max_length=50,
                        verbose_name="incomplete submissions removal method",
                    ),
                ),
                (
                    "successful_submissions_removal_limit",
                    models.PositiveIntegerField(
                        default=7,
                        help_text="Amount of days successful submissions will remain before being removed",
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="successful submission removal limit",
                    ),
                ),
                (
                    "successful_submissions_removal_method",
                    models.CharField(
                        choices=[
                            ("delete_permanently", "Submissions will be deleted"),
                            (
                                "make_anonymous",
                                "Sensitive data within the submissions will be deleted",
                            ),
                        ],
                        default="delete_permanently",
                        help_text="How successful submissions will be removed after the limit",
                        max_length=50,
                        verbose_name="successful submissions removal method",
                    ),
                ),
            ],
            options={
                "verbose_name": "General configuration",
            },
        ),
    ]
