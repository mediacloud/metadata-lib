import logging

import requests

from mcmetadata.exceptions import BadContentError

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECS = (
    3  # wait only this many seconds for a server to respond with content
)

# pretend to be this kind of browser
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; automated fetch; TBD domain)"

# central storage for use by Media Cloud projects, follows industry norms for bots
MEDIA_CLOUD_USER_AGENT = (
    "Mozilla/5.0 (compatible; mediacloud academic archive; mediacloud.org)"
)


def fetch(
    url: str, user_agent: str = None, timeout: int = None, fix_encoding: bool = True
) -> tuple:
    """
    Simple helper to fetch a webpage and return the HTML content and the response object.
    @param url: the URL to fetch
    @param user_agent: the user agent to use (defaults to generic DEFAULT_USER_AGENT)
    @param timeout: how long to wait before giving up (defaults to DEFAULT_TIMEOUT_SECS)
    @param fix_encoding: encodings are terribly inconsistent; we found it helps to fix obvious errors  (default True)
    @return: a tuple with the HTML text content and the `requests` response object
    """
    custom_user_agent = user_agent or DEFAULT_USER_AGENT
    custom_timeout = timeout or DEFAULT_TIMEOUT_SECS
    # remove leading or trailing whitespace (we've seen this on real URLs from feeds)
    url = url.strip()
    # grab HTML only once so each library doesn't have to do it
    response = requests.get(
        url, headers={"User-Agent": custom_user_agent}, timeout=custom_timeout
    )
    if response.status_code != 200:
        raise RuntimeError(
            "Webpage didn't return content ({}) from {}".format(
                response.status_code, url
            )
        )
    if ("content-type" in response.headers) and (
        "text/html" not in response.headers["content-type"]
    ):
        raise RuntimeError(
            "Webpage didn't return html content ({}) from {}".format(
                response.headers["content-type"], url
            )
        )
    # fix for improperly marked encodings
    if fix_encoding:
        if (
            response.encoding
            and (response.encoding.lower() != "utf-8")
            and (response.encoding != response.apparent_encoding)
        ):
            response.encoding = response.apparent_encoding
    html_text = response.text
    return html_text, response


def final_url(response: requests.Response) -> str:
    """
    The final URL might be the result of redirects, or an original URL if hosted at an archive
    """
    url = response.url  # followed all the redirects
    if "memento-datetime" in response.headers:  # we hit an archive like Wayback Machine
        try:
            url = response.links["original"][
                "url"
            ]  # the original url archived by the provider
        except KeyError:
            # maybe the responder doesn't provide the desired headers, so just fall back on the full URL because
            # there's nothing else we can really do
            raise BadContentError(
                "memento-datetime header without original url, skipping to avoid incorrect domain/url"
            )
    return url
