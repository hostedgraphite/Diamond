# coding=utf-8
URLOPEN = "diamond.pycompat.urlopen"
try:
    from urllib2 import HTTPError, Request, urlopen, URLError
    from urllib import urlencode, quote
    from urlparse import urljoin, urlparse
    from Queue import Empty, Full, Queue
except ImportError:
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode, quote, urljoin, urlparse
    from urllib.error import HTTPError, URLError
    from queue import Full, Empty, Queue

try:
    long = long
    unicode = unicode
except NameError:
    long = int
    unicode = str
