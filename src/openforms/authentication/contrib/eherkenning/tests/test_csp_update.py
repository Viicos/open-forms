from pathlib import Path

from django.core.files import File
from django.test import TestCase
from django.urls import reverse

from digid_eherkenning.models.eherkenning import EherkenningConfiguration
from privates.test import temp_private_root

from openforms.config.constants import CSPDirective
from openforms.config.models import CSPSetting
from openforms.forms.tests.factories import FormFactory
from openforms.utils.tests.cache import clear_caches
from simple_certmanager_ext.tests.factories import CertificateFactory

TEST_FILES = Path(__file__).parent / "data"
METADATA = TEST_FILES / "eherkenning-metadata.xml"


@temp_private_root()
class CSPUpdateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cert = CertificateFactory.create(label="eHerkenning", with_private_key=True)

        cls.config = EherkenningConfiguration.get_solo()

        cls.config.certificate = cert
        cls.config.idp_service_entity_id = (
            "urn:etoegang:DV:00000001111111111000:entities:9000"
        )
        cls.config.want_assertions_signed = False
        cls.config.entity_id = "https://test-sp.nl"
        cls.config.base_url = "https://test-sp.nl"
        cls.config.service_name = "Test"
        cls.config.service_description = "Test"
        cls.config.loa = "urn:etoegang:core:assurance-class:loa3"
        cls.config.oin = "00000001111111111000"
        cls.config.no_eidas = True
        cls.config.privacy_policy = "https://test-sp.nl/privacy_policy"
        cls.config.makelaar_id = "00000002222222222000"
        cls.config.organization_name = "Test Organisation"

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
        self.config.idp_service_entity_id = "https://updated-test-eherkenning.nl"
        self.config.save()

        csp_1 = CSPSetting.objects.get()

        self.assertEqual(csp_1.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(
            csp_1.value,
            "'self' https://updated-test-eherkenning.nl",
        )

        # assert new csp entry is added and the old one is deleted
        self.config.idp_service_entity_id = "https://new-test-eherkenning.nl"
        self.config.save()

        # old entry
        self.assertFalse(CSPSetting.objects.filter(pk=csp_1.pk).exists())

        # new entry
        csp_2 = CSPSetting.objects.get()

        self.assertEqual(csp_2.directive, CSPDirective.FORM_ACTION)
        self.assertEqual(csp_2.value, "'self' https://new-test-eherkenning.nl")

    def test_response_headers_contain_form_action_values(self):
        form = FormFactory.create(
            authentication_backends=["eherkenning"],
            generate_minimal_setup=True,
            formstep__form_definition__login_required=True,
        )
        login_url = reverse(
            "authentication:start",
            kwargs={"slug": form.slug, "plugin_id": "eherkenning"},
        )
        form_path = reverse("core:form-detail", kwargs={"slug": form.slug})
        form_url = f"http://testserver{form_path}"

        # redirect_to_eherkenning_login
        response = self.client.get(login_url, {"next": form_url}, follow=True)

        self.assertIn(
            "form-action 'self' urn:etoegang:DV:00000001111111111000:entities:9000;",
            response.headers["Content-Security-Policy"],
        )
