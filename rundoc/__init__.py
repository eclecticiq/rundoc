"""
A command-line utility that runs code blocks from markdown files.
"""
__version__ = "0.4.3"
__license__ = "BSD"
__year__ = "2017-2019"
__author__ = "Predrag Mandic, EclecticIQ"
__author_email__ = "rundoc@eclecticiq.com"
__copyright__ = "Copyright {} {} <{}>".format(
    __year__, __author__, __author_email__)

class ansi:
    ''' 
    ANSI colors for pretty output.
    '''
    red = '\033[91m'
    green = '\033[92m'
    blue = '\033[94m'
    yellow = '\033[93m'
    bold = '\033[1m'
    underline = '\033[4m'
    end = '\033[0m'

class RundocException(Exception):
    """Generic rundoc exception."""
    pass

class BadEnv(RundocException):
    """Attempt to load invalid environment name/value"""
    pass

class CodeFailed(RundocException):
    """Raise this when code block returns non-zero exit status."""
    pass

class BadInterpreter(RundocException):
    """Selected interpreter not found or is not executable by current user."""
    pass

