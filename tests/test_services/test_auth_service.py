from app.services.auth import hash_password, verify_password


def test_hash_and_verify_password():
    raw = "SecurePass123"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed)
