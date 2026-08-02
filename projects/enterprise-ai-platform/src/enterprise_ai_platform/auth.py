from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError


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
