from pathlib import Path

from django.core.files import File
from django.test import TestCase, override_settings
from django.urls import reverse

from digid_eherkenning.models.digid import DigidConfiguration
from privates.test import temp_private_root

from openforms.config.constants import CSPDirective
from openforms.config.models import CSPSetting
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.utils.tests.cache import clear_caches
from simple_certmanager_ext.tests.factories import CertificateFactory

TEST_FILES = Path(__file__).parent / "data"
METADATA = TEST_FILES / "metadata.xml"


@temp_private_root()
@override_settings(CORS_ALLOW_ALL_ORIGINS=True, IS_HTTPS=True)
class CSPUpdateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cert = CertificateFactory.create(label="DigiD", with_private_key=True)

        cls.config = DigidConfiguration.get_solo()

        cls.config.certificate = cert
        cls.config.idp_service_entity_id = "https://test-digid.nl"
        cls.config.want_assertions_signed = False
        cls.config.entity_id = "https://test-sp.nl"
        cls.config.base_url = "https://test-sp.nl"
        cls.config.service_name = "Test"
        cls.config.service_description = "Test description"
        cls.config.slo = False

        with METADATA.open("rb") as md_file:
            cls.config.idp_metadata_file = File(md_file, METADATA.name)
            cls.config.save()

    def setUp(self):
        super().setUp()

        clear_caches()
        self.addCleanup(clear_caches)

    def test_csp_updates(self):
        # assert no csp entry is created
        self.assertTrue(CSPSetting.objects.none)

        # assert csp entry is updated
        self.config.idp_service_entity_id = (
            "https://test-digid.nl https://updated-test-digid.nl"
        )
        self.config.save()

        csp_1 = CSPSetting.objects.get()

        self.assertEqual(csp_1.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(
            csp_1.value,
            "'self' https://digid.nl https://*.digid.nl https://test-digid.nl https://updated-test-digid.nl",
        )

        # assert new csp entry is added and the old one is deleted
        self.config.idp_service_entity_id = "https://test-digid.nl"
        self.config.save()

        # old entry
        self.assertFalse(CSPSetting.objects.filter(pk=csp_1.pk).exists())

        # new entry
        csp_2 = CSPSetting.objects.get()

        self.assertEqual(csp_2.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(
            csp_2.value,
            "'self' https://digid.nl https://*.digid.nl https://test-digid.nl",
        )

    def test_response_headers_contain_form_action_values(self):
        form = FormFactory.create(authentication_backends=["digid"])
        form_definition = FormDefinitionFactory.create(login_required=True)
        FormStepFactory.create(form_definition=form_definition, form=form)

        login_url = reverse(
            "authentication:start", kwargs={"slug": form.slug, "plugin_id": "digid"}
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}?_start=1"

        # redirect_to_digid_login
        response = self.client.get(f"{login_url}?next={form_url}", follow=True)

        self.assertIn(
            "form-action 'self' https://digid.nl https://*.digid.nl https://test-digid.nl;",
            response.headers["Content-Security-Policy"],
        )
