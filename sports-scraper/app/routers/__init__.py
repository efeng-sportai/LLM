"""
FastAPI Routers
"""

from . import health
from . import api
from . import training_data
from . import populate

__all__ = [
    "health",
    "api", 
    "training_data",
    "populate"
]