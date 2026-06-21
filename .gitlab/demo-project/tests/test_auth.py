from auth import UserService

def test_authenticate():
    service = UserService()
    service.create_user("alice", "secret")
    assert service.authenticate("alice", "secret") is True

def test_authenticate_fail():
    service = UserService()
    assert service.authenticate("bob", "wrong") is False
