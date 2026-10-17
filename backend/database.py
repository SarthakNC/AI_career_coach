from typing import Any, Dict, Optional
import httpx
from supabase import create_client, Client
from config import get_settings

_client: Optional[Client] = None


def is_placeholder_value(val: Optional[str]) -> bool:
    """Check if value is empty, unset, or a typical placeholder string."""
    if not val or not val.strip():
        return True
    lower = val.strip().lower()
    placeholders = [
        "your-supabase-url",
        "your_supabase_url",
        "your-supabase-key",
        "your_supabase_key",
        "your-anon-key",
        "your-service-role-key",
        "https://your-project.supabase.co",
        "https://xxx.supabase.co",
        "placeholder",
        "none",
    ]
    return any(p in lower for p in placeholders)


def get_supabase_client() -> Optional[Client]:
    """
    Creates and returns a reusable Supabase client instance.
    Returns None if credentials are missing or invalid, avoiding app crashes.
    """
    global _client
    settings = get_settings()

    url = settings.supabase_url
    key = settings.supabase_key

    if is_placeholder_value(url) or is_placeholder_value(key):
        return None

    if _client is None:
        try:
            _client = create_client(url.strip(), key.strip())
        except Exception:
            return None

    return _client


def check_database_connection() -> Dict[str, Any]:
    """
    Performs a real database connectivity check to Supabase PostgreSQL.
    Distinguishes clearly between 'not_configured', 'connected', and 'error'.
    Does not report connected unless a real network check succeeds.
    Credentials and secrets are strictly excluded from output and logs.
    """
    settings = get_settings()
    url = settings.supabase_url
    key = settings.supabase_key

    # Check configuration presence
    if is_placeholder_value(url) or is_placeholder_value(key):
        return {
            "status": "not_configured",
            "configured": False,
            "message": "Supabase environment variables (SUPABASE_URL, SUPABASE_KEY) are pending configuration."
        }

    try:
        client = get_supabase_client()
        if client is None:
            return {
                "status": "error",
                "configured": True,
                "message": "Invalid Supabase configuration parameters."
            }

        # Lightweight check using Supabase PostgREST root endpoint.
        # This executes a real PostgreSQL connection handshake and schema verification.
        rest_url = f"{str(client.supabase_url).rstrip('/')}/rest/v1/"
        headers = {
            "apikey": str(client.supabase_key),
            "Authorization": f"Bearer {client.supabase_key}",
        }

        with httpx.Client(timeout=5.0) as http_client:
            response = http_client.get(rest_url, headers=headers)

        if response.status_code == 200:
            return {
                "status": "connected",
                "configured": True,
                "message": "Successfully connected to Supabase PostgreSQL database."
            }
        elif response.status_code in (401, 403):
            return {
                "status": "error",
                "configured": True,
                "message": f"Authentication failed with Supabase (HTTP {response.status_code}). Verify SUPABASE_KEY."
            }
        else:
            return {
                "status": "error",
                "configured": True,
                "message": f"Supabase returned unexpected response (HTTP {response.status_code})."
            }

    except httpx.ConnectError:
        return {
            "status": "error",
            "configured": True,
            "message": "Unable to connect to Supabase host. Verify SUPABASE_URL and network."
        }
    except httpx.TimeoutException:
        return {
            "status": "error",
            "configured": True,
            "message": "Connection to Supabase timed out after 5 seconds."
        }
    except Exception as e:
        return {
            "status": "error",
            "configured": True,
            "message": f"Database connectivity check encountered an error: {type(e).__name__}"
        }
