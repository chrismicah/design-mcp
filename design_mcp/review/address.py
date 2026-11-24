"""Rules for a pasted page address: public http(s) pages only, and never with sign-in details."""

import ipaddress
import socket
from urllib.parse import urlsplit

from .evidence import EvidenceError, inspect_url

_LOCAL_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home.arpa")
NOT_PUBLIC = (
    "That address is on this computer or a private network. Open the page yourself and click the "
    "Design MCP button on it: the toolbar button works on any page you can see."
)
_NOT_FOUND = "That address could not be found. Check the spelling and try again."


def local_address_reason(url):
    """Why an address is not a public page, judged from the address alone. None when it looks public."""
    return NOT_PUBLIC if is_private_host(urlsplit(url).hostname or "") else None


def canonical_host(host):
    return host.lower().rstrip(".")


def is_public_ip(address):
    if isinstance(address, ipaddress.IPv6Address):
        if address.scope_id is not None or address.sixtofour is not None:
            return False
        if address.ipv4_mapped:
            address = address.ipv4_mapped
    return address.is_global and not address.is_multicast and not address.is_reserved


def is_private_host(host):
    host = canonical_host(host)
    if host == "localhost" or host.endswith(_LOCAL_SUFFIXES) or ("." not in host and ":" not in host):
        return True
    try:
        return not is_public_ip(ipaddress.ip_address(host))
    except ValueError:
        return False


def credentials_reason(removed):
    """The sentence shown when a pasted address carries sign-in details. None when it carries none."""
    if not removed:
        return None
    return ("That address carries " + " and ".join(removed) +
            ". Paste the public address without it: scans never use sign-in details.")


def public_target(url, resolve=socket.getaddrinfo):
    """Return `(clean_url, host, address)` for a public page, or raise with a message for the person pasting.

    The address must be http(s), carry no credentials and resolve only to public addresses. The returned
    address is the one a separate browser is pinned to, so the name cannot be re-pointed after this check.
    """
    clean, removed = inspect_url(url)
    if removed:
        raise EvidenceError("credentials-in-url", credentials_reason(removed))
    parts = urlsplit(clean)
    port = parts.port or (443 if parts.scheme == "https" else 80)
    return clean, parts.hostname, resolve_public_host(parts.hostname, port, resolve)


def resolve_public_host(host, port, resolve=socket.getaddrinfo):
    """Resolve a connection target and return a checked numeric address."""
    if is_private_host(host):
        raise EvidenceError("private-address", NOT_PUBLIC)
    try:
        answers = resolve(host, port, type=socket.SOCK_STREAM)
    except OSError:
        raise EvidenceError("unresolved", _NOT_FOUND) from None
    addresses = []
    for answer in answers:
        try:
            address = ipaddress.ip_address(answer[4][0])
        except ValueError:
            raise EvidenceError("private-address", NOT_PUBLIC) from None
        if not is_public_ip(address):
            raise EvidenceError("private-address", NOT_PUBLIC)
        addresses.append(address)
    if not addresses:
        raise EvidenceError("unresolved", _NOT_FOUND)
    chosen = next((address for address in addresses if address.version == 4), addresses[0])
    return str(chosen)
