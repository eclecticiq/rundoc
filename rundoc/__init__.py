"""
Tool that let's you run code blocks from a markdown file in controlled manner.
"""

__version__ = "0.1.11"
__licence__ = "BSD"
__year__ = "2017"
__author__ = "EclecticIQ"
__author_email__ = "info@eclecticiq.com"


class RundocException(Exception):
    """Generic rundoc exception."""
    pass

class BadEnv(RundocException):
    """Attempt to load invalid environment name/value"""
    pass

