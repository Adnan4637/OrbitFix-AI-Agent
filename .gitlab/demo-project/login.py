from auth import UserService

def login(username, password):
    service = UserService()
    if service.authenticate(username, password):
        return "Login successful"
    return "Login failed"