"""Read package data with either a filesystem or an archive-backed loader."""

import json
from importlib.resources import files
from zipfile import BadZipFile


class ResourceError(RuntimeError):
    """A required design-mcp resource could not be read."""


def data_file(name: str):
    entry = files("design_mcp") / "data"
    for part in name.split("/"):
        entry = entry / part
    return entry


def read_json(name: str):
    try:
        with data_file(name).open("r", encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, ValueError, BadZipFile) as error:
        raise ResourceError(f"Cannot read bundled data/{name}. Reinstall design-mcp. {error}") from error
