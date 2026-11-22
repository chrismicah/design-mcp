"""The optional legacy pattern corpus. Only verified snapshots reach the cache."""

import hashlib
import io
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import BadZipFile

from platformdirs import user_cache_path

from .resources import ResourceError, data_file


# Git blob 79d9995bc1322213b16b212aea01057980ea1aaa at this public commit.
URL = (
    "https://raw.githubusercontent.com/chrismicah/design-mcp/"
    "82fe6e3749acccf80aecfd523e531be4302865e3/design_mcp/data/patterns.json"
)
SHA256 = "dd51bf8db34f9295253b846ee8719cfd9b76b775ff029f591e49d9e7d16806a5"
SIZE = 10_092_399
REPAIR = "Run design-mcp doctor --repair to rebuild the legacy cache."


class CorpusError(ResourceError):
    """The legacy tools cannot use the requested corpus."""


class IntegrityError(CorpusError):
    """A present corpus differs from the pinned bytes."""


def cache_path() -> Path:
    return user_cache_path("design-mcp", appauthor=False) / f"patterns-{SHA256}.json"


def _verify(data: bytes, origin: str) -> bytes:
    if len(data) != SIZE:
        raise IntegrityError(f"{origin} has the wrong size (expected {SIZE} bytes).")
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise IntegrityError(f"{origin} failed its SHA-256 check.")
    return data


def _read(entry, advice: str) -> bytes | None:
    try:
        with entry.open("rb") as stream:
            return _verify(stream.read(SIZE + 1), str(entry))
    except FileNotFoundError:
        return None
    except IntegrityError as error:
        raise IntegrityError(f"{error} {advice}") from error
    except (OSError, BadZipFile) as error:
        raise CorpusError(f"Cannot read {entry}. {error}") from error


def read_bundled() -> bytes | None:
    return _read(data_file("patterns.json"), "Restore the bundled file from the original checkout or install.")


def read_cached() -> bytes | None:
    path = cache_path()
    if path.parent.is_symlink() or path.is_symlink():
        raise CorpusError(f"The design-mcp cache points to a symlink at {path.parent} or {path.name}.")
    if path.exists() and not path.is_file():
        raise CorpusError(f"Expected a regular cache file at {path}.")
    return _read(path, REPAIR)


def _download() -> bytes:
    import httpx

    try:
        with httpx.stream("GET", URL, headers={"Accept-Encoding": "identity"},
                          timeout=15, follow_redirects=False, trust_env=False) as response:
            response.raise_for_status()
            length = response.headers.get("Content-Length")
            if length is not None and length != str(SIZE):
                raise IntegrityError(f"Unexpected corpus Content-Length {length!r} (expected {SIZE}).")
            body = io.BytesIO()
            for chunk in response.iter_raw(chunk_size=64 * 1024):
                if body.tell() + len(chunk) > SIZE:
                    raise IntegrityError(f"The legacy download exceeds {SIZE} bytes.")
                body.write(chunk)
            return _verify(body.getvalue(), URL)
    except (httpx.HTTPError, OSError, IntegrityError) as error:
        raise CorpusError(f"Cannot fetch the verified legacy corpus from {URL}. {error} {REPAIR}") from error


def ensure_cache(*, repair: bool = False) -> bytes:
    """Publish one complete file. Concurrent writers can only publish identical bytes."""
    try:
        cached = read_cached()
    except IntegrityError:
        if not repair:
            raise
    else:
        if cached is not None:
            return cached

    data = read_bundled()
    if data is None:
        data = _download()
    path = cache_path()
    temporary = None
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=path.parent, prefix=".patterns-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError as error:
        raise CorpusError(f"Cannot publish the legacy cache at {path}. {error}") from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return data


def read_corpus() -> bytes:
    bundled = read_bundled()
    return bundled if bundled is not None else ensure_cache()
