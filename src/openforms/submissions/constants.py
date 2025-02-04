from django.db import models
from django.utils.translation import gettext_lazy as _

SUBMISSIONS_SESSION_KEY = "form-submissions"
UPLOADS_SESSION_KEY = "form-uploads"

IMAGE_COMPONENTS = ["signature"]


class RegistrationStatuses(models.TextChoices):
    pending = "pending", _("Pending (not registered yet)")
    in_progress = "in_progress", _("In progress (not registered yet)")
    success = "success", _("Success")
    failed = "failed", _("Failed")


class ProcessingStatuses(models.TextChoices):
    """
    Translation of interal Celery states to public states.
    """

    in_progress = "in_progress", _("In progress")
    done = "done", _("Done")


class ProcessingResults(models.TextChoices):
    """
    Possible background processing outcomes (once it's 'done')
    """

    failed = "failed", _("Failed, should return to the start of the form.")
    success = "success", _("Success, proceed to confirmation page.")


class SubmissionValueVariableSources(models.TextChoices):
    sensitive_data_cleaner = "sensitive_data_cleaner", _("Sensitive data cleaner")
    user_input = "user_input", _("User input")
    prefill = "prefill", _("Prefill")
    logic = "logic", _("Logic")
    dmn = "dmn", _("DMN")
