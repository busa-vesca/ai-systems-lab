import pytest

from enterprise_ai_platform.domain import (
    User,
    UserAlreadyExistsError,
    UserRole,
)
from enterprise_ai_platform.repository import InMemoryUserRepository


def test_in_memory_user_repository_normalizes_lookup() -> None:
    repository = InMemoryUserRepository()
    user = User.create(
        email="operator@example.com",
        password_hash="$argon2id$test-hash",
        role=UserRole.OPERATOR,
    )

    repository.add(user)

    assert repository.get(user.id) == user
    assert repository.get_by_email(" Operator@Example.COM ") == user


def test_in_memory_user_repository_rejects_duplicate_email() -> None:
    repository = InMemoryUserRepository()
    repository.add(
        User.create(
            email="viewer@example.com",
            password_hash="$argon2id$first-test-hash",
        )
    )

    with pytest.raises(UserAlreadyExistsError):
        repository.add(
            User.create(
                email="VIEWER@example.com",
                password_hash="$argon2id$second-test-hash",
            )
        )
