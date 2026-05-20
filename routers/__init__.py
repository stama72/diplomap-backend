"""
Package router initializer.

Import submodules in a dependency-aware order and expose them as package attributes
so that `from routers import maps, mappoints, ...` works reliably even with
interdependent modules.
"""

# Import order matters because modules reference each other at import time.
from . import maps as maps
from . import mappoints as mappoints
from . import countries as countries
from . import links as links

__all__ = [
	"maps",
	"mappoints",
	"countries",
	"links",
]
