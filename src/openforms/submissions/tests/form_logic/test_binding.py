from functools import lru_cache
from pathlib import Path
from typing import Any
from unittest import skip
from urllib.parse import unquote

from django.test import SimpleTestCase

import requests_mock
from factory.django import FileField
from furl import furl
from hypothesis import assume, example, given, settings, strategies as st
from zgw_consumers.constants import APITypes, AuthTypes

from openforms.forms.tests.factories import FormVariableFactory
from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory
from openforms.variables.constants import DataMappingTypes
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory
from openforms.variables.validators import HeaderValidator, ValidationError

from ...logic.binding import bind

DEFAULT_REQUEST_HEADERS = {
    "Accept",
    "Accept-Encoding",
    "Connection",
    "Content-Type",
    "User-Agent",
}


def data_mapping_values() -> st.SearchStrategy[Any]:
    "Generates values for the value side of openforms.typing.DataMapping"
    return st.one_of(st.text(), st.integers(), st.floats(), st.dates(), st.datetimes())


# the first test in the process might take too much time
settings.register_profile("django", deadline=500)
settings.load_profile("django")


class ServiceFetchConfigVariableBindingTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = ServiceFactory.build(
            api_type=APITypes.orc,
            api_root="https://httpbin.org/",
            auth_type=AuthTypes.no_auth,
            oas_file=FileField(
                from_path=str(Path(__file__).parent.parent / "files" / "openapi.yaml")
            ),
        )
        # prevent parsing the yaml over and over and over
        cls.service.id = 1  # need pk for __hash__
        cls.service.build_client = lru_cache(1)(cls.service.build_client)

    @requests_mock.Mocker()
    def test_it_performs_simple_get(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})
        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="get",
            )
        )

        value = bind(var, {})

        self.assertEqual(value["url"], "https://httpbin.org/get")

    @given(data_mapping_values())
    @example("../otherendpoint")
    @example("./../.")
    @example("foo/.")
    def test_it_can_construct_simple_path_parameters(self, field_value):
        assume(field_value != ".")  # request_mock eats the single dot :pacman:
        # https://swagger.io/docs/specification/describing-parameters/#path-parameters
        context = {"seconds": field_value}

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="delay/{seconds}",  # this is not defined as number in the OAS
            )
        )

        with requests_mock.Mocker() as m:
            m.get(requests_mock.ANY)
            _ = bind(var, context)
            request = m.last_request

        head, rest = request.url[:26], request.url[26:]
        self.assertEqual(head, "https://httpbin.org/delay/")
        # the service should get the value
        self.assertEqual(unquote(rest), str(field_value))

        # I guess if the rest is unmangled, the rest of the assertions are not
        # really needed; I think
        # ∄ a way for Bobby Tables to drop a table ∧ become an unmangled entry in it
        # but asserting is cheaper than a CVE

        # it shouldn't change other parts of the request
        self.assertIs(request.body, None)
        self.assertIs(request.query, "")
        self.assertEqual(set(request.headers), DEFAULT_REQUEST_HEADERS)
        # and a weak assertion
        self.assertNotIn(str(field_value), request.headers.values())

    @skip("TODO")
    @given(
        st.one_of(
            st.lists(elements=data_mapping_values()),
            st.dictionaries(
                keys=st.text(), values=st.one_of(st.text(), st.integers(), st.floats())
            ),
        )
    )
    def test_it_can_construct_product_type_path_parameters(self, field_value):
        # serialize lists and dicts of values as specified by `style` and
        # `explode` in the oas-spec of the service
        # https://swagger.io/docs/specification/serialization/
        ...

    @given(
        field_value=data_mapping_values(),
        question_mark=st.one_of(st.just("?"), st.just("")),  # optional
    )
    def test_it_can_construct_simple_query_parameters(self, field_value, question_mark):
        # https://swagger.io/docs/specification/describing-parameters/#query-parameters
        context = {"some_field": field_value}

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="response-headers",
                query_params=question_mark + "freeform={some_field}",
            )
        )

        with requests_mock.Mocker(case_sensitive=True) as m:
            m.get(
                furl("https://httpbin.org/response-headers")
                .set({"freeform": field_value})
                .url
            )
            _ = bind(var, context)
            request = m.last_request

        # it shouldn't change other parts of the request
        self.assertIs(request.body, None)
        self.assertEqual(set(request.headers), DEFAULT_REQUEST_HEADERS)
        # and a weak assertion
        self.assertNotIn(str(field_value), request.headers.values())

    @given(
        st.text(),  # OAS schema: type: string
        data_mapping_values(),
    )
    def test_it_can_construct_multiple_simple_query_parameters(
        self, some_text, some_value
    ):
        # https://swagger.io/docs/specification/describing-parameters/#query-parameters
        context = {"url": some_text, "code": some_value}

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="redirect-to",
                query_params="?status_code={code}&url={url}",
            )
        )

        with requests_mock.Mocker(case_sensitive=True) as m:
            m.get(
                furl("https://httpbin.org/redirect-to")
                .set({"url": some_text, "status_code": some_value})
                .url
            )
            _ = bind(var, context)
            request = m.last_request

        # it shouldn't change other parts of the request
        self.assertIs(request.body, None)
        self.assertEqual(set(request.headers), DEFAULT_REQUEST_HEADERS)
        # and some weak assertions
        self.assertNotIn(str(some_text), request.headers.values())
        self.assertNotIn(str(some_value), request.headers.values())

    @skip("TODO")
    @given(
        st.one_of(
            st.lists(elements=st.one_of(st.text(), st.integers(), st.floats())),
            st.dictionaries(
                keys=st.text(), values=st.one_of(st.text(), st.integers(), st.floats())
            ),
        )
    )
    def test_it_can_construct_product_type_query_parameters(self, field_value):
        # serialize lists and dicts of values as specified by `style` and
        # `explode` in the oas-spec of the service
        # https://swagger.io/docs/specification/serialization/
        ...

    @requests_mock.Mocker()
    def test_it_sends_request_headers(self, m):
        m.get("https://httpbin.org/get")

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="get",
                headers={"X-Brony-Identity": "Jumper"},
            )
        )

        _ = bind(var, {})
        request_headers = m.last_request.headers

        self.assertIn(("X-Brony-Identity", "Jumper"), request_headers.items())

    @given(
        st.one_of(
            st.text(
                # blacklist invisible control characters
                alphabet=st.characters(blacklist_categories=("C"))
            ),
            st.integers(),
            st.floats(),
            st.dates(),
            st.datetimes(),
        )
    )
    def test_it_can_construct_simple_header_parameters(self, field_value):
        "Assert the happy path"
        # https://swagger.io/docs/specification/describing-parameters/#header-parameters
        context = {"some_value": field_value}
        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="cache",
                # our OAS spec doesn't care what ETags look like.
                headers={"If-None-Match": "{some_value}"},
            )
        )

        # force unicode into a str with just characters in [\x00 .. \xff]
        expected_value = str(field_value).strip().encode("utf-8").decode("latin1")

        with requests_mock.Mocker(case_sensitive=True) as m:
            m.get("https://httpbin.org/cache")
            _ = bind(var, context)
            request = m.last_request

        self.assertIn(("If-None-Match", expected_value), request.headers.items())
        # it should not add any other headers
        self.assertEquals(
            set(request.headers), {"If-None-Match"}.union(DEFAULT_REQUEST_HEADERS)
        )
        # assert headers we sent were valid RFC 9110 (requests doesn't
        # guarantee this, it just checks for CR but it will happily send \x00)
        HeaderValidator()(request.headers)

        # it shouldn't change other parts of the request
        self.assertIs(request.body, None)
        self.assertEqual(request.path, "/cache")
        self.assertEqual(len(request.qs), 0)

    @given(data_mapping_values())
    @example("Little Bobby Tables\r\nX-Other-Header: Some value")
    def test_it_never_sends_bad_headers_regardless_of_what_people_submit(
        self, field_value
    ):
        context = {"some_value": field_value}
        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="cache",
                headers={"If-None-Match": "{some_value}"},
            )
        )

        with requests_mock.Mocker(case_sensitive=True) as m:
            m.get("https://httpbin.org/cache")
            try:
                # when we bind
                _ = bind(var, context)
            except Exception:  # XXX unclear what exception to expect
                # either raise an exception
                return

        # or place a welformed request
        request = m.last_request
        try:
            HeaderValidator()(request.headers)
        except ValidationError as e:
            raise self.failureException("bind sent bad headers!") from e

    @requests_mock.Mocker()
    def test_it_sends_the_body_as_json(self, m):
        m.get("https://httpbin.org/anything", json="Armour")

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="anything",
                body="Armour",
            )
        )

        _ = bind(var, {})
        request = m.last_request

        self.assertIn(("Content-Type", "application/json"), request.headers.items())
        self.assertEqual(request.body, b'"Armour"')

    @requests_mock.Mocker()
    def test_it_applies_jsonlogic_on_response(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="get",
                data_mapping_type=DataMappingTypes.json_logic,
                mapping_expression={"var": "url"},
            )
        )

        value = bind(var, {})

        self.assertEqual(value, "https://httpbin.org/get")

    @requests_mock.Mocker()
    def test_it_applies_jq_on_response(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="get",
                data_mapping_type=DataMappingTypes.jq,
                mapping_expression=".url",
            )
        )

        value = bind(var, {})

        self.assertEqual(value, "https://httpbin.org/get")

    @skip("This will go into an infinite loop")
    @requests_mock.Mocker()
    def test_it_does_not_hang_on_infinite_jq_recursion(self, m):
        m.get("https://httpbin.org/get", json={"url": "https://httpbin.org/get"})

        var = FormVariableFactory.build(
            service_fetch_configuration=ServiceFetchConfigurationFactory.build(
                service=self.service,
                path="get",
                data_mapping_type=DataMappingTypes.jq,
                mapping_expression="[while(.;.)]",
            )
        )

        value = bind(var, {})

        self.assertEqual(value, "https://httpbin.org/get")

    def test_it_does_not_swallow_unknown_types(self):
        var = FormVariableFactory.build()

        with self.assertRaises(NotImplementedError):
            bind(var, {})
