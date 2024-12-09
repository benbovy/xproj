from importlib.metadata import PackageNotFoundError, version

from .accessor import ProjAccessor as _ProjAccessor  # noqa: F401
from .index import CRSIndex  # noqa: F401

__all__ = ["_ProjAccessor", "CRSIndex"]

try:
    __version__ = version("xproj")
except PackageNotFoundError:  # noqa
    # package is not installed
    pass
