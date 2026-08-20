"""Public API for dhidb."""

from importlib.metadata import PackageNotFoundError, version

from .config import DHIConfig
from .provider import DHIProvider

try:
    __version__ = version("dhidb")
except PackageNotFoundError:  # pragma: no cover - source tree without installation
    __version__ = "0.0.0+unknown"

__all__ = ["DHIConfig", "DHIProvider", "__version__"]

