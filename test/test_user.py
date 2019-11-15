"Test the user API endpoints."

import http.client

import base


class User(base.Base):
    "Test the user API endpoints."

    def test_user_data(self):
        "Get user JSON."
        url = f"{base.SETTINGS['ROOT_URL']}/user/{base.SETTINGS['USERNAME']}"
        response = self.session.get(url)
        user = self.check_schema(response)

    def test_users_data(self):
        "Get all users JSON."
        url = f"{base.SETTINGS['ROOT_URL']}/user"
        response = self.session.get(url)
        user = self.check_schema(response)


if __name__ == '__main__':
    base.run()
