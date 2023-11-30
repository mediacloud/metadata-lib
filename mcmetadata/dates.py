import datetime as dt
from typing import Optional
import logging

import dateparser
import htmldate

logger = logging.getLogger(__name__)


def guess_publication_date(html: str, url: str, max_date: Optional[dt.datetime] = None,
                           default_date: Optional[dt.datetime] = None) -> Optional[dt.datetime]:
    pub_date = None
    try:
        pub_date_str = htmldate.find_date(html, url=url, original_date=True, extensive_search=False,
                                          max_date=max_date)
        if pub_date_str:
            pub_date = dateparser.parse(pub_date_str)
            if max_date and (pub_date > max_date):  # double check for safety
                logger.warning("Ignore date as after max - {} > {}".format(pub_date, max_date))
                pub_date = None
    except:
        # if there is no date found, or it is in a format that can't be parsed, ignore and just keep going
        logger.error('Publication date parsing failed', exc_info=1)
    if (pub_date is None) and (default_date is not None):
        pub_date = default_date
    return pub_date
