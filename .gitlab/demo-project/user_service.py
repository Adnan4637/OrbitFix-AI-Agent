from auth import UserService

def register_user(username, password):
    service = UserService()
    return service.create_user(username, password)
