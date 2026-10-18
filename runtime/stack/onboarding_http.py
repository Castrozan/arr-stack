import http.cookiejar
import json
import urllib.error
import urllib.request


class JsonClient:
    def __init__(self, base_url, headers=None):
        self.base_url = base_url
        self.headers = headers or {}
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )

    def request(self, method, path, payload=None):
        request = urllib.request.Request(
            self.base_url + path,
            method=method,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Content-Type": "application/json", **self.headers},
        )
        try:
            with self.opener.open(request, timeout=30) as response:
                body = response.read()
        except urllib.error.HTTPError as error:
            raise RuntimeError(
                f"{method} {self.base_url}{path} returned HTTP {error.code}"
            ) from error
        return json.loads(body) if body else None
