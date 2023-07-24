import logging
from collections.abc import Sequence
from typing import Protocol

from requests import RequestException
from zds_client import ClientError

from openforms.pre_requests.clients import PreRequestClientContext, PreRequestZGWClient
from openforms.typing import JSONObject

logger = logging.getLogger(__name__)


class HaalCentraalClient(Protocol):
    context: PreRequestClientContext | None

    def __init__(self, service_client: PreRequestZGWClient):  # pragma: no cover
        ...

    def find_person(self, bsn: str, **kwargs) -> JSONObject | None:  # pragma: no cover
        ...


class BaseClient:
    def __init__(self, service_client: PreRequestZGWClient):
        self.service_client = service_client

    @property
    def context(self) -> PreRequestClientContext | None:
        return self.service_client.context

    @context.setter
    def context(self, context: PreRequestClientContext) -> None:
        self.service_client.context = context


class HaalCentraalV1Client(BaseClient):
    """
    Haal Centraal 1.3 compatible client.
    """

    def find_person(self, bsn: str, **kwargs) -> JSONObject | None:
        try:
            data = self.service_client.retrieve(
                "ingeschrevenpersonen",
                burgerservicenummer=bsn,
                url=f"ingeschrevenpersonen/{bsn}",
                request_kwargs={
                    "headers": {"Accept": "application/hal+json"},
                },
            )
        except (ClientError, RequestException) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        return data


class HaalCentraalV2Client(BaseClient):
    """
    Haal Centraal 2.0 compatible client.
    """

    def find_person(self, bsn: str, **kwargs) -> JSONObject | None:
        attributes: Sequence[str] = kwargs.pop("attributes")
        body = {
            "type": "RaadpleegMetBurgerservicenummer",
            "burgerservicenummer": [bsn],
            "fields": attributes,
        }

        try:
            data = self.service_client.operation(
                "Personen",
                data=body,
                url="personen",
                request_kwargs={
                    "headers": {"Content-Type": "application/json; charset=utf-8"}
                },
            )
            assert isinstance(data, dict)
        except (ClientError, RequestException) as e:
            logger.exception("exception while making request", exc_info=e)
            return

        if not data.get("personen"):
            logger.debug("Personen not found")
            return

        return data["personen"][0]
