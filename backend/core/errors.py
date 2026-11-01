"""Domain errors raised by the core pipeline.

The API layer maps these exceptions to HTTP status codes, so the core never
depends on FastAPI.
"""


class CoreError(Exception):
    """Base class for every recoverable pipeline error."""


class InvalidImageError(CoreError):
    """The uploaded bytes cannot be decoded as an image."""


class InvalidOptionError(CoreError):
    """A pipeline option is out of range or unknown."""


class SegmentationError(CoreError):
    """The person segmentation model failed or returned an unusable mask."""
