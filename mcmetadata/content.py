import logging
from abc import ABC, abstractmethod
import re
import dateparser
import newspaper
from goose3 import Goose
from typing import Dict
from bs4 import BeautifulSoup
from boilerpy3 import extractors as bp3_extractors
import readability
import trafilatura
import collections
import lxml.etree
from lxml.html.clean import Cleaner
from lxml.html import fromstring, tostring

from .exceptions import UnableToExtractError, BadContentError
from .text import strip_tags

logger = logging.getLogger(__name__)

MINIMUM_CONTENT_LENGTH = 200  # less than this and it doesn't count as working extraction (experimentally determined)

# customize readability to remove all tags
everything_cleaner = Cleaner(scripts=True, javascript=True, comments=True, style=True, links=True, meta=True,
                             add_nofollow=False, page_structure=True, processing_instructions=True, embedded=True,
                             frames=True, forms=True, annoying_tags=True, remove_tags=[], remove_unknown_tags=True,
                             safe_attrs_only=False)
readability.readability.html_cleaner = everything_cleaner


METHOD_NEWSPAPER_3k = 'newspaper3k'
METHOD_GOOSE_3 = 'goose3'
METHOD_BEAUTIFUL_SOUP_4 = 'beautifulsoup4'
METHOD_BOILER_PIPE_3 = 'boilerpipe3'
METHOD_READABILITY = 'readability'
METHOD_TRAFILATURA = 'trafilatura'
METHOD_LXML = 'lxml'
METHOD_FAILED = 'failed'  # placeholder for stats
METHOD_OVERRIDEN = 'overriden'

# track stats on how frequently each method succeeds (keyed by the METHOD_XYZ constants)
method_success_stats = collections.Counter()


def from_html(url: str, html_text: str, include_metadata: bool = False) -> Dict:
    """
    Try a series of extractors to pull content out of HTML. The idea is to try as hard as can to get
    good content, but fallback to at least get something useful. The writeup at this site was very helpful:
    https://adrien.barbaresi.eu/blog/evaluating-text-extraction-python.html
    :param html_text: the raw HTML to parser
    :param url: this is useful to pass in for some metadata parsing
    :param include_metadata: true to try and extract any other metdata the underlying extractor supports, which can
                             create a notable performance hit
    :return: a dict of with url, text, title, publish_date, top_image_url, authors, and extraction_method keys
    """
    # now try each extractor against the same HTML
    for extractor_info in extractors:
        
        try:
            # logger.debug("Trying {}".format(extractor_info['method']))
            extractor = extractor_info['instance']
            extractor.extract(url, html_text, include_metadata)
            if extractor.worked():
                method_success_stats[extractor.content['extraction_method']] += 1
                extractor.content['text'] = extractor.content['text'].strip()
                return extractor.content
        except BadContentError as e:
            raise e
        except Exception as e:

            # if the extractor fails for any reason, just continue on to the next one
            pass
    method_success_stats[METHOD_FAILED] += 1  # track how many failures we've had too
    raise UnableToExtractError(url)


class AbstractExtractor(ABC):
    """
    Wrapper around individual libraries that can be useful to extract the news article "content" from an HTML page.
    Once you've called `extract()` then the `content` property will be filled in.
    """

    def __init__(self):
        self.content = None

    @abstractmethod
    def extract(self, url: str, html_text: str, include_metadata: bool = False):
        pass

    def worked(self) -> bool:
        # if there was some reasonable amount of none-tag content then we'll assume things worked
        if self.content is None:
            return False
        text_no_tags = self.content['text']
        if len(text_no_tags) > MINIMUM_CONTENT_LENGTH:
            return True
        else:
            raise BadContentError("Content is too short")


class Newspaper3kExtractor(AbstractExtractor):

    def extract(self, url, html_text: str, include_metadata: bool = False):
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

    def extract(self, url, html_text: str, include_metadata: bool = False):
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

    def extract(self, url: str, html_text: str, include_metadata: bool = False):
        try:
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
        except AttributeError:
            # getting some None errors on tag parsing, which suggests invalid HTML so let the next one try
            pass


# Trafilatura outputs images in teh raw text in Markdown format
markdown_img_path_pattern = re.compile(r"!\[[^\]]*\]\((.*?)\)")


class TrafilaturaExtractor(AbstractExtractor):

    def extract(self, url: str, html_text: str, include_metadata: bool = False):
        results = trafilatura.bare_extraction(html_text, only_with_metadata=include_metadata, url=url,
                                              include_images=include_metadata)
        image_urls = []
        if include_metadata:
            # pull out the images embedded in the markdown
            for match in markdown_img_path_pattern.finditer(results['text']):
                image_urls.append(match.group(1))
            # remove the image links from the full text
            text = markdown_img_path_pattern.sub("", results['text'])
        else:
            text = results['text']
        self.content = {
            'url': url,
            'text': text,
            'title': results['title'],
            'potential_publish_date': dateparser.parse(results['date']),
            'top_image_url': image_urls[0] if len(image_urls) > 0 else None,
            'authors': results['author'].split(',') if results['author'] else None,
            'extraction_method': METHOD_TRAFILATURA,
        }


class ReadabilityExtractor(AbstractExtractor):

    def extract(self, url: str, html_text: str, include_metadata: bool = False):
        try:
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
        except lxml.etree.ParserError:
            # getting "Document is empty" error, which means it didn't parse so let the next extractor try
            pass


class RawHtmlExtractor(AbstractExtractor):

    REMOVE_LIST = {'[document]', 'noscript', 'header', 'html', 'meta', 'head', 'input', 'script', 'style'}

    def __init__(self):
        super(RawHtmlExtractor, self).__init__()

    def extract(self, url: str, html_text: str, include_metadata: bool = False):
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


class LxmlExtractor(AbstractExtractor):
    """
    An inefficient fallback extractor that should work in all contexts
    """
    
    def extract(self, url: str, html_text: str, include_metadata: bool = False):
        cleaner = Cleaner(scripts=True, javascript=True, 
                comments=True, style=True, links=True, meta=True,
                add_nofollow=False, page_structure=True, 
                processing_instructions=True, embedded=True,
                frames=True, forms=True, annoying_tags=True, 
                allow_tags=[None],safe_attrs_only=False)


        parsed = lxml.etree.HTML(html_text)
        #This ensures that the etree is cast correctly-
        #It seems like pages with multiple head nodes sometimes confuse
        #the parser without this step
        circular = fromstring(tostring(parsed))
        content_string = tostring(cleaner.clean_html(circular))
        
        self.content = {
            "url": url,
            'text': content_string,
            'title': None,
            'potential_publish_date': None,
            'top_image_url': None,
            'authors': None,
            'extraction_method': METHOD_LXML,
        }
        
        


# based by findings from trafilatura paper, but customized to performance on EN and ES sources (see tests)
extractors = [
    dict(method=METHOD_TRAFILATURA, instance=TrafilaturaExtractor()),
    dict(method=METHOD_READABILITY, instance=ReadabilityExtractor()),
    dict(method=METHOD_BOILER_PIPE_3, instance=BoilerPipe3Extractor()),
    dict(method=METHOD_GOOSE_3, instance=GooseExtractor()),
    dict(method=METHOD_NEWSPAPER_3k, instance=Newspaper3kExtractor()),
    # this one should never fail (if there is any content at all) because it just parses HTML
    dict(method=METHOD_BEAUTIFUL_SOUP_4, instance=RawHtmlExtractor()),
    dict(method=METHOD_LXML, instance=LxmlExtractor())
]
