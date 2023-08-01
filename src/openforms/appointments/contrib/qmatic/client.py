from requests import Session

from .models import QmaticConfig


class QmaticException(Exception):
    pass


class QmaticClient(Session):
    """
    Lightweight wrapper around Session to work with the API root and auth
    headers.
    """

    _config: QmaticConfig | None = None

    def _get_cert(self) -> None | str | tuple[str, str]:
        if not self._config:
            self._config = QmaticConfig.get_solo()

        certificate = self._config.service.client_certificate
        if not certificate:
            return None

        if certificate.public_certificate and certificate.private_key:
            return (certificate.public_certificate.path, certificate.private_key.path)

        if certificate.public_certificate:
            return certificate.public_certificate.path

    def request(self, method: str, url: str, *args, **kwargs):
        if not self._config:
            config = QmaticConfig.get_solo()
            assert isinstance(config, QmaticConfig)
            self._config = config

        api_root = self._config.service.api_root
        _temp_client = self._config.service.build_client()
        headers = {
            "Content-Type": "application/json",
            **_temp_client.auth_header,
        }
        del _temp_client

        url = f"{api_root}{url}"
        response = super().request(
            method, url, headers=headers, cert=self._get_cert(), *args, **kwargs
        )

        if response.status_code == 500:
            error_msg = response.headers.get(
                "error_message", response.content.decode("utf-8")
            )
            raise QmaticException(
                f"Server error (HTTP {response.status_code}): {error_msg}"
            )

        return response
