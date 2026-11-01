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


# Single user-facing wording for "nothing to convert", shared by CLI and API.
BLANK_IMAGE_MESSAGE = "Error, blank image"


class EmptySubjectError(CoreError):
    """The image produced no subject pixels, so the result would be empty."""

    def __init__(self, message: str = BLANK_IMAGE_MESSAGE) -> None:
        super().__init__(message)
