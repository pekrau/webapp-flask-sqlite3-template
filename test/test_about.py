"Test the about API endpoints."

import http.client

import base


class About(base.Base):
    "Test the about API endpoint."

    def test_software(self):
        "Get software API JSON."
        url = f"{base.SETTINGS['ROOT_URL']}/about/software"
        response = self.session.get(url)
        self.check_schema(response)


if __name__ == '__main__':
    base.run()
