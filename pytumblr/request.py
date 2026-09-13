from future import standard_library
standard_library.install_aliases()
from builtins import object
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
        """Issue a JSON POST request, used by modern NPF endpoints."""
        resp = requests.post(
            self.host + url, json=payload, headers=self.headers, auth=self.oauth,
            allow_redirects=False, timeout=self.timeout
        )
        return self.json_parse(resp)

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
        """Issue a JSON PUT request, used by modern NPF endpoints."""
        resp = requests.put(
            self.host + url, json=payload, headers=self.headers, auth=self.oauth,
            allow_redirects=False, timeout=self.timeout
        )
        return self.json_parse(resp)

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
        try:
            data = response.json()
        except ValueError:
            data = {'meta': {'status': 500, 'msg': 'Server Error'}, 'response': {"error": "Malformed JSON or HTML was returned."}}
        if 200 <= data['meta']['status'] <= 399:
            return data['response']
        return data

    def post_multipart(self, url, params, files):
        resp = requests.post(
            url, data=params, files=files, headers=self.headers,
            allow_redirects=False, auth=self.oauth, timeout=self.timeout
        )
        return self.json_parse(resp)
