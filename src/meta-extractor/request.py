import time
from functools import wraps
from requests.exceptions import SSLError, ReadTimeout, TooManyRedirects, ConnectionError, RequestException
import logging

import helpers
from helpers.exceptions import UnableToExtractError

logger = logging.getLogger(__name__)

STATUS_OK = 'ok'
STATUS_ERROR = 'error'


def _duration(start_time: float):
    return int(round((time.time() - start_time) * 1000)) if start_time else 0


def _error_results(message: str, start_time: float, status_code: int = 400):
    """
    Central handler for returning error messages.
    :param message:
    :param start_time:
    :param status_code:
    :return:
    """
    return {
        'status': STATUS_ERROR,
        'statusCode': status_code,
        'duration': _duration(start_time),
        'message': message,
        'modelMode': helpers.MODEL_MODE
    }


def api_method(func):
    """
    Helper to add metadata to every api method. Use this in server.py and it will add stuff like the
    version to the response. Plug it handles errors in one place, and supresses ones we don't care to log to Sentry.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            results = func(*args, **kwargs)
            return {
                'version': helpers.VERSION,
                'status': STATUS_OK,
                'duration': _duration(start_time),
                'results': results,
                'modelMode': helpers.MODEL_MODE
            }
        # don't log certain exceptions, because they are expected and are too noisy on Sentry
        except SSLError as se:
            # this is a subclass of ConnectionError, but good to catch it so we have a more detailed error message
            return _error_results(str(se), start_time)
        except TooManyRedirects as tmr:
            return _error_results(str(tmr), start_time)
        except ReadTimeout as rt:
            return _error_results(str(rt), start_time)
        except UnableToExtractError as utee:
            return _error_results(str(utee), start_time)
        except ConnectionError as ce:
            return _error_results(str(ce), start_time)
        except RequestException as rexc:
            return _error_results(str(rexc), start_time)
        except ValueError as ve:
            return _error_results(str(ve), start_time)
        except Exception as e:
            # log other, unexpected, exceptions to Sentry
            logger.exception(e)
            return _error_results(str(e), start_time)
    return wrapper
