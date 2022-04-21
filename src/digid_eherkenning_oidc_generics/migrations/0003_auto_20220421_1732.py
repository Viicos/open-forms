# Generated by Django 3.2.13 on 2022-04-21 15:32

from django.db import migrations, models

import django_better_admin_arrayfield.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("digid_eherkenning_oidc_generics", "0002_openidconnectdigidmachtigenconfig"),
    ]

    operations = [
        migrations.AddField(
            model_name="openidconnectdigidmachtigenconfig",
            name="oidc_exempt_urls",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=models.CharField(max_length=1000, verbose_name="Exempt URL"),
                blank=True,
                default=list,
                help_text="This is a list of absolute url paths, regular expressions for url paths, or Django view names. This plus the mozilla-django-oidc urls are exempted from the session renewal by the SessionRefresh middleware.",
                size=None,
                verbose_name="URLs exempt from session renewal",
            ),
        ),
        migrations.AddField(
            model_name="openidconnectdigidmachtigenconfig",
            name="oidc_nonce_size",
            field=models.PositiveIntegerField(
                default=32,
                help_text="Sets the length of the random string used for OpenID Connect nonce verification",
                verbose_name="Nonce size",
            ),
        ),
        migrations.AddField(
            model_name="openidconnectdigidmachtigenconfig",
            name="oidc_state_size",
            field=models.PositiveIntegerField(
                default=32,
                help_text="Sets the length of the random string used for OpenID Connect state verification",
                verbose_name="State size",
            ),
        ),
        migrations.AddField(
            model_name="openidconnectdigidmachtigenconfig",
            name="oidc_use_nonce",
            field=models.BooleanField(
                default=True,
                help_text="Controls whether the OpenID Connect client uses nonce verification",
                verbose_name="Use nonce",
            ),
        ),
        migrations.AddField(
            model_name="openidconnecteherkenningconfig",
            name="oidc_exempt_urls",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=models.CharField(max_length=1000, verbose_name="Exempt URL"),
                blank=True,
                default=list,
                help_text="This is a list of absolute url paths, regular expressions for url paths, or Django view names. This plus the mozilla-django-oidc urls are exempted from the session renewal by the SessionRefresh middleware.",
                size=None,
                verbose_name="URLs exempt from session renewal",
            ),
        ),
        migrations.AddField(
            model_name="openidconnecteherkenningconfig",
            name="oidc_nonce_size",
            field=models.PositiveIntegerField(
                default=32,
                help_text="Sets the length of the random string used for OpenID Connect nonce verification",
                verbose_name="Nonce size",
            ),
        ),
        migrations.AddField(
            model_name="openidconnecteherkenningconfig",
            name="oidc_state_size",
            field=models.PositiveIntegerField(
                default=32,
                help_text="Sets the length of the random string used for OpenID Connect state verification",
                verbose_name="State size",
            ),
        ),
        migrations.AddField(
            model_name="openidconnecteherkenningconfig",
            name="oidc_use_nonce",
            field=models.BooleanField(
                default=True,
                help_text="Controls whether the OpenID Connect client uses nonce verification",
                verbose_name="Use nonce",
            ),
        ),
        migrations.AddField(
            model_name="openidconnectpublicconfig",
            name="oidc_exempt_urls",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=models.CharField(max_length=1000, verbose_name="Exempt URL"),
                blank=True,
                default=list,
                help_text="This is a list of absolute url paths, regular expressions for url paths, or Django view names. This plus the mozilla-django-oidc urls are exempted from the session renewal by the SessionRefresh middleware.",
                size=None,
                verbose_name="URLs exempt from session renewal",
            ),
        ),
        migrations.AddField(
            model_name="openidconnectpublicconfig",
            name="oidc_nonce_size",
            field=models.PositiveIntegerField(
                default=32,
                help_text="Sets the length of the random string used for OpenID Connect nonce verification",
                verbose_name="Nonce size",
            ),
        ),
        migrations.AddField(
            model_name="openidconnectpublicconfig",
            name="oidc_state_size",
            field=models.PositiveIntegerField(
                default=32,
                help_text="Sets the length of the random string used for OpenID Connect state verification",
                verbose_name="State size",
            ),
        ),
        migrations.AddField(
            model_name="openidconnectpublicconfig",
            name="oidc_use_nonce",
            field=models.BooleanField(
                default=True,
                help_text="Controls whether the OpenID Connect client uses nonce verification",
                verbose_name="Use nonce",
            ),
        ),
    ]
