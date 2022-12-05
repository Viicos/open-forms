from unittest.mock import patch

from django.test import TestCase

import requests_mock

from openforms.prefill.contrib.haalcentraal.tests.utils import load_binary_mock
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory

from ..base import PreRequestHookBase
from ..registry import Registry


class PreRequestHooksTest(TestCase):
    def test_pre_request_hook(self):
        register = Registry()

        @register("test-hook")
        class PreRequestHook(PreRequestHookBase):
            def __call__(self, url, method, **kwargs):
                headers = kwargs.get("headers", {})
                headers.update({"test": "test"})

        some_service = ServiceFactory(
            api_root="https://personen/api/",
            oas="https://personen/api/schema/openapi.yaml",
        )
        client = some_service.build_client()

        with requests_mock.Mocker() as m:
            m.get(
                "https://personen/api/schema/openapi.yaml?v=3",
                status_code=200,
                content=load_binary_mock("personen.yaml"),
            )
            m.get(
                "https://personen/api/test/path",
                status_code=200,
            )

            with patch("openforms.pre_requests.clients.registry", new=register):
                client.request(path="/api/test/path", operation="test")

            last_request = m.request_history[-1]

            self.assertIn("test", last_request.headers)
            self.assertEqual("test", last_request.headers["test"])
