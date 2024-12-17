from importlib.metadata import PackageNotFoundError, version

from .accessor import ProjAccessor as _ProjAccessor  # noqa: F401
from .accessor import register_accessor
from .index import CRSIndex  # noqa: F401
from .mixins import ProjAccessorMixin, ProjIndexMixin

__all__ = ["_ProjAccessor", "CRSIndex", "ProjAccessorMixin", "ProjIndexMixin", "register_accessor"]

try:
    __version__ = version("xproj")
except PackageNotFoundError:  # noqa
    # package is not installed
    pass
