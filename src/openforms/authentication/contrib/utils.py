from digid_eherkenning.models.digid import DigidConfiguration
from digid_eherkenning.models.eherkenning import EherkenningConfiguration

from openforms.config.constants import CSPDirective
from openforms.config.models import CSPSetting

ADDITIONAL_VALUES = {
    "digid": "'self' https://digid.nl https://*.digid.nl",
    "eherkenning": "'self'",
}


def create_csp_setting(new_entity_id: str, type: str) -> None:
    csps = {
        "directive": CSPDirective.FORM_ACTION,
        "value": f"{ADDITIONAL_VALUES[type]} {new_entity_id}",
    }
    CSPSetting.objects.create(**csps)


def update_csp(
    instance: DigidConfiguration | EherkenningConfiguration, type: str
) -> None:
    if not instance._state.adding:
        original_object = instance.__class__.objects.get(pk=instance.pk)

        if original_object.idp_service_entity_id != instance.idp_service_entity_id:
            CSPSetting.objects.filter(
                directive=CSPDirective.FORM_ACTION,
                value__in=[
                    original_object.idp_service_entity_id,
                    f"{ADDITIONAL_VALUES[type]} {original_object.idp_service_entity_id}",
                ],
            ).delete()

            create_csp_setting(instance.idp_service_entity_id, type)
