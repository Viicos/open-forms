# This TestCase contains a few tests that test implementation details
# to properly test the behaviour either integration with a mock
# mitmproxy, or some patch of the socket has to be done
#
# tests are tagged as such.

import signal
from pathlib import Path

from django.test import SimpleTestCase, override_settings, tag

from requests.exceptions import RequestException

from openforms.utils.tests.vcr import OFVCRMixin

from ..models import SoapService
from .factories import CertificateFactory, SoapServiceFactory

DATA_DIR = Path(__file__).parent / "data"


class SoapServiceTests(OFVCRMixin, SimpleTestCase):
    VCR_TEST_FILES = DATA_DIR

    def test_it_can_build_a_functional_client(self):
        service: SoapService = SoapServiceFactory.build(
            url="http://www.soapclient.com/xml/soapresponder.wsdl"
        )
        client = service.build_client()

        self.assertEqual(
            client.service.Method1("under the normal run", "things"),
            "Your input parameters are under the normal run and things",
        )

    @override_settings(DEFAULT_TIMEOUT_REQUESTS=1)
    def test_the_client_obeys_timeout_requests(self):
        "We don't want an unresponsive service DoS us."
        self.assertFalse(self.cassette.responses)

        service: SoapService = SoapServiceFactory.build(
            # this service acts like some slow lorris on https
            url="https://www.soapclient.com/xml/soapresponder.wsdl"
        )

        # signals aren't thread save
        org_handler = signal.getsignal(signal.SIGALRM)
        self.addCleanup(lambda: signal.signal(signal.SIGALRM, org_handler))
        signal.signal(
            signal.SIGALRM,
            lambda _sig, _frm: self.fail("Client seems to hang")
            # but there is a chance be that the service started responding, but we couldn't
            # process the wsdl in time
        )
        with self.assertRaises(RequestException):
            signal.alarm(5)
            # zeep will try to read the wsdl
            service.build_client()

            # Passed this point, the test has broken, find or create another test service
            # that opens the socket, but doesn't respond.
            self.fail("The service unexpectedly responded!")

    @tag("implementation_detail_requests")
    def test_client_has_server_cert_tls_configured(self):
        # Should just use the certificate (chain) of the pair
        certificate_pair = CertificateFactory.build(with_private_key=True)
        service: SoapService = SoapServiceFactory.build(
            url=f"file://{DATA_DIR / 'empty.wsdl'}", server_certificate=certificate_pair
        )
        client = service.build_client()
        self.assertEqual(
            client.transport.session.verify, certificate_pair.public_certificate.path
        )

    @tag("implementation_detail_requests")
    def test_full_mtls(self):
        service: SoapService = SoapServiceFactory.build(
            url=f"file://{DATA_DIR / 'empty.wsdl'}",
            with_server_cert=True,
            with_client_cert=True,
            client_certificate__with_private_key=True,
        )
        client = service.build_client()

        self.assertEqual(len(client.transport.session.cert), 2)
        # sanity check server cert
        self.assertTrue(client.transport.session.verify)
        self.assertNotEqual(client.transport.session.verify, True)

    @tag("implementation_detail_requests")
    def test_no_tls(self):
        service: SoapService = SoapServiceFactory.build(
            url=f"file://{DATA_DIR / 'empty.wsdl'}",
            with_server_cert=False,
            with_client_cert=False,
        )
        client = service.build_client()

        # still check tls against default chain
        self.assertEqual(client.transport.session.verify, True)
        # no client certs
        self.assertEqual(client.transport.session.cert, None)
