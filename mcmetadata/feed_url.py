"""
Routines for (RSS) Feed URLs.
Created for the great Media Merge of 2022
"""

import urllib.parse

def normalize(url: str) -> str:
    """
    Put a feed URL into a "normal" form for *COMPARISON*
    Output is "lossy", NOT meant to be used.

    (flattens case, turn https into https, removes redundant ports, www prefix)
    """
    # lower casify and parse
    a = urllib.parse.urlparse(url.lower())

    # make https into http, remove redundant port info
    scheme = a.scheme
    netloc = a.netloc
    nls = netloc.split(':',1)   # netloc, split into host[:port]
    if scheme == 'https':
        scheme = 'http'
        if len(nls) > 1 and nls[1] == '443':
            netloc = nls[0]
    elif scheme == 'http':
        if len(nls) > 1 and nls[1] == '80':
            netloc = nls[0]

    # remove www prefix
    if netloc.startswith('www.'):
        netloc = netloc[4:]

    # remove trailing slash from path
    path = a.path
    if path.endswith('/'):
        path = path[:-1]

    # put it back together
    u = f"{scheme}://{netloc}{path}"

    # reassemble query in sorted order:
    q = '&'.join(sorted(a.query.split('&')))
    if q:
        u = f"{u}?{q}"
    if a.fragment:
        u = f"{u}#{a.fragment}"
    return u

if __name__ == '__main__':
    print(normalize('https://Aaa.Bbb/ccc?a=1&c=3&b=2#z'))
    print(normalize('http://aaA.bbB:80/ccc?c=3&b=2&a=1#Z'))
    print(normalize('https://aaA.bbB:443/ccc?c=3&b=2&a=1#Z'))
    print(normalize('http://aaA.bbB:123/ccc?c=3&b=2&a=1#Z'))
    print(normalize('http://peoplesdailyng.com/feed/'))
    print(normalize('https://www.peoplesdailyng.com/feed'))
