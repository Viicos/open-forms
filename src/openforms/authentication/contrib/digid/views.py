import logging
from collections import namedtuple

from django.http import HttpResponseRedirect

from digid_eherkenning.backends import BaseSaml2Backend
from digid_eherkenning.choices import SectorType
from digid_eherkenning.saml2.digid import DigiDClient
from digid_eherkenning.views import (
    DigiDAssertionConsumerServiceView as _DigiDAssertionConsumerServiceView,
)
from onelogin.saml2.errors import OneLogin_Saml2_ValidationError

from .constants import DIGID_AUTH_SESSION_KEY
from .mixins import AssertionConsumerServiceMixin

logger = logging.getLogger(__name__)


class BSNNotPresentError(Exception):
    pass


DIGID_MESSAGE_PARAMETER = "_digid-message"
LOGIN_CANCELLED = "login-cancelled"
GENERIC_LOGIN_ERROR = "error"


class DigiDAssertionConsumerServiceView(
    AssertionConsumerServiceMixin,
    BaseSaml2Backend,
    _DigiDAssertionConsumerServiceView,
):
    """Process step 5, 6 and 7 of the authentication

    This class overwrites the digid_eherkenning class, because we don't need to use the authentication backend.
    We just need to receive the BSN number.
    """

    def get(self, request):
        saml_art = request.GET.get("SAMLart")
        client = DigiDClient()

        try:
            response = client.artifact_resolve(request, saml_art)
            logger.debug(response.pretty_print())
        except OneLogin_Saml2_ValidationError as exc:
            if exc.code == OneLogin_Saml2_ValidationError.STATUS_CODE_AUTHNFAILED:
                failure_url = self.get_failure_url(
                    DIGID_MESSAGE_PARAMETER, LOGIN_CANCELLED
                )
            else:
                logger.error(exc)
                failure_url = self.get_failure_url(
                    DIGID_MESSAGE_PARAMETER, GENERIC_LOGIN_ERROR
                )
            return HttpResponseRedirect(failure_url)

        try:
            name_id = response.get_nameid()
            assert isinstance(name_id, str)
        except OneLogin_Saml2_ValidationError as exc:
            logger.error(exc)
            failure_url = self.get_failure_url(
                DIGID_MESSAGE_PARAMETER, GENERIC_LOGIN_ERROR
            )
            return HttpResponseRedirect(failure_url)

        bits = name_id.split(":")

        # Sectorcode missing; assume BSN as SOFI aren't issued since
        # Aanpassingswet Brp in 2014
        if len(bits) == 1:
            bits.insert(0, SectorType.bsn)

        sector_code, bsn = bits
        # We only care about users with a BSN.
        if sector_code != SectorType.bsn:
            raise BSNNotPresentError

        # store the bsn itself in the session, and let the plugin decide where
        # to persist it. This is an implementation detail for this specific plugin!
        request.session[DIGID_AUTH_SESSION_KEY] = bsn

        return HttpResponseRedirect(self.get_success_url())
