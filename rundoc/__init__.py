"""
A command-line utility that runs code blocks from markdown files.
"""

__version__ = "0.2.6"
__license__ = "BSD"
__year__ = "2017-2018"
__author__ = "Predrag Mandic"
__author_email__ = "predrag@eclecticiq.com"
__copyright__ = "Copyright {} {} <{}>".format(
    __year__, __author__, __author_email__)


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

