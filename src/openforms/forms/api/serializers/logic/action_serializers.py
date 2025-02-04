import warnings
from datetime import date

from django.urls import resolve
from django.utils.translation import ugettext_lazy as _

from drf_polymorphic.serializers import PolymorphicSerializer
from drf_spectacular.utils import extend_schema_serializer
from furl import furl
from json_logic.typing import Primitive
from rest_framework import serializers

from openforms.api.serializers import DummySerializer
from openforms.utils.json_logic.api.validators import JsonLogicValidator
from openforms.variables.constants import FormVariableDataTypes

from ....constants import (
    LOGIC_ACTION_TYPES_REQUIRING_COMPONENT,
    LOGIC_ACTION_TYPES_REQUIRING_VARIABLE,
    LogicActionTypes,
    PropertyTypes,
)
from .fields import ActionFormStepUUIDField


class ComponentPropertySerializer(serializers.Serializer):
    value = serializers.CharField(
        label=_("property key"),
        help_text=_(
            "The Form.io component property to alter, identified by `component.key`"
        ),
    )
    type = serializers.ChoiceField(
        label=_("type"),
        help_text=_("The type of the value field"),
        choices=PropertyTypes.choices,
    )


class LogicPropertyActionSerializer(serializers.Serializer):
    property = ComponentPropertySerializer()
    state = serializers.JSONField(
        label=_("value of the property"),
        help_text=_(
            "Valid JSON determining the new value of the specified property. For example: `true` or `false`."
        ),
    )

    def validate_state(self, value):
        if value == "":
            raise serializers.ValidationError(
                self.fields["state"].error_messages["null"],
                code="blank",
            )
        return value


class LogicValueActionSerializer(serializers.Serializer):
    value = serializers.JSONField(
        label=_("Value"),
        help_text=_(
            "A valid JsonLogic expression describing the value. This may refer to "
            "(other) Form.io components."
        ),
        validators=[JsonLogicValidator()],
    )


class LogicFetchActionSerializer(serializers.Serializer):
    value = serializers.JSONField(
        label=_("service_fetch_configuration"),
    )


class LogicSetRegistrationBackendActionSerializer(serializers.Serializer):
    value = serializers.CharField(
        label=_("registration_backend_key"),
        allow_blank=False,
    )


class LogicActionPolymorphicSerializer(PolymorphicSerializer):
    type = serializers.ChoiceField(
        choices=LogicActionTypes.choices,
        label=_("Type"),
        help_text=_("Action type for this particular action."),
    )

    discriminator_field = "type"
    serializer_mapping = {
        str(LogicActionTypes.disable_next): DummySerializer,
        str(LogicActionTypes.property): LogicPropertyActionSerializer,
        str(LogicActionTypes.step_not_applicable): DummySerializer,
        str(LogicActionTypes.variable): LogicValueActionSerializer,
        str(LogicActionTypes.fetch_from_service): LogicFetchActionSerializer,
        str(
            LogicActionTypes.set_registration_backend
        ): LogicSetRegistrationBackendActionSerializer,
    }


@extend_schema_serializer(deprecate_fields=["form_step"])
class LogicComponentActionSerializer(serializers.Serializer):
    # TODO: validate that the component is present on the form
    component = serializers.CharField(
        required=False,  # validated against the action.type
        allow_blank=True,
        label=_("Form.io component"),
        help_text=_(
            "Key of the Form.io component that the action applies to. This field is "
            "required for the action types {action_types} - otherwise it's optional."
        ).format(
            action_types=", ".join(
                [
                    f"`{action_type}`"
                    for action_type in sorted(LOGIC_ACTION_TYPES_REQUIRING_COMPONENT)
                ]
            )
        ),
    )
    variable = serializers.CharField(
        required=False,  # validated against the action.type
        allow_blank=True,
        label=_("Key of the target variable"),
        help_text=_(
            "Key of the target variable whose value will be changed. This field is "
            "required for the action types {action_types} - otherwise it's optional."
        ).format(
            action_types=", ".join(
                [
                    f"`{action_type}`"
                    for action_type in sorted(LOGIC_ACTION_TYPES_REQUIRING_VARIABLE)
                ]
            )
        ),
    )
    # Deprecated field! form_step_uuid should be used instead
    form_step = serializers.URLField(
        allow_null=True,
        required=False,  # validated against the action.type
        allow_blank=True,
        label=_("form step"),
        help_text=_(
            "The form step that will be affected by the action. This field is "
            "required if the action type is `%(action_type)s`, otherwise optional."
        )
        % {"action_type": LogicActionTypes.step_not_applicable},
    )
    form_step_uuid = ActionFormStepUUIDField(
        allow_null=True,
        required=False,  # validated against the action.type
        label=_("form step"),
        help_text=_(
            "The UUID of the form step that will be affected by the action. This field is "
            "required if the action type is `%(action_type)s`, otherwise optional."
        )
        % {"action_type": LogicActionTypes.step_not_applicable},
    )
    action = LogicActionPolymorphicSerializer()

    def validate(self, data: dict) -> dict:
        """
        1. Check that the component is supplied depending on the action type.
        2. Check that the value for date variables has the right format
        """
        action_type = data.get("action", {}).get("type")
        action_value = data.get("action", {}).get("value")
        component = data.get("component")
        form_step = data.get("form_step")

        if form_step and not data.get("form_step_uuid"):
            warnings.warn(
                "Logic action 'formStep' is deprecated, use 'formStepUuid' instead",
                DeprecationWarning,
            )
            # normalize to UUID following deprecation of URL reference
            match = resolve(furl(form_step).path)
            data["form_step_uuid"] = match.kwargs["uuid"]

        form_step_uuid = data.get("form_step_uuid")
        variable = data.get("variable")

        if (
            action_type
            and action_type in LOGIC_ACTION_TYPES_REQUIRING_COMPONENT
            and not component
        ):
            raise serializers.ValidationError(
                {"component": self.fields["component"].error_messages["blank"]},
                code="blank",
            )

        if (
            action_type
            and action_type in LOGIC_ACTION_TYPES_REQUIRING_VARIABLE
            and not variable
        ):
            raise serializers.ValidationError(
                {"variable": self.fields["variable"].error_messages["blank"]},
                code="blank",
            )

        # validate format of value for date variable
        if action_type == LogicActionTypes.variable and isinstance(
            action_value, Primitive
        ):
            form_var = self.context["form_variables"].variables[variable]

            if form_var.data_type == FormVariableDataTypes.date:
                try:
                    date.fromisoformat(action_value)
                except (ValueError, TypeError) as ex:
                    raise serializers.ValidationError(
                        {
                            "action": {
                                "value": _(
                                    "Value for date variable must be a string in the "
                                    "format yyyy-mm-dd (e.g. 2023-07-03)"
                                ),
                            }
                        },
                    ) from ex

        if (
            action_type
            and action_type == LogicActionTypes.step_not_applicable
            and (not form_step and not form_step_uuid)
        ):
            raise serializers.ValidationError(
                {
                    "form_step_uuid": self.fields["form_step_uuid"].error_messages[
                        "null"
                    ]
                },
                code="blank",
            )

        return data
