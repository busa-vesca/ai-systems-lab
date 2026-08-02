import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from .domain import User, UserRole
from .repository import UserRepository


MIN_PASSWORD_LENGTH = 12
ACCESS_TOKEN_MINUTES = 30
JWT_ALGORITHM = "HS256"
JWT_AUDIENCE = "enterprise-ai-platform-api"
JWT_ISSUER = "enterprise-ai-platform"


class InvalidCredentialsError(Exception):
    """The supplied email/password pair cannot authenticate a user."""


class AuthenticationNotConfiguredError(Exception):
    """JWT authentication is unavailable until a secret is configured."""


class InvalidAccessTokenError(Exception):
    """A bearer token cannot identify an active user."""


@dataclass(frozen=True, slots=True)
class AccessToken:
    value: str
    token_type: str
    expires_in: int


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


class JWTTokenService:
    def __init__(
        self,
        *,
        secret: str,
        lifetime: timedelta = timedelta(minutes=ACCESS_TOKEN_MINUTES),
    ) -> None:
        if len(secret) < 32:
            raise ValueError("JWT secret must contain at least 32 characters")
        self._secret = secret
        self._lifetime = lifetime

    @classmethod
    def from_environment(cls) -> "JWTTokenService | None":
        secret = os.getenv("JWT_SECRET")
        return cls(secret=secret) if secret else None

    def issue(self, user: User) -> AccessToken:
        now = datetime.now(UTC)
        expires_at = now + self._lifetime
        value = jwt.encode(
            {
                "sub": str(user.id),
                "role": user.role.value,
                "iat": now,
                "exp": expires_at,
                "iss": JWT_ISSUER,
                "aud": JWT_AUDIENCE,
            },
            self._secret,
            algorithm=JWT_ALGORITHM,
        )
        return AccessToken(
            value=value,
            token_type="bearer",
            expires_in=int(self._lifetime.total_seconds()),
        )

    def decode(self, token: str) -> dict[str, object]:
        return jwt.decode(
            token,
            self._secret,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"require": ["sub", "iat", "exp", "iss", "aud"]},
        )


class AuthenticationService:
    def __init__(
        self,
        *,
        users: UserRepository,
        passwords: PasswordHasher,
        tokens: JWTTokenService,
    ) -> None:
        self._users = users
        self._passwords = passwords
        self._tokens = tokens

    def login(self, *, email: str, password: str) -> AccessToken:
        user = self._users.get_by_email(email)
        if (
            user is None
            or not user.is_active
            or not self._passwords.verify(password, user.password_hash)
        ):
            raise InvalidCredentialsError("invalid email or password")
        return self._tokens.issue(user)

    def current_user(self, token: str) -> User:
        try:
            claims = self._tokens.decode(token)
            user_id = UUID(str(claims["sub"]))
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as error:
            raise InvalidAccessTokenError("invalid access token") from error

        user = self._users.get(user_id)
        if user is None or not user.is_active:
            raise InvalidAccessTokenError("invalid access token")
        return user
