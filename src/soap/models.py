from typing import NewType

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from requests import Session
from simple_certmanager.models import Certificate
from zeep.client import Client, Transport

from .constants import EndpointSecurity, SOAPVersion

CertificatePath = NewType("CertificatePath", str)
PrivateKeyPath = NewType("PrivateKeyPath", str)


class SoapService(models.Model):
    label = models.CharField(
        _("label"),
        max_length=100,
        help_text=_("Human readable label to identify services"),
    )
    url = models.URLField(
        _("URL"),
        blank=True,
        help_text=_("URL of the service to connect to."),
    )

    soap_version = models.CharField(
        _("SOAP version"),
        max_length=5,
        default=SOAPVersion.soap12,
        choices=SOAPVersion.choices,
        help_text=_("The SOAP version to use for the message envelope."),
    )

    endpoint_security = models.CharField(
        _("Security"),
        max_length=20,
        blank=True,
        choices=EndpointSecurity.choices,
        help_text=_("The security to use for messages sent to the endpoints."),
    )

    user = models.CharField(
        _("user"),
        max_length=200,
        blank=True,
        help_text=_("Username to use in the XML security context."),
    )
    password = models.CharField(
        _("password"),
        max_length=200,
        blank=True,
        help_text=_("Password to use in the XML security context."),
    )

    client_certificate = models.ForeignKey(
        Certificate,
        blank=True,
        null=True,
        help_text=_(
            "The SSL certificate file used for client identification. If left empty, mutual TLS is disabled."
        ),
        on_delete=models.PROTECT,
        related_name="soap_services_client",
    )
    server_certificate = models.ForeignKey(
        Certificate,
        blank=True,
        null=True,
        help_text=_("The SSL/TLS certificate of the server"),
        on_delete=models.PROTECT,
        related_name="soap_services_server",
    )

    class Meta:
        verbose_name = _("SOAP service")
        verbose_name_plural = _("SOAP services")

    def __str__(self):
        return self.label

    @property
    def cert(
        self,
    ) -> None | CertificatePath | tuple[CertificatePath, PrivateKeyPath]:
        match self.client_certificate:
            case Certificate(public_certificate=cert, private_key=key) if cert and key:
                return CertificatePath(cert.path), PrivateKeyPath(key.path)
            case Certificate(public_certificate=cert) if cert:
                return CertificatePath(cert.path)
        return None

    @property
    def verify(self) -> CertificatePath | bool:
        match self.server_certificate:
            case Certificate(public_certificate=cert) if cert:
                return CertificatePath(cert.path)
        return True

    def build_client(self) -> Client:
        """
        Build an SOAP API client from the service configuration.
        """
        session = Session()
        session.cert = self.cert
        session.verify = self.verify

        client = Client(
            self.url,
            transport=Transport(
                timeout=settings.DEFAULT_TIMEOUT_REQUESTS,
                session=session,
            ),
        )

        return client
