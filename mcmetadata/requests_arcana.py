"""
Incantations for reqeusts to allow fetching from as many sites as
Scrapy does.

This was originally in mediacloud/story-indexer, but copied to
metadata-lib to enable more mediacloud projects to consistently fetch
web pages.

WARNING: Do NOT use this if you care about data security/privacy.
This has been added to metadata-lib as a convenience to the Media
Cloud project, and it is NOT suitable for any/all uses!!

BE VERY CAREFUL making any changes, because it can/will effect what
sites will talk to you!

YOU HAVE BEEN WARNED!!!

Admissions:

In this library so Media Cloud didn't need to create another
library/module.

Was written/cribbed for the mediacloud specific use case,
and does not provide the fullest possible flexibiliy

In a file of it's own to hide the nastiness, fragility,
and the possibility that it's not suitable for general use!
"""

import logging
import ssl

import requests
import urllib3
from requests.structures import CaseInsensitiveDict

logger = logging.getLogger(__name__)


# https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled
class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    """
    Transport adapter for urllib3 that allows us to use custom ssl_context.
    """

    def __init__(self, ssl_context: ssl.SSLContext):
        self._ssl_context = ssl_context

        # NOTE! feed_seeker creates CustomHttpAdapters with alternate
        # retry settings (halves retry attempts, and enables backoff).
        # This may need (re)visiting to harmonize behavior across
        # all of Media Cloud fetching!
        super().__init__()  # calls init_poolmanager

    def init_poolmanager(
        self,
        connections,
        maxsize,
        block=requests.adapters.DEFAULT_POOLBLOCK,
        **pool_kwargs,
    ) -> None:
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self._ssl_context,
        )


def insecure_requests_session(user_agent: str) -> requests.Session:
    """
    Return a requests.Session object that behaves like OpenSSL 1.1.1
    while using OpenSSL 3.0, in order to match Scrapy behavior (and
    most browsers?) in order to fetch pages from "unpatched" sites.

    Like it says in the name:
    DON'T USE THIS IF YOU WANT TO KEEP DATA PRIVATE!!
    """

    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

    # https://docs.openssl.org/3.0/man3/SSL_CTX_set_options/#patched-openssl-client-and-unpatched-server
    # says:
    #
    #   If the option SSL_OP_LEGACY_SERVER_CONNECT or
    #   SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION is set then initial
    #   connections and renegotiation between patched OpenSSL clients
    #   and unpatched servers succeeds. If neither option is set then
    #   initial connections to unpatched servers will fail.
    #
    #   Setting the option SSL_OP_LEGACY_SERVER_CONNECT has security
    #   implications; clients that are willing to connect to servers
    #   that do not implement RFC 5746 secure renegotiation are
    #   subject to attacks such as CVE-2009-3555.
    #
    #   OpenSSL client applications wishing to ensure they can connect
    #   to unpatched servers should always set
    #   SSL_OP_LEGACY_SERVER_CONNECT
    #
    #   OpenSSL client applications that want to ensure they can not
    #   connect to unpatched servers (and thus avoid any security
    #   issues) should always clear SSL_OP_LEGACY_SERVER_CONNECT using
    #   SSL_CTX_clear_options() or SSL_clear_options().
    #
    #   The difference between the SSL_OP_LEGACY_SERVER_CONNECT and
    #   SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION options is that
    #   SSL_OP_LEGACY_SERVER_CONNECT enables initial connections and
    #   secure renegotiation between OpenSSL clients and unpatched
    #   servers only, while SSL_OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION
    #   allows initial connections and renegotiation between OpenSSL
    #   and unpatched clients or servers.
    ctx.options |= int(getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x4))

    # NOTE!  This does not seem to be working, *AND* verification can
    # be disabled with session.get(url, .... verify=False), but *NOT* removing
    # it out of caution that it could effect fetch results!!!
    # https://stackoverflow.com/questions/33770129/how-do-i-disable-the-ssl-check-in-python-3-x
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    session = requests.session()
    session.mount("https://", CustomHttpAdapter(ctx))
    session.mount("http://", CustomHttpAdapter(ctx))  # for retries

    # Overwriting entire headers dict to get as close as possible to
    # Scrapy (only Host is out of place).  Both "Connection: close" and
    # "Connection: keep-alive" cause NPR Akamai https connections to hang!!
    # (http connections seem to hang regardless)
    session.headers = CaseInsensitiveDict(
        {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "en",
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
        }
    )

    return session


# https://secariolabs.com/logging-raw-http-requests-in-python/
def log_http_requests() -> None:
    """
    For debugging:

    call this function once to patch code paths so that HTTP
    requests are logged for test/debug.
    """
    import http

    old_send = http.client.HTTPConnection.send

    def new_send(self, data):  # type: ignore[no-untyped-def]
        logger.debug("HTTP %s", data.decode("utf-8").strip())
        return old_send(self, data)

    http.client.HTTPConnection.send = new_send  # type: ignore[method-assign]


if __name__ == "__main__":
    # run in mcmetadata (no venv required)
    from webpages import MEDIA_CLOUD_USER_AGENT

    # NOTE! this is not a test case, as it depends on a "known bad"
    # site that's out of our control, and could be fixed, or disappear
    # at any time!

    url = "https://baoapbac.vn/xa-hoi/index.rss"
    try:
        s1 = requests.Session()
        resp = s1.get(url, allow_redirects=True)
        assert False
    except requests.exceptions.SSLError as e:
        print("expected:", e)

    s = insecure_requests_session(MEDIA_CLOUD_USER_AGENT)
    resp = s.get(url, allow_redirects=True)
    assert resp
