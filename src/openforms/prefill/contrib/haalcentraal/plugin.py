import logging
from typing import Any, Iterable, Optional

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests
from glom import GlomError, glom

from openforms.authentication.constants import AuthAttribute
from openforms.contrib.haal_centraal.clients import NoServiceConfigured, get_brp_client
from openforms.contrib.haal_centraal.constants import BRPVersions
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.pre_requests.clients import PreRequestClientContext
from openforms.submissions.models import Submission

from ...base import BasePlugin
from ...constants import IdentifierRole, IdentifierRoles
from ...registry import register
from .constants import Attributes, AttributesV2

logger = logging.getLogger(__name__)


VERSION_TO_ATTRIBUTES_MAP: dict[BRPVersions, type[models.TextChoices]] = {
    BRPVersions.v13: Attributes,
    BRPVersions.v20: AttributesV2,
}


def get_config() -> HaalCentraalConfig | None:
    config = HaalCentraalConfig.get_solo()
    assert isinstance(config, HaalCentraalConfig)
    if not config.brp_personen_service:
        logger.warning("No service defined for Haal Centraal prefill.")
        return None
    return config


@register("haalcentraal")
class HaalCentraalPrefill(BasePlugin):
    verbose_name = _("Haal Centraal: BRP Personen Bevragen")
    requires_auth = AuthAttribute.bsn

    @staticmethod
    def get_available_attributes() -> list[tuple[str, str]]:
        match get_config():
            case HaalCentraalConfig(
                version=version
            ) if version in VERSION_TO_ATTRIBUTES_MAP:
                AttributesCls = VERSION_TO_ATTRIBUTES_MAP[version]
            case _:
                AttributesCls = Attributes
        return AttributesCls.choices

    @classmethod
    def _get_values_for_bsn(
        cls,
        config: HaalCentraalConfig,
        submission: Submission | None,
        bsn: str,
        attributes: Iterable[str],
    ) -> dict[str, Any]:
        client = config.build_client()
        assert client is not None
        client.context = PreRequestClientContext(submission=submission)

        data = client.find_person(bsn, attributes=attributes)
        if not data:
            return {}

        values = dict()
        for attr in attributes:
            try:
                values[attr] = glom(data, attr)
            except GlomError as exc:
                logger.warning(
                    "missing expected attribute '%s' in backend response",
                    attr,
                    exc_info=exc,
                )

        return values

    @classmethod
    def get_identifier_value(
        cls, submission: Submission, identifier_role: IdentifierRole
    ) -> str | None:
        if not submission.is_authenticated:
            return

        if (
            identifier_role == IdentifierRoles.main
            and submission.auth_info.attribute == cls.requires_auth
        ):
            return submission.auth_info.value

        if identifier_role == IdentifierRoles.authorised_person:
            return submission.auth_info.machtigen.get("identifier_value")

    @classmethod
    def get_prefill_values(
        cls,
        submission: Submission,
        attributes: list[str],
        identifier_role: IdentifierRole = IdentifierRoles.main,
    ) -> dict[str, Any]:
        if (config := get_config()) is None:
            return {}

        if not (bsn_value := cls.get_identifier_value(submission, identifier_role)):
            logger.info("No appropriate identifier found on the submission.")
            return {}

        return cls._get_values_for_bsn(config, submission, bsn_value, attributes)

    @classmethod
    def get_co_sign_values(
        cls, identifier: str, submission: Optional["Submission"] = None
    ) -> tuple[dict[str, Any], str]:
        """
        Given an identifier, fetch the co-sign specific values.

        The return value is a dict keyed by field name as specified in
        ``self.co_sign_fields``.

        :param identifier: the unique co-signer identifier used to look up the details
          in the prefill backend.
        :return: a key-value dictionary, where the key is the requested attribute and
          the value is the prefill value to use for that attribute.
        """
        config = get_config()
        if config is None:
            return ({}, "")

        version_atributes = config.get_attributes()

        values = cls._get_values_for_bsn(
            config,
            submission,
            identifier,
            (
                version_atributes.naam_voornamen,
                version_atributes.naam_voorvoegsel,
                version_atributes.naam_geslachtsnaam,
                version_atributes.naam_voorletters,
            ),
        )

        first_names = values.get(version_atributes.naam_voornamen, "")
        first_letters = values.get(version_atributes.naam_voorletters) or " ".join(
            [f"{name[0]}." for name in first_names.split(" ") if name]
        )
        representation_bits = [
            first_letters,
            values.get(version_atributes.naam_voorvoegsel, ""),
            values.get(version_atributes.naam_geslachtsnaam, ""),
        ]
        return (
            values,
            " ".join([bit for bit in representation_bits if bit]),
        )

    def check_config(self):
        """
        Check if the admin configuration is valid.

        The purpose of this fuction is to simply check the connection to the
        service, so we are using dummy data and an endpoint which does not exist.
        We want to avoid calls to the national registration by using a (valid) BSN.
        """
        try:
            with get_brp_client() as client:
                client.make_config_test_request()
        # Possibly no service or (valid) version is set.
        except NoServiceConfigured as exc:
            raise InvalidPluginConfiguration(_("Service not selected")) from exc
        except RuntimeError as exc:
            raise InvalidPluginConfiguration(exc.args[0]) from exc
        # The request itself can error
        except requests.RequestException as exc:
            raise InvalidPluginConfiguration(
                _("Client error: {exception}").format(exception=exc)
            ) from exc

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:haalcentraal_haalcentraalconfig_change",
                    args=(HaalCentraalConfig.singleton_instance_id,),
                ),
            ),
        ]
