from uuid import UUID
from fastapi import Header, HTTPException, status
import httpx
from config import get_settings


class AuthenticatedUser:
    def __init__(self, user_id: UUID, email: str, token: str):
        self.user_id = user_id
        self.email = email
        self.token = token


def get_current_user(authorization: str = Header(..., description="Supabase Bearer Token")) -> AuthenticatedUser:
    """
    Validates Supabase JWT bearer token by querying Supabase Auth endpoint /auth/v1/user.
    This guarantees that the token is valid, active, and not revoked, without needing
    to handle complex asymmetric key rotation manually.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must follow format 'Bearer <token>'."
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token cannot be empty."
        )

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service configuration is missing."
        )

    auth_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/user"
    headers = {
        "apikey": settings.supabase_key,
        "Authorization": f"Bearer {token}",
    }

    try:
        with httpx.Client(timeout=6.0) as client:
            res = client.get(auth_url, headers=headers)
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authentication token. Please log in again."
                )
            user_data = res.json()
            user_id_str = user_data.get("id")
            if not user_id_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User ID not present in validated token."
                )
            user_id = UUID(user_id_str)
            email = user_data.get("email", "")
            return AuthenticatedUser(user_id=user_id, email=email, token=token)

    except HTTPException:
        raise
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to verify authentication with Supabase: {str(e)}"
        )
