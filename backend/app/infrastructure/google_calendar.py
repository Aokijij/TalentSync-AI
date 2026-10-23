"""Fixed-endpoint delegated Google Calendar, own primary events only."""
import json
from urllib.parse import urlencode, urlsplit

import httpx

from app.application.calendar_errors import CalendarProviderError

SCOPE = "https://www.googleapis.com/auth/calendar.events.owned"
TOKEN = "https://oauth2.googleapis.com/token"
EVENTS = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


class GoogleCalendar:
    def __init__(self, settings, transport=None):
        self.settings, self.transport = settings, transport

    @property
    def configured(self):
        origin = urlsplit(self.settings.public_app_url)
        safe = origin.scheme == "https" or self.settings.environment == "development" and origin.scheme == "http" and origin.hostname in {"127.0.0.1", "localhost"}
        return bool(self.settings.calendar_sync_enabled and self.settings.session_auth_enabled and self.settings.calendar_google_client_id and self.settings.calendar_google_client_secret and safe and not origin.username and not origin.password and not origin.query and not origin.fragment and origin.path in {"", "/"})

    @property
    def callback_url(self):
        return self.settings.public_app_url.rstrip("/") + "/api/v1/account/calendar/google/callback"

    def authorization_url(self, state, challenge):
        if not self.configured:
            raise CalendarProviderError("configuration")
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({"client_id": self.settings.calendar_google_client_id, "redirect_uri": self.callback_url,
            "response_type": "code", "scope": SCOPE, "access_type": "offline", "prompt": "consent", "state": state, "code_challenge": challenge, "code_challenge_method": "S256"})

    @staticmethod
    def _read(response):
        body = bytearray()
        for chunk in response.iter_bytes():
            body.extend(chunk)
            if len(body) > 65536:
                raise CalendarProviderError()
        try:
            value = json.loads(body)
            if not isinstance(value, dict):
                raise ValueError()
            return value
        except ValueError:
            raise CalendarProviderError() from None

    def _token(self, values):
        if not self.configured:
            raise CalendarProviderError("configuration")
        try:
            with httpx.Client(transport=self.transport, timeout=15, follow_redirects=False, trust_env=False) as client:
                with client.stream("POST", TOKEN, data={**values, "client_id": self.settings.calendar_google_client_id, "client_secret": self.settings.calendar_google_client_secret}) as response:
                    if response.status_code != 200:
                        raise CalendarProviderError("authorization" if response.status_code in {400, 401, 403} else "temporary")
                    result = self._read(response)
        except httpx.HTTPError:
            raise CalendarProviderError() from None
        if not isinstance(result.get("access_token"), str) or not 10 <= len(result["access_token"]) <= 8192:
            raise CalendarProviderError()
        return result

    def exchange(self, code, verifier):
        value = self._token({"grant_type": "authorization_code", "code": code, "code_verifier": verifier, "redirect_uri": self.callback_url})
        if SCOPE not in value.get("scope", "").split() or not isinstance(value.get("refresh_token"), str) or not 10 <= len(value["refresh_token"]) <= 8192:
            raise CalendarProviderError("authorization")
        return value["refresh_token"]

    def refresh(self, refresh_token):
        value = self._token({"grant_type": "refresh_token", "refresh_token": refresh_token})
        rotated = value.get("refresh_token")
        return value["access_token"], rotated if isinstance(rotated, str) and 10 <= len(rotated) <= 8192 else None

    def sync(self, access_token, remote_id, event, create):
        if len(remote_id) > 64 or not remote_id or any(c not in "0123456789abcdefghijklmnopqrstuv" for c in remote_id):
            raise CalendarProviderError("configuration")
        method, url = ("DELETE", f"{EVENTS}/{remote_id}") if event is None else ("POST", EVENTS) if create else ("PATCH", f"{EVENTS}/{remote_id}")
        try:
            with httpx.Client(transport=self.transport, timeout=15, follow_redirects=False, trust_env=False) as client:
                with client.stream(method, url, headers={"Authorization": f"Bearer {access_token}"}, params={"sendUpdates": "none"}, json={**event, **({"id": remote_id} if create else {})} if event else None) as response:
                    status = response.status_code
                if create and status == 409:
                    with client.stream("PATCH", f"{EVENTS}/{remote_id}", headers={"Authorization": f"Bearer {access_token}"}, params={"sendUpdates": "none"}, json=event) as response:
                        status = response.status_code
                if status in {200, 201, 204} or event is None and status in {404, 410}:
                    return
                if event is not None and status in {404, 410}:
                    raise CalendarProviderError("missing")
                raise CalendarProviderError("authorization" if status in {401, 403} else "temporary")
        except httpx.HTTPError:
            raise CalendarProviderError() from None
