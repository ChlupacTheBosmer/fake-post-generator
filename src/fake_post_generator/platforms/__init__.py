# Importing each platform package triggers its @register decorator,
# adding it to the global platform registry.
from . import reddit, twitter  # noqa: F401
