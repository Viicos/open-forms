import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypedDict, cast
from urllib.parse import urlparse

from django.conf import settings

from cookie_consent.models import Cookie, CookieGroup

from openforms.config.models import CSPSetting
from openforms.typing import JSONObject

if TYPE_CHECKING:  # pragma: no cover
    from .models import AnalyticsToolsConfiguration, ToolConfiguration


CONTRIB_DIR = (Path(__file__).parent / "contrib").resolve()


class CookieDict(TypedDict):
    name: str
    path: str


class CSPDict(TypedDict):
    directive: str
    value: str


def update_analytics_tool(
    config: "AnalyticsToolsConfiguration",
    analytics_tool: str,
    is_activated: bool,
    tool_config: "ToolConfiguration",
):
    from openforms.logging import logevent

    if is_activated:
        logevent.enabling_analytics_tool(config, analytics_tool)
    else:
        logevent.disabling_analytics_tool(config, analytics_tool)

    # process the CSP headers
    csps = cast(list[CSPDict], load_asset("csp_headers.json", analytics_tool))
    for csp in csps:
        for replacement in tool_config.replacements:
            if not (field_name := replacement.field_name):
                continue  # we do not support callables for CSP
            replacement_value = getattr(config, field_name)
            csp["value"] = csp["value"].replace(
                replacement.needle, str(replacement_value)
            )

    # process the cookies
    cookies = cast(list[CookieDict], load_asset("cookies.json", analytics_tool))
    for cookie in cookies:
        for replacement in tool_config.replacements:
            if field_name := replacement.field_name:
                replacement_value = getattr(config, field_name)
            else:
                replacement_value = replacement.callback(cookie)
            cookie["name"] = cookie["name"].replace(
                replacement.needle, str(replacement_value)
            )

    update_analytical_cookies(
        cookies,
        create=is_activated,
        cookie_consent_group_id=config.analytics_cookie_consent_group.id,
    )
    update_csp(csps, create=is_activated)


def load_asset(
    asset: Literal["cookies.json", "csp_headers.json"],
    analytics_tool: str,
) -> list[JSONObject]:
    json_file = CONTRIB_DIR / analytics_tool / asset
    with json_file.open("r") as infile:
        return json.load(infile)


def get_cookie_domain() -> str:
    """
    Obtain the value for the cookie domain from the hostname.

    The value is taken from ``settings.BASE_URL`` as canonical source of "the" domain
    where Open Forms is deployed.
    """
    # extract the domain/host from the BASE_URL setting
    # RFC 6265 states that cookies are not bound to a port, so we must ignore that part.
    parsed = urlparse(settings.BASE_URL)
    return parsed.hostname


# Implementation based on updateDomainHash()
# see https://github.com/matomo-org/matomo/blob/a8d917778e75346eab9509ac9707f7e6e2e6c58d/js/piwik.js#L3048
def calculate_domain_hash(cookie_domain: str, cookie_path: str) -> str:
    domain_hash = hashlib.sha1(f"{cookie_domain}{cookie_path}".encode())
    return domain_hash.hexdigest()[:4]


def get_domain_hash(cookie: CookieDict) -> str:
    domain = get_cookie_domain()
    return calculate_domain_hash(domain, cookie_path=cookie["path"])


def update_analytical_cookies(
    cookies: list[CookieDict], create: bool, cookie_consent_group_id: int
):
    if create:
        cookie_domain = get_cookie_domain()
        cookie_group = CookieGroup.objects.get(id=cookie_consent_group_id)
        instances = [
            Cookie(
                name=cookie["name"],
                # NOTE: if/when OF is hosted on a subpath, that should be taken into
                # account as well in a dynamic way... django.urls.get_script_prefix
                # could be used for this, but perhaps using the path part of settings.BASE_URL
                # is more predictable
                path=cookie["path"],
                domain=cookie_domain,
                cookiegroup=cookie_group,
            )
            for cookie in cookies
        ]
        Cookie.objects.bulk_create(instances)
    else:
        Cookie.objects.filter(name__in=[cookie["name"] for cookie in cookies]).delete()


def update_csp(csps: list[CSPDict], create: bool):
    if create:
        instances = [
            CSPSetting(directive=csp["directive"], value=csp["value"]) for csp in csps
        ]
        CSPSetting.objects.bulk_create(instances)
    else:
        CSPSetting.objects.filter(value__in=[csp["value"] for csp in csps]).delete()
