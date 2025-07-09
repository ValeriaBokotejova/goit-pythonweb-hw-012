from app.models.user import User, UserRole


def test_user_model_defaults():
    user = User(
        username="john",
        email="john@example.com",
        password="hashedpass",
        is_verified=False,
        role=UserRole.USER,
    )
    assert user.is_verified is False
    assert user.role == UserRole.USER
