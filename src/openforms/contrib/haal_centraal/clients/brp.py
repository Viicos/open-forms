"""
Haal Centraal BRP Personen bevragen API client implementations.

Open Forms supports v1 and v2 of the APIs.

Documentation for v2: https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/getting-started
"""
import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

import requests
from ape_pie import APIClient

from openforms.contrib.hal_client import HALMixin
from openforms.pre_requests.clients import PreRequestMixin
from openforms.typing import JSONObject

from ..constants import BRPVersions

logger = logging.getLogger(__name__)

# DATA MODEL DEFINITIONS


@dataclass
class Name:
    voornamen: str
    voorvoegsel: str
    geslachtsnaam: str


@dataclass
class Person:
    bsn: str
    name: Name


# CLIENT IMPLEMENTATIONS


class BRPClient(PreRequestMixin, ABC, APIClient):
    @abstractmethod
    def find_person(self, bsn: str, **kwargs) -> JSONObject | None:  # pragma: no cover
        ...

    @abstractmethod
    def get_family_members(
        self, bsn: str, include_children: bool, include_partner: bool
    ) -> list[Person]:  # pragma: no cover
        """
        Look up the partner(s) and/or the children of the person with the given BSN.
        """
        ...

    @abstractmethod
    def make_config_test_request(self) -> None:  # pragma: no cover
        ...


class V1Client(HALMixin, BRPClient):
    """
    BRP Personen Bevragen 1.3 compatible client.

    Hosted API Documentation: https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v1/redoc
    """

    def find_person(self, bsn: str, **kwargs) -> JSONObject | None:
        try:
            response = self.get(f"ingeschrevenpersonen/{bsn}")
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.exception("exception while making request", exc_info=exc)
            return None

        return response.json()

    def _get_children(self, bsn: str) -> list[Person]:
        response = self.get(f"ingeschrevenpersonen/{bsn}/kinderen")
        response.raise_for_status()
        response_data = response.json()["_embedded"]

        persons = []
        for kind in response_data["kinderen"]:
            name_data = kind["naam"]
            person = Person(
                bsn=kind["burgerservicenummer"],
                name=Name(
                    voornamen=name_data["voornamen"],
                    voorvoegsel=name_data["voorvoegsel"],
                    geslachtsnaam=name_data["geslachtsnaam"],
                ),
            )
            persons.append(person)
        return persons

    def _get_partner(self, bsn: str) -> list[Person]:
        response = self.get(f"ingeschrevenpersonen/{bsn}/partners")
        response.raise_for_status()
        response_data = response.json()["_embedded"]

        persons = []
        for partner in response_data["partners"]:
            name_data = partner["naam"]
            person = Person(
                bsn=partner["burgerservicenummer"],
                name=Name(
                    voornamen=name_data["voornamen"],
                    voorvoegsel=name_data["voorvoegsel"],
                    geslachtsnaam=name_data["geslachtsnaam"],
                ),
            )
            persons.append(person)
        return persons

    def get_family_members(
        self, bsn: str, include_children: bool, include_partner: bool
    ) -> list[Person]:
        family_members = []
        if include_children:
            family_members += self._get_children(bsn)

        if include_partner:
            family_members += self._get_partner(bsn)

        return family_members

    def make_config_test_request(self):
        # expected to 404
        response = self.get("test")
        if response.status_code != 404:
            response.raise_for_status()


class V2Client(BRPClient):
    """
    BRP Personen Bevragen 2.0 compatible client.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # requests encodes the json kwarg as utf-8, no extra action needed
        self.headers["Content-Type"] = "application/json; charset=utf-8"

    def find_person(
        self, bsn: str, reraise_errors: bool = False, **kwargs
    ) -> JSONObject | None:
        attributes: Sequence[str] = kwargs.pop("attributes")
        body = {
            "type": "RaadpleegMetBurgerservicenummer",
            "burgerservicenummer": [bsn],
            "fields": attributes,
        }

        try:
            response = self.post("personen", json=body)
            response.raise_for_status()
        except requests.RequestException as exc:
            if reraise_errors:
                raise exc
            logger.exception("exception while making request", exc_info=exc)
            return None

        data = response.json()
        assert isinstance(data, dict)

        if not (personen := data.get("personen", [])):
            logger.debug("Person not found")
            return None

        return personen[0]

    def get_family_members(
        self, bsn: str, include_children: bool, include_partner: bool
    ) -> list[Person]:
        fields = []
        if include_children:
            fields += ["kinderen.burgerservicenummer", "kinderen.naam"]
        if include_partner:
            fields += ["partners.burgerservicenummer", "partners.naam"]

        body = {
            "type": "RaadpleegMetBurgerservicenummer",
            "burgerservicenummer": [bsn],
            "fields": fields,
        }
        response = self.post("personen", json=body)
        response.raise_for_status()

        data = response.json()
        if not (personen := data.get("personen", [])):
            logger.debug("Person not found")
            return []

        family_data = []
        if include_children:
            family_data += personen[0]["kinderen"]
        if include_partner:
            family_data += personen[0]["partners"]

        family_members = [
            Person(
                bsn=family_member["burgerservicenummer"],
                name=Name(
                    voornamen=family_member["naam"]["voornamen"],
                    voorvoegsel=family_member["naam"].get("voorvoegsel", ""),
                    geslachtsnaam=family_member["naam"]["geslachtsnaam"],
                ),
            )
            for family_member in family_data
        ]
        return family_members

    def make_config_test_request(self):
        try:
            self.find_person(
                bsn="test",
                attributes=["burgerservicenummer"],
                reraise_errors=True,
            )
        except requests.HTTPError as exc:
            if (response := exc.response) is not None and response.status_code == 400:
                return
            raise exc


CLIENT_CLS_FOR_VERSION: dict[BRPVersions, type[BRPClient]] = {
    BRPVersions.v13: V1Client,
    BRPVersions.v20: V2Client,
}
