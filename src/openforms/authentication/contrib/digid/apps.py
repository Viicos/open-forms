from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DigidApp(AppConfig):
    name = "openforms.authentication.contrib.digid"
    label = "authentication_digid"
    verbose_name = _("DigiD authentication plugin")

    def ready(self):
        # register the plugin
        from . import plugin  # noqa

        # register the signals
        from .signals import update_csp  # noqa
