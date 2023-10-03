from django.db.models.signals import pre_save
from django.dispatch import receiver

from digid_eherkenning.models.eherkenning import EherkenningConfiguration

from ..utils import update_csp


@receiver(pre_save, sender=EherkenningConfiguration)
def trigger_csp_update(sender, instance, **kwargs):
    update_csp(instance, "eherkenning")
