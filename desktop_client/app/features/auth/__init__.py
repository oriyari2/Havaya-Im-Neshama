from desktop_client.app.features.auth.registration import LoginFeature, build_login_feature
from desktop_client.app.features.auth.service import AuthService


def build_auth_service(api_client) -> AuthService:
    """Create the authentication service behind the auth feature public API."""

    return AuthService(api_client)


__all__ = ["LoginFeature", "build_auth_service", "build_login_feature"]
