from future import standard_library
standard_library.install_aliases()
from builtins import object
import json
import urllib.parse
import requests
import sys

PY3 = sys.version_info[0] == 3

from requests_oauthlib import OAuth1
from requests.exceptions import TooManyRedirects


class TumblrRequest(object):
    """A simple request object that lets us query the Tumblr API."""

    __version = "0.1.3"

    def __init__(self, consumer_key, consumer_secret="", oauth_token="",
                 oauth_secret="", host="https://api.tumblr.com", timeout=30,
                 allow_custom_host=False):
        self.host = host
        self.timeout = timeout
        self.oauth = OAuth1(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=oauth_token,
            resource_owner_secret=oauth_secret
        )
        self.consumer_key = consumer_key
        self.headers = {"User-Agent": "pytumblr/" + self.__version}
        self.last_response_headers = None

    def get(self, url, params):
        url = self.host + url
        if params:
            url = url + "?" + urllib.parse.urlencode(params)
        try:
            resp = requests.get(
                url, allow_redirects=False, headers=self.headers,
                auth=self.oauth, timeout=self.timeout
            )
        except TooManyRedirects as e:
            resp = e.response
        return self.json_parse(resp)

    def post(self, url, params=None, files=None):
        url = self.host + url
        params = params or {}
        files = files or {}
        if files:
            return self.post_multipart(url, params, files)
        data = urllib.parse.urlencode(params)
        if not PY3:
            data = str(data)
        resp = requests.post(
            url, data=data, headers=self.headers, auth=self.oauth,
            allow_redirects=False, timeout=self.timeout
        )
        return self.json_parse(resp)

    def post_json(self, url, payload):
        return self._json_request("post", url, payload)

    def put(self, url, params=None, files=None):
        url = self.host + url
        params = params or {}
        files = files or {}
        if files:
            resp = requests.put(
                url, data=params, files=files, headers=self.headers,
                auth=self.oauth, allow_redirects=False, timeout=self.timeout
            )
        else:
            data = urllib.parse.urlencode(params)
            if not PY3:
                data = str(data)
            resp = requests.put(
                url, data=data, headers=self.headers, auth=self.oauth,
                allow_redirects=False, timeout=self.timeout
            )
        return self.json_parse(resp)

    def put_json(self, url, payload):
        return self._json_request("put", url, payload)

    def post_npf(self, url, payload, media_sources=None):
        if media_sources:
            return self._multipart_npf("post", url, payload, media_sources)
        return self.post_json(url, payload)

    def put_npf(self, url, payload, media_sources=None):
        if media_sources:
            return self._multipart_npf("put", url, payload, media_sources)
        return self.put_json(url, payload)

    def _json_request(self, method, url, payload):
        resp = getattr(requests, method)(
            self.host + url, json=payload, headers=self.headers,
            auth=self.oauth, allow_redirects=False, timeout=self.timeout
        )
        return self.json_parse(resp)

    def _multipart_npf(self, method, url, payload, media_sources):
        """Send Tumblr's multipart NPF shape: JSON part plus named media parts."""
        opened = []
        files = [("json", (None, json.dumps(payload), "application/json"))]
        try:
            for identifier, source in media_sources.items():
                if hasattr(source, "read"):
                    file_object = source
                    filename = getattr(source, "name", str(identifier))
                else:
                    file_object = open(source, "rb")
                    opened.append(file_object)
                    filename = str(source)
                files.append((str(identifier), (filename, file_object)))

            resp = getattr(requests, method)(
                self.host + url,
                files=files,
                headers=self.headers,
                allow_redirects=False,
                auth=self.oauth,
                timeout=self.timeout,
            )
            return self.json_parse(resp)
        finally:
            for file_object in opened:
                file_object.close()

    def delete(self, url, params):
        url = self.host + url
        if params:
            url = url + "?" + urllib.parse.urlencode(params)
        try:
            resp = requests.delete(
                url, allow_redirects=False, headers=self.headers,
                auth=self.oauth, timeout=self.timeout
            )
        except TooManyRedirects as e:
            resp = e.response
        return self.json_parse(resp)

    def json_parse(self, response):
        self.last_response_headers = getattr(response, "headers", None)
        try:
            data = response.json()
        except (ValueError, TypeError):
            return {
                "meta": {
                    "status": getattr(response, "status_code", 500),
                    "msg": getattr(response, "reason", "Server Error")
                },
                "response": {"error": "Malformed JSON or HTML was returned."},
            }

        # /tagged is documented/observed to sometimes return a top-level array.
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return data

        meta = data.get("meta")
        status = meta.get("status") if isinstance(meta, dict) else None
        if status is None:
            status = getattr(response, "status_code", 500)
        if 200 <= status <= 399:
            return data.get("response", data)
        return data

    def post_multipart(self, url, params, files):
        resp = requests.post(
            url, data=params, files=files, headers=self.headers,
            allow_redirects=False, auth=self.oauth, timeout=self.timeout
        )
        return self.json_parse(resp)
