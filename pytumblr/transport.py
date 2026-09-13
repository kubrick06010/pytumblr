"""Shared transport behavior for modern Tumblr API calls."""

import json
import requests


class ModernTransportMixin(object):
    """Single-source JSON, NPF multipart and response handling for OAuth1/2."""

    def _auth_kwargs(self):
        oauth = getattr(self, "oauth", None)
        return {"auth": oauth} if oauth is not None else {}

    def _json_request(self, method, url, payload):
        kwargs = {
            "json": payload,
            "headers": self.headers,
            "allow_redirects": False,
            "timeout": self.timeout,
        }
        kwargs.update(self._auth_kwargs())
        response = getattr(requests, method)(self.host + url, **kwargs)
        return self.json_parse(response)

    def post_json(self, url, payload):
        return self._json_request("post", url, payload)

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

    def _multipart_npf(self, method, url, payload, media_sources):
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

            kwargs = {
                "files": files,
                "headers": self.headers,
                "allow_redirects": False,
                "timeout": self.timeout,
            }
            kwargs.update(self._auth_kwargs())
            response = getattr(requests, method)(self.host + url, **kwargs)
            return self.json_parse(response)
        finally:
            for file_object in opened:
                file_object.close()

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
