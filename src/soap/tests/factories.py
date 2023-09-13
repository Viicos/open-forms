from pathlib import Path

import factory
from simple_certmanager.constants import CertificateTypes

from ..models import SoapService

DATA_DIR = Path(__file__).parent.resolve() / "data"


class CertificateFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"certificate-{n}")
    type = CertificateTypes.cert_only
    public_certificate = factory.django.FileField(
        from_path=str(DATA_DIR / "test.certificate")
    )

    class Meta:
        model = "simple_certmanager.Certificate"

    class Params:
        with_private_key = factory.Trait(
            private_key=factory.django.FileField(from_path=str(DATA_DIR / "test.key")),
            type=CertificateTypes.key_pair,
        )


class SoapServiceFactory(factory.django.DjangoModelFactory):
    label = factory.Sequence(lambda n: f"soap-service-{n}")
    url = "http://zaken/soap/"

    class Meta:
        model = SoapService

    class Params:
        with_server_cert = factory.Trait(
            server_certificate=factory.SubFactory(
                CertificateFactory,
                public_certificate__filename="server.cert",
            ),
        )
        with_client_cert = factory.Trait(
            client_certificate=factory.SubFactory(
                CertificateFactory,
                public_certificate__filename="client.cert",
            ),
        )
