"""Real TLS handshakes against a disposable loopback-only SMTP sink."""
import ipaddress
import socketserver
import ssl
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from app.application.ports.services import MailDeliveryError
from app.infrastructure.security.smtp import SmtpDelivery


@contextmanager
def smtp_sink(tmp_path, mode, *, matching_hostname=True):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Local SMTP test")])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(days=1))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(
                "127.0.0.1" if matching_hostname else "127.0.0.2"))]), critical=False)
            .sign(key, hashes.SHA256()))
    certificate, private = tmp_path / "certificate.pem", tmp_path / "key.pem"
    certificate.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    private.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                        serialization.NoEncryption()))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certificate, private)
    captured = {"authenticated": False, "messages": [], "encrypted": False}

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            connection = self.request
            connection.settimeout(5)
            reader = None
            try:
                if mode == "ssl":
                    connection = context.wrap_socket(connection, server_side=True)
                    captured["encrypted"] = True
                reader = connection.makefile("rb")
                connection.sendall(b"220 local test SMTP\r\n")
                while line := reader.readline(8192):
                    command = line.split(b" ", 1)[0].strip().upper()
                    if command == b"EHLO":
                        connection.sendall(b"250-local\r\n250-STARTTLS\r\n250 AUTH PLAIN\r\n")
                    elif command == b"STARTTLS":
                        connection.sendall(b"220 start TLS\r\n")
                        reader.close()
                        connection = context.wrap_socket(connection, server_side=True)
                        captured["encrypted"] = True
                        reader = connection.makefile("rb")
                    elif command == b"AUTH" and captured["encrypted"]:
                        captured["authenticated"] = True
                        connection.sendall(b"235 authenticated\r\n")
                    elif command in {b"MAIL", b"RCPT"}:
                        connection.sendall(b"250 OK\r\n")
                    elif command == b"DATA" and captured["authenticated"]:
                        connection.sendall(b"354 data\r\n")
                        lines = []
                        while (data := reader.readline(8192)) not in {b".\r\n", b""}:
                            lines.append(data)
                        captured["messages"].append(b"".join(lines))
                        connection.sendall(b"250 accepted\r\n")
                    elif command == b"QUIT":
                        connection.sendall(b"221 bye\r\n")
                        break
                    else:
                        connection.sendall(b"530 rejected\r\n")
            except (OSError, ssl.SSLError):
                # An untrusted certificate must terminate before AUTH or DATA.
                pass
            finally:
                if reader:
                    reader.close()
                connection.close()

    class Server(socketserver.ThreadingTCPServer):
        daemon_threads = True

    with Server(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .05}, daemon=True)
        thread.start()
        config = SimpleNamespace(smtp_enabled=True, smtp_host="127.0.0.1", smtp_port=server.server_address[1],
                                 smtp_security=mode, smtp_username="synthetic", smtp_password="test-only-password",
                                 smtp_from="sender@example.com", secret_key="test-only-key")
        try:
            yield config, captured, certificate
        finally:
            server.shutdown()
            thread.join(timeout=5)


@pytest.mark.parametrize("mode", ["ssl", "starttls"])
@pytest.mark.parametrize("failure", [None, "untrusted", "hostname"])
def test_delivery_validates_real_tls_before_authentication(tmp_path, monkeypatch, mode, failure):
    default_context = ssl.create_default_context
    with smtp_sink(tmp_path, mode, matching_hostname=failure != "hostname") as (config, captured, certificate):
        if failure != "untrusted":
            monkeypatch.setattr(ssl, "create_default_context", lambda: default_context(cafile=str(certificate)))
        def send():
            SmtpDelivery(config).send(recipient="recipient@example.com", subject="Local test",
                                      body="Synthetic content", message_id=123)
        if failure:
            with pytest.raises(MailDeliveryError) as error:
                send()
            assert not error.value.retryable and error.value.kind == "configuration"
            assert not captured["authenticated"] and captured["messages"] == []
        else:
            send()
            assert captured["encrypted"] and captured["authenticated"]
            assert len(captured["messages"]) == 1
            assert b"Synthetic content" in captured["messages"][0]
            assert b"Message-ID: <talentsync-" in captured["messages"][0]
