# OrbitFix-AI demo — AuthManager service
class AuthManager:
    def __init__(self):
        self.users = {}

    def authenticate(self, username, password):
        return self.users.get(username) == password

    def create_user(self, username, password):
        self.users[username] = password
        return True