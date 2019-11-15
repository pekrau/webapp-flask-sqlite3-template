"Test the root API endpoint."

import http.client

import base


class Root(base.Base):
    "Test the root API endpoint."

    def test_root_data(self):
        "Get API root JSON."
        url = f"{base.SETTINGS['ROOT_URL']}"
        response = self.session.get(url)
        self.check_schema(response)


if __name__ == '__main__':
    base.run()
