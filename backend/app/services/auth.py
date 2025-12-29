from dataclasses import dataclass

from supabase import Client, create_client
from supabase.client import ClientOptions

from app.schemas.auth import AuthenticatedUser


@dataclass(frozen=True)
class AuthServiceError(Exception):
    user_message: str
    status_code: int


class SupabaseAuthService:
    def __init__(self, supabase_url: str | None, supabase_anon_key: str | None):
        self._supabase_url = supabase_url
        self._supabase_anon_key = supabase_anon_key

    @property
    def is_configured(self) -> bool:
        return bool(self._supabase_url and self._supabase_anon_key)

    def get_user_for_token(self, access_token: str) -> AuthenticatedUser:
        if not self.is_configured:
            raise AuthServiceError(
                user_message="Authentication is not configured on the backend.",
                status_code=503,
            )

        try:
            client = self._create_client()
            response = client.auth.get_user(access_token)
            user = response.user
        except Exception as error:
            raise AuthServiceError(
                user_message="Your session is invalid or has expired.",
                status_code=401,
            ) from error

        if not user or not user.id:
            raise AuthServiceError(
                user_message="Your session is invalid or has expired.",
                status_code=401,
            )

        return AuthenticatedUser(
            id=str(user.id),
            email=getattr(user, "email", None),
        )

    def _create_client(self) -> Client:
        return create_client(
            self._supabase_url,
            self._supabase_anon_key,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False,
            ),
        )
