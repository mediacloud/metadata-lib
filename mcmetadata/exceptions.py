
class UnableToExtractError(RuntimeError):
    """
    Thrown when none of the content extractors worked on a given URL
    """

    def __init__(self, url, message="Tried all the extractors and none worked!"):
        self.url = url
        self.message = message
        super().__init__(self.message)


class UnknownLanguageException(Exception):
    """Raised when the input language is invalid"""
    pass

class BadContentError(RuntimeError):
    """
    Thrown when the content is not suitable for parsing, ie: too short 
    """
    pass