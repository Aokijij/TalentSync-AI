"""Bounded HTTPS GETs, with public DNS addresses pinned to the TLS connection."""
import http.client
import ipaddress
import socket
import ssl
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit


class PublicHTTPError(ValueError):
    pass


def public_url(value):
    if not isinstance(value, str) or len(value) > 2000 or any(ord(c) < 33 or c == "\\" for c in value):
        raise PublicHTTPError("Invalid public URL")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in {None, 443}:
        raise PublicHTTPError("Only public HTTPS URLs are allowed")
    host = parsed.hostname.encode("idna").decode("ascii").lower()
    if "." not in host or host.endswith((".local", ".localhost", ".internal")):
        raise PublicHTTPError("Invalid public host")
    return urlunsplit(("https", host, parsed.path or "/", parsed.query, ""))


@dataclass(frozen=True)
class PublicResponse:
    status: int
    url: str
    body: bytes
    content_type: str


class PublicHTTP:
    def __init__(self, *, timeout=6, max_bytes=1_000_000):
        self.timeout, self.max_bytes = timeout, max_bytes

    def get(self, url):
        target = public_url(url)
        for _ in range(4):
            parsed = urlsplit(target)
            connection = None
            try:
                addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
                # Reject the entire DNS answer if it mixes public and private addresses.
                if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
                    raise PublicHTTPError("Non-public address")
                ip = addresses[0][4][0]
                connection = http.client.HTTPSConnection(parsed.hostname, timeout=self.timeout)
                context = ssl.create_default_context()
                sock = socket.create_connection((ip, 443), timeout=self.timeout)
                try:
                    connection.sock = context.wrap_socket(sock, server_hostname=parsed.hostname)
                except Exception:
                    sock.close()
                    raise
                # Host name is retained for SNI, certificate and Host; only the socket is pinned.
                connection.request("GET", urlunsplit(("", "", parsed.path or "/", parsed.query, "")), headers={
                    "User-Agent": "TalentSyncCatalog/1.0 (+https://talentsync-ai.pages.dev)",
                    "Accept": "application/json, text/html, text/plain;q=0.8", "Accept-Encoding": "identity",
                })
                response = connection.getresponse()
                if response.status in {301, 302, 303, 307, 308}:
                    location = response.getheader("Location")
                    if not location:
                        raise PublicHTTPError("Missing redirect")
                    target = public_url(urljoin(target, location))
                    continue
                if response.getheader("Content-Encoding", "identity").lower() not in {"identity", ""}:
                    raise PublicHTTPError("Unsupported encoding")
                body = response.read(self.max_bytes + 1)
                if len(body) > self.max_bytes:
                    raise PublicHTTPError("Response too large")
                return PublicResponse(response.status, target, body, response.getheader("Content-Type", "").lower())
            except (OSError, http.client.HTTPException, ValueError) as error:
                raise PublicHTTPError("Public source unavailable") from error
            finally:
                if connection:
                    connection.close()
        raise PublicHTTPError("Too many redirects")
