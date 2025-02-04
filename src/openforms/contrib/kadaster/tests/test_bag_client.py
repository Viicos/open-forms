import json
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

import requests
import requests_mock

from zgw_consumers_ext.tests.factories import ServiceFactory

from ..clients import get_bag_client
from ..models import KadasterApiConfig

TEST_FILES = Path(__file__).parent.resolve() / "files"


def _load_json_mock(name):
    with (TEST_FILES / name).open("r") as f:
        return json.load(f)


class BAGClientTests(SimpleTestCase):
    def setUp(self):
        super().setUp()

        config = KadasterApiConfig(
            search_service=None,  # unused, but would otherwise execute queries
            bag_service=ServiceFactory.build(
                api_root="https://bag/api/",
                oas="https://bag/api/schema/openapi.yaml",
            ),
        )
        patcher = patch(
            "openforms.contrib.kadaster.clients.KadasterApiConfig.get_solo",
            return_value=config,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @requests_mock.Mocker()
    def test_client_returns_street_name_and_city(self, m):
        m.get(
            "https://bag/api/adressen?postcode=1015CJ&huisnummer=117",
            status_code=200,
            json=_load_json_mock("addresses.json"),
        )

        with get_bag_client() as client:
            address_data = client.get_address("1015CJ", "117")

        assert address_data is not None
        self.assertEqual(address_data.street_name, "Keizersgracht")
        self.assertEqual(address_data.city, "Amsterdam")

    @requests_mock.Mocker()
    def test_client_returns_empty_value_when_no_results_are_found(self, m):
        m.get(
            "https://bag/api/adressen?postcode=1015CJ&huisnummer=1",
            status_code=200,
            json={},
        )

        with get_bag_client() as client:
            address_data = client.get_address("1015CJ", "1")

        self.assertIsNone(address_data)

    @requests_mock.Mocker()
    def test_client_returns_empty_value_when_client_exception_is_thrown(self, m):
        m.get(
            "https://bag/api/adressen?postcode=1015CJ&huisnummer=115",
            exc=requests.RequestException,
        )

        with get_bag_client() as client:
            address_data = client.get_address("1015CJ", "115")

        self.assertIsNone(address_data)
