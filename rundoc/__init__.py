"""
Tool that let's you run code blocks from a markdown file in controlled manner.
"""

__version__ = "0.2.5"
__license__ = "BSD"
__year__ = "2017"
__author__ = "Predrag Mandic"
__author_email__ = "predrag@eclecticiq.com"


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

