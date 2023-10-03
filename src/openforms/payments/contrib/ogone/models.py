from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.config.constants import CSPDirective
from openforms.config.models import CSPSetting

from .constants import HashAlgorithm, OgoneEndpoints


class OgoneMerchant(models.Model):
    label = models.CharField(
        _("Label"),
        max_length=255,
        help_text=_("Human readable label"),
    )

    pspid = models.CharField(
        _("PSPID"),
        max_length=255,
        help_text=_("Ogone PSPID"),
    )
    sha_in_passphrase = models.CharField(
        _("SHA-IN passphrase"),
        max_length=255,
        help_text=_("This must match with the Ogone backend"),
    )
    sha_out_passphrase = models.CharField(
        _("SHA-OUT passphrase"),
        max_length=255,
        help_text=_("This must match with the Ogone backend"),
    )
    hash_algorithm = models.CharField(
        _("Hash algorithm"),
        choices=HashAlgorithm.choices,
        max_length=8,
        help_text=_("This must match with the Ogone backend"),
    )

    endpoint_preset = models.URLField(
        _("Preset endpoint"),
        choices=OgoneEndpoints.choices,
        default=OgoneEndpoints.test,
        help_text=_("Select a common preset endpoint"),
    )
    endpoint_custom = models.URLField(
        _("Custom endpoint"),
        blank=True,
        help_text=_("Optionally override the preset endpoint"),
    )

    @property
    def endpoint(self):
        return self.endpoint_custom or self.endpoint_preset

    def __str__(self):
        return self.label

    def update_csp(self, new_endpoint: str) -> None:
        csps = {
            "directive": CSPDirective.FORM_ACTION,
            "value": f"'self' {new_endpoint}",
        }
        CSPSetting.objects.create(**csps)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.update_csp(self.endpoint)
        else:
            original_object = self.__class__.objects.get(pk=self.pk)

            if original_object.endpoint != self.endpoint:
                CSPSetting.objects.filter(
                    directive=CSPDirective.FORM_ACTION,
                    value__in=[
                        original_object.endpoint,
                        f"'self' {original_object.endpoint}",
                    ],
                ).delete()

                self.update_csp(self.endpoint)

        super().save(*args, **kwargs)
