import logging
from abc import ABC, abstractmethod
import newspaper
from goose3 import Goose
from typing import Dict
from bs4 import BeautifulSoup
from boilerpy3 import extractors as bp3_extractors
import readability
import trafilatura
import collections

from .exceptions import UnableToExtractError
from .html import strip_tags

logger = logging.getLogger(__name__)

MINIMUM_CONTENT_LENGTH = 200  # less than this and it doesn't count as working extraction (experimentally determined)


METHOD_NEWSPAPER_3k = 'newspaper3k'
METHOD_GOOSE_3 = 'goose3'
METHOD_BEAUTIFUL_SOUP_4 = 'beautifulsoup4'
METHOD_BOILER_PIPE_3 = 'boilerpipe3'
METHOD_DRAGNET = 'dragnet'
METHOD_READABILITY = 'readability'
METHOD_TRIFILATURA = 'trifilatura'
METHOD_FAILED = 'failed'  # placeholder for stats

# track stats on how frequently each method succeeds (keyed by the METHOD_XYZ constants)
method_success_stats = collections.Counter()


def from_html(url: str, html_text: str) -> Dict:
    """
    Try a series of extractors to pull content out of HTML. The idea is to try as hard as can to get
    good content, but fallback to at least get something useful. The writeup at this site was very helpful:
    https://adrien.barbaresi.eu/blog/evaluating-text-extraction-python.html
    :param html_text: the raw HTML to parser
    :param url: this is useful to pass in for some metadata parsing
    :return: a dict of with url, text, title, publish_date, top_image_url, authors, and extraction_method keys
    """
    # now try each extractor against the same HTML
    order = [  # based by findings from trifilatura paper, but customized to performance on EN and ES sources (see test)
        ReadabilityExtractor,
        TrafilaturaExtractor,
        BoilerPipe3Extractor,
        GooseExtractor,
        Newspaper3kExtractor,
        RawHtmlExtractor  # this one should never fail (if there is any content at all) because it just parses HTML
    ]
    for extractor_class in order:
        try:
            extractor = extractor_class()
            extractor.extract(url, html_text)
            if extractor.worked():
                method_success_stats[extractor.content['extraction_method']] += 1
                return extractor.content
        except Exception as e:
            # if the extractor fails for any reason, just continue on to the next one
            pass
    method_success_stats[METHOD_FAILED] += 1  # track how many failures we've had too
    raise UnableToExtractError(url)


class AbstractExtractor(ABC):

    def __init__(self):
        self.content = None

    @abstractmethod
    def extract(self, url: str, html_text: str):
        pass

    def worked(self) -> bool:
        # if there was some reasonable amount of none-tag content then we'll assume things worked
        if self.content is None:
            return False
        text_no_tags = strip_tags(self.content['text'])
        return len(text_no_tags) > MINIMUM_CONTENT_LENGTH


class Newspaper3kExtractor(AbstractExtractor):

    def extract(self, url, html_text: str):
        doc = newspaper.Article(url)
        doc.download(input_html=html_text)
        doc.parse()
        self.content = {
            'url': url,
            'text': doc.text,
            'title': doc.title,
            'potential_publish_date': doc.publish_date,
            'top_image_url': doc.top_image,
            'authors': doc.authors,
            'extraction_method': METHOD_NEWSPAPER_3k,
        }


class GooseExtractor(AbstractExtractor):

    def extract(self, url, html_text: str):
        g = Goose()
        g3_article = g.extract(raw_html=html_text)
        self.content = {
            'url': url,
            'text': g3_article.cleaned_text,
            'title': g3_article.title,
            'potential_publish_date': g3_article.publish_date,
            'top_image_url': g3_article.top_image.src if g3_article.top_image else None,
            'authors': g3_article.authors,
            'extraction_method': METHOD_GOOSE_3,
        }


class BoilerPipe3Extractor(AbstractExtractor):

    def extract(self, url: str, html_text: str):
        extractor = bp3_extractors.ArticleExtractor()
        bp_doc = extractor.get_doc(html_text)
        self.content = {
            'url': url,
            'text': bp_doc.content,
            'title': bp_doc.title,
            'potential_publish_date': None,
            'top_image_url': None,
            'authors': None,
            'extraction_method': METHOD_BOILER_PIPE_3,
        }


class TrafilaturaExtractor(AbstractExtractor):

    def extract(self, url: str, html_text: str):
        # don't fallback to readability/justext because we have our own hierarchy of things to try
        text = trafilatura.extract(html_text, no_fallback=True)
        self.content = {
            'url': url,
            'text': text,
            'title': None,
            'potential_publish_date': None,
            'top_image_url': None,
            'authors': None,
            'extraction_method': METHOD_TRIFILATURA,
        }


class ReadabilityExtractor(AbstractExtractor):

    def extract(self, url: str, html_text: str):
        doc = readability.Document(html_text)
        self.content = {
            'url': url,
            'text': strip_tags(doc.summary()),  # remove any tags that readability leaves in place (links)
            'title': doc.title(),
            'potential_publish_date': None,
            'top_image_url': None,
            'authors': None,
            'extraction_method': METHOD_READABILITY,
        }


class RawHtmlExtractor(AbstractExtractor):

    REMOVE_LIST = {'[document]', 'noscript', 'header', 'html', 'meta', 'head', 'input', 'script', 'style'}

    def __init__(self):
        super(RawHtmlExtractor, self).__init__()

    def extract(self, url: str, html_text: str):
        soup = BeautifulSoup(html_text, 'lxml')
        text = soup.find_all(string=True)
        output = ''
        for t in text:
            if t.parent.name not in self.REMOVE_LIST:
                output += '{} '.format(t)
        self.content = {
            'url': url,
            'text': output,
            'title': None,
            'potential_publish_date': None,
            'top_image_url': None,
            'authors': None,
            'extraction_method': METHOD_BEAUTIFUL_SOUP_4,
        }
