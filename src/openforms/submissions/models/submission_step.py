import uuid

from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import gettext_lazy as _

from frozendict import frozendict

from openforms.forms.models import FormStep


def _make_frozen(obj):
    if not isinstance(obj, (dict, list)):
        return obj

    elif isinstance(obj, list):
        return tuple([_make_frozen(item) for item in obj])

    retval = frozendict()
    for key, value in obj.items():
        if isinstance(value, dict):
            frozen_value = _make_frozen(value)
        elif isinstance(value, list):
            frozen_value = tuple([_make_frozen(item) for item in value])
        else:
            frozen_value = value
        retval = retval.set(key, frozen_value)
    return retval


def _make_unfrozen(obj):
    if isinstance(obj, frozendict):
        return {key: _make_unfrozen(value) for key, value in obj.items()}

    elif isinstance(obj, tuple):
        return [_make_unfrozen(item) for item in obj]

    return obj


# Note that this exists because of data loss bug #2135 - when a FormStep is being
# deleted in the form designer (or during import/export), we do not want to destroy
# the submitted data for that step.
#
# This implements a bandaid fix where we record just enough information to reconstruct
# the FormStep in memory.
def RECORD_HISTORICAL_FORM_STEP(collector, field, sub_objs, using):
    form_steps = list(collector.data[FormStep])
    assert (
        len(form_steps) == 1
    ), "Only this specific case for SubmissionStep cascade delete is supported"
    form_step = form_steps[0]
    serialized_form_definition = serializers.serialize(
        "python", [form_step.form_definition]
    )[0]
    serialized_form_step = serializers.serialize("python", [form_step])[0]

    # update the history field
    history_field = SubmissionStep._meta.get_field("form_step_history")
    frozen_history = _make_frozen(
        {
            "form_step": serialized_form_step,
            "form_definition": serialized_form_definition,
        }
    )
    collector.add_field_update(history_field, frozen_history, sub_objs)

    # our own reference can now become NULL
    collector.add_field_update(field, None, sub_objs)


class FrozenDjangoJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, frozendict):
            unfrozen = _make_unfrozen(o)
            return unfrozen
        return super().default(o)


class SubmissionStep(models.Model):
    """
    Submission data.

    TODO: This model (and therefore API) allows for the same form step to be
    submitted multiple times. Can be useful for retrieving historical data or
    changes made during filling out the form... but...
    """

    uuid = models.UUIDField(_("UUID"), unique=True, default=uuid.uuid4)
    submission = models.ForeignKey("submissions.Submission", on_delete=models.CASCADE)
    form_step = models.ForeignKey(
        "forms.FormStep",
        on_delete=RECORD_HISTORICAL_FORM_STEP,
        null=True,
        blank=True,
    )
    data = models.JSONField(_("data"), blank=True, null=True)
    created_on = models.DateTimeField(_("created on"), auto_now_add=True)
    modified = models.DateTimeField(_("modified on"), auto_now=True)

    # bugfix for #2135
    form_step_history = models.JSONField(
        _("form step (historical)"),
        encoder=FrozenDjangoJSONEncoder,
        editable=False,
        default=None,
        blank=True,
        null=True,
    )

    # can be modified by logic evaluations/checks
    _can_submit = True
    _is_applicable = True

    class Meta:
        verbose_name = _("Submission step")
        verbose_name_plural = _("Submission steps")
        unique_together = (("submission", "form_step"),)

    def __str__(self):
        return f"SubmissionStep {self.pk}: Submission {self.submission_id} submitted on {self.created_on}"

    @property
    def completed(self) -> bool:
        # TODO: should check that all the data for the form definition is present?
        # and validates?
        # For now - if it's been saved, we assume that was because it was completed
        return bool(self.pk and self.data is not None)

    @property
    def can_submit(self) -> bool:
        return self._can_submit

    @property
    def is_applicable(self) -> bool:
        return self._is_applicable

    def reset(self):
        self.data = None
        self.save()
