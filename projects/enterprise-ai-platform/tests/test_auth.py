import pytest

from enterprise_ai_platform.auth import PasswordHasher


def test_password_is_hashed_and_can_be_verified() -> None:
    hasher = PasswordHasher()

    password_hash = hasher.hash("correct-horse-battery-staple")

    assert password_hash != "correct-horse-battery-staple"
    assert password_hash.startswith("$argon2")
    assert hasher.verify("correct-horse-battery-staple", password_hash) is True
    assert hasher.verify("wrong-password", password_hash) is False


def test_short_password_is_rejected() -> None:
    hasher = PasswordHasher()

    with pytest.raises(ValueError, match="at least 12 characters"):
        hasher.hash("too-short")


def test_unknown_hash_format_is_rejected_safely() -> None:
    hasher = PasswordHasher()

    assert hasher.verify("password", "not-a-supported-hash") is False
