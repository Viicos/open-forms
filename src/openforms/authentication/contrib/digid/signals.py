from django.db.models.signals import pre_save
from django.dispatch import receiver

from digid_eherkenning.models.digid import DigidConfiguration

from ..utils import update_csp


@receiver(pre_save, sender=DigidConfiguration)
def trigger_csp_update(sender, instance, **kwargs):
    update_csp(instance, "digid")
