class Authorization(object):
    def __init__(self, username, password):
        self._username = username
        self._password = password

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    def __eq__(self, other):
        return (self._username == other._username and
                self._password == other._password)
