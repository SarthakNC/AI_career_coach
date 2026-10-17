import ipaddress
import socket
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException, status

MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB maximum response size
REQUEST_TIMEOUT = 12.0  # 12 seconds timeout


def is_ip_allowed(ip_str: str) -> bool:
    """
    Check if an IP address is public and safe to connect to (not private/loopback/link-local/multicast/reserved).
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return False
        # Block IPv4-mapped IPv6 addresses that map to private IPs
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
            if ip.ipv4_mapped.is_private or ip.ipv4_mapped.is_loopback:
                return False
        return True
    except ValueError:
        return False


def validate_url_safety(url_str: str) -> None:
    """
    Validates that a URL is HTTP or HTTPS, has a valid hostname,
    and resolves strictly to public, non-private IP addresses to prevent SSRF.
    """
    if not url_str or not url_str.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job posting URL cannot be empty."
        )

    url_str = url_str.strip()
    try:
        parsed = urlparse(url_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL format."
        )

    if parsed.scheme.lower() not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL scheme. Only HTTP and HTTPS URLs are allowed."
        )

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL: Hostname is missing."
        )

    # Disallow known localhost/internal naming patterns
    lower_host = hostname.lower()
    if lower_host in ("localhost", "127.0.0.1", "::1") or lower_host.endswith(".local") or lower_host.endswith(".internal"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access to internal, loopback, or private host addresses is forbidden."
        )

    # Resolve DNS and check all resolved IP addresses
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to resolve host '{hostname}'. Please verify the URL."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"DNS resolution error for host '{hostname}': {str(e)}"
        )

    for item in addr_info:
        sockaddr = item[4]
        ip_addr = sockaddr[0]
        if not is_ip_allowed(ip_addr):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access to private or local network resources is forbidden (SSRF protection)."
            )


def fetch_job_page(url_str: str) -> str:
    """
    Safely retrieves the raw HTML content of a public job posting URL with redirect revalidation and SSRF protection.
    """
    validate_url_safety(url_str)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 CareerProof/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    current_url = url_str
    max_redirects = 5

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=False) as client:
            for _ in range(max_redirects):
                validate_url_safety(current_url)

                try:
                    response = client.get(current_url, headers=headers)
                except httpx.TimeoutException:
                    raise HTTPException(
                        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                        detail="The request to fetch the job posting timed out. Please paste the job description manually."
                    )
                except (httpx.ConnectError, httpx.RequestError) as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Could not connect to job posting URL: {str(e)}. Please paste the job description manually."
                    )

                # Handle redirects manually to revalidate target URL safety
                if response.is_redirect:
                    location = response.headers.get("Location")
                    if not location:
                        break
                    # Build absolute URL if relative
                    current_url = str(response.url.join(location))
                    continue

                # Check HTTP status
                if response.status_code in (401, 403):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="The job posting page is protected by authentication or anti-bot defenses (HTTP 401/403). Please paste the job description manually."
                    )
                if response.status_code == 404:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="The job posting URL returned 404 Not Found. Please check the link or paste the description manually."
                    )
                if response.status_code >= 400:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"The job posting host returned HTTP error {response.status_code}. Please paste the description manually."
                    )

                # Validate content type
                content_type = response.headers.get("Content-Type", "").lower()
                if not any(t in content_type for t in ("text/html", "application/xhtml+xml", "text/plain")):
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail=f"Unsupported content format ('{content_type}'). Please paste the job description text manually."
                    )

                # Check content length
                content = response.content
                if len(content) > MAX_CONTENT_LENGTH:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="The job posting page exceeded the maximum allowed size (5MB). Please paste the description manually."
                    )

                return response.text

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many redirects encountered while fetching the job posting. Please paste the description manually."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve job posting: {str(e)}. Please paste the job description manually."
        )
