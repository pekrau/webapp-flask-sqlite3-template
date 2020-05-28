"Base class for tests."

import argparse
import http.client
import json
import os
import re
import sys
import unittest

import jsonschema
import requests

SCHEMA_LINK_RX = re.compile(r'<([^>])+>; rel="([^"]+)')

JSON_MIMETYPE = 'application/json'

DEFAULT_SETTINGS = {
    'ROOT_URL': 'http://127.0.0.1:5002/api',
    'USERNAME': None,           # Needs to be set! Must have admin privileges.
    'APIKEY': None              # Needs to be set! For the above user.
}

# The actual settings to use.
SETTINGS = {}

def process_args(filepath=None):
    """Process command-line arguments for this test suite.
    Reset the settings and read the given settings file.
    Return the unused arguments.
    """
    if filepath is None:
        parser = argparse.ArgumentParser()
        parser.add_argument('-S', '--settings', dest='settings',
                            metavar='FILE', default='settings.json',
                            help='Settings file')
        parser.add_argument('unittest_args', nargs='*')
        options, args = parser.parse_known_args()
        filepath = options.settings
        args = [sys.argv[0]] + args
    else:
        args = sys.argv
    SETTINGS.update(DEFAULT_SETTINGS)
    with open(filepath) as infile:
        SETTINGS.update(json.load(infile))
    assert SETTINGS['USERNAME']
    assert SETTINGS['APIKEY']
    return args

def run():
    unittest.main(argv=process_args())


class Base(unittest.TestCase):
    "Base class for Symbasis test cases."

    def setUp(self):
        self.schemas = {}
        self.session = requests.Session()
        self.session.headers.update({'x-apikey': SETTINGS['APIKEY']})
        self.addCleanup(self.close_session)

    def close_session(self):
        self.session.close()

    @property
    def root(self):
        "Return the API root data."
        try:
            return self._root
        except AttributeError:
            response = self.GET(SETTINGS['ROOT_URL'])
            self.assertEqual(response.status_code, http.client.OK)
            self._root = self.check_schema(response)
            return self._root

    def GET(self, url):
        return self.session.get(url)

    def POST(self, url, json=None):
        return self.session.post(url, json=json)

    def PUT(self, url):
        return self.session.put(url)

    def DELETE(self, url):
        return self.session.delete(url)

    def check_schema(self, response):
        """Check that the response JSON data matches the schema
        linked to in the response header.
        Return the response JSON.
        """
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        url = response.links['schema']['url']
        try:
            schema = self.schemas[url]
        except KeyError:
            r = self.GET(url)
            self.assertEqual(r.status_code, http.client.OK)
            schema = r.json()
            self.schemas[url] = schema
        self.validate_schema(result, schema)
        return result

    def validate_schema(self, instance, schema):
        "Validate the JSON instance versus the given JSON schema."
        jsonschema.validate(instance=instance,
                            schema=schema,
                            format_checker=jsonschema.draft7_format_checker)
