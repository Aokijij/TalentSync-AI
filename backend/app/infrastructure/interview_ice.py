import base64
import hashlib
import hmac
import secrets
import time


class InterviewIce:
    def __init__(self, settings):
        self.settings = settings

    def configuration(self, room_id, user_id):
        servers = []
        if self.settings.webrtc_stun_urls:
            servers.append({"urls": self.settings.webrtc_stun_urls})
        expires = None
        if self.settings.webrtc_turn_urls:
            expires = int(time.time()) + 3600
            opaque = hashlib.sha256(f"{room_id}:{user_id}:{secrets.token_hex(8)}".encode()).hexdigest()[:24]
            username = f"{expires}:{opaque}"
            credential = base64.b64encode(hmac.new(self.settings.webrtc_turn_secret.encode(), username.encode(), hashlib.sha1).digest()).decode()
            servers.append({"urls": self.settings.webrtc_turn_urls, "username": username, "credential": credential})
        return {"ice_servers": servers, "ice_transport_policy": "relay" if self.settings.webrtc_relay_only else "all",
                "expires_at": expires, "mode": "turn_configured" if self.settings.webrtc_turn_urls else "stun_configured" if servers else "direct"}
