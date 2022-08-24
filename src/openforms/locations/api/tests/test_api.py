from unittest.mock import patch

from django.conf import settings
from django.core.cache import caches
from django.test import TestCase, override_settings, tag
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

CACHES = settings.CACHES.copy()
CACHES["default"] = {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}


@override_settings(CACHES=CACHES)
class GetStreetNameAndCityViewAPITests(SubmissionsMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.submission = SubmissionFactory.create()

    def setUp(self):
        super().setUp()
        caches["default"].clear()
        self.addCleanup(caches["default"].clear)
        self._add_submission_to_session(self.submission)

    @patch("openforms.locations.api.views.import_string")
    def test_getting_street_name_and_city(self, import_string_mock):
        import_string_mock.return_value.get_address.return_value = {
            "street_name": "Keizersgracht",
            "city": "Amsterdam",
        }

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?postcode=1015CJ&house_number=117"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()["streetName"], "Keizersgracht")
        self.assertEqual(response.json()["city"], "Amsterdam")

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_getting_street_name_and_city_without_post_code_returns_error(self, _mock):

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?house_number=117"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "type": "http://testserver/fouten/ValidationError/",
                "code": "invalid",
                "title": _("Invalid input."),
                "status": 400,
                "detail": "",
                "instance": "urn:uuid:95a55a81-d316-44e8-b090-0519dd21be5f",
                "invalidParams": [
                    {
                        "name": "postcode",
                        "code": "required",
                        "reason": _("This field is required."),
                    }
                ],
            },
        )

    @patch(
        "openforms.api.exception_handling.uuid.uuid4",
        return_value="95a55a81-d316-44e8-b090-0519dd21be5f",
    )
    def test_getting_street_name_and_city_without_house_number_returns_error(
        self, _mock
    ):

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?postcode=1015CJ"
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "type": "http://testserver/fouten/ValidationError/",
                "code": "invalid",
                "title": _("Invalid input."),
                "status": 400,
                "detail": "",
                "instance": "urn:uuid:95a55a81-d316-44e8-b090-0519dd21be5f",
                "invalidParams": [
                    {
                        "name": "houseNumber",
                        "code": "required",
                        "reason": _("This field is required."),
                    }
                ],
            },
        )

    @patch("openforms.locations.api.views.import_string")
    def test_getting_street_name_and_city_with_extra_query_params_ignores_extra_param(
        self, import_string_mock
    ):
        import_string_mock.return_value.get_address.return_value = {
            "street_name": "Keizersgracht",
            "city": "Amsterdam",
        }

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?postcode=1015CJ&house_number=117&random=param"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()["streetName"], "Keizersgracht")
        self.assertEqual(response.json()["city"], "Amsterdam")

    @patch("openforms.locations.api.views.import_string")
    def test_address_not_found_returns_empty_200_response(self, import_string_mock):
        import_string_mock.return_value.get_address.return_value = {}

        response = self.client.get(
            f"{reverse('api:get-street-name-and-city-list')}?postcode=1015CJ&house_number=1"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    @tag("gh-1832")
    @patch("openforms.locations.api.views.import_string")
    def test_endpoint_uses_caching(self, import_string_mock):
        import_string_mock.return_value.get_address.return_value = {
            "street_name": "Keizersgracht",
            "city": "Amsterdam",
        }
        endpoint = reverse("api:get-street-name-and-city-list")

        # make the request twice, second one should use cache
        self.client.get(endpoint, {"postcode": "1015CJ", "house_number": "117"})
        self.client.get(endpoint, {"postcode": "1015CJ", "house_number": "117"})

        # assert that the client call was only made once
        import_string_mock.return_value.get_address.assert_called_once_with(
            "1015CJ", "117"
        )
