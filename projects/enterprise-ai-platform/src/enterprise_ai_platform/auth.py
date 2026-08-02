from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from .domain import User, UserRole
from .repository import UserRepository


MIN_PASSWORD_LENGTH = 12


class PasswordHasher:
    """Hash and verify user passwords without storing plaintext secrets."""

    def __init__(self) -> None:
        self._password_hash = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"password must contain at least {MIN_PASSWORD_LENGTH} characters"
            )
        return self._password_hash.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._password_hash.verify(password, password_hash)
        except UnknownHashError:
            return False


class RegistrationService:
    def __init__(
        self,
        *,
        users: UserRepository,
        passwords: PasswordHasher,
    ) -> None:
        self._users = users
        self._passwords = passwords

    def register(self, *, email: str, password: str) -> User:
        user = User.create(
            email=email,
            password_hash=self._passwords.hash(password),
            role=UserRole.VIEWER,
        )
        self._users.add(user)
        return user
