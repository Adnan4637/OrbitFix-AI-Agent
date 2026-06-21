from login import login

def test_login_success():
    result = login("alice", "secret")
    assert isinstance(result, str)