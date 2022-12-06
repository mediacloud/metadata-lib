import logging
import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECS = 3  # wait only this many seconds for a server to respond with content

# pretend to be this kind of browser
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) Gecko/20100101 Firefox/78.0'


def fetch(url: str, user_agent: str = None, timeout: int = None, fix_encoding: bool = True) -> tuple:
    custom_user_agent = user_agent or DEFAULT_USER_AGENT
    custom_timeout = timeout or DEFAULT_TIMEOUT_SECS
    # grab HTML only once so each library doesn't have to do it
    response = requests.get(url, headers={'User-Agent': custom_user_agent}, timeout=custom_timeout)
    if response.status_code != 200:
        raise RuntimeError("Webpage didn't return content ({}) from {}".format(response.status_code, url))
    if ("content-type" in response.headers) and ("text/html" not in response.headers["content-type"]):
        raise RuntimeError("Webpage didn't return html content ({}) from {}".format(
            response.headers["content-type"], url))
    # fix for improperly marked encodings
    if fix_encoding:
        if response.encoding and (response.encoding.lower() != "utf-8") and\
                (response.encoding != response.apparent_encoding):
            response.encoding = response.apparent_encoding
    html_text = response.text
    return html_text, response
