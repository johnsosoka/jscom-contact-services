"""
Cloudflare Turnstile validation utilities for jscom contact services
"""

import boto3
import requests

ssm = boto3.client("ssm")

# Site-to-secret key mapping
SITE_SECRET_MAP = {
    "sosoka.com": "/jscom/turnstile/sosoka-com/secret-key",
    "johnsosoka.com": "/jscom/turnstile/johnsosoka-com/secret-key",
}


def validate_turnstile(token: str, remote_ip: str, site: str) -> bool:
    """
    Validate Cloudflare Turnstile token for a specific site

    This function retrieves the site-specific Turnstile secret key from AWS
    Systems Manager Parameter Store and validates the token with Cloudflare's API.

    Args:
        token: Turnstile response token from frontend
        remote_ip: Client IP address
        site: Site domain (sosoka.com or johnsosoka.com)

    Returns:
        True if validation succeeds, False otherwise
    """
    try:
        # Validate site parameter
        if site not in SITE_SECRET_MAP:
            print(f"Invalid site parameter: {site}")
            return False

        # Get site-specific secret key from Parameter Store
        secret_path = SITE_SECRET_MAP[site]
        response = ssm.get_parameter(Name=secret_path, WithDecryption=True)
        secret_key = response["Parameter"]["Value"]

        # Validate with Cloudflare API
        verify_response = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            json={"secret": secret_key, "response": token, "remoteip": remote_ip},
            timeout=5,
        )

        result = verify_response.json()
        success = result.get("success", False)

        if not success:
            error_codes = result.get("error-codes", [])
            print(f"Turnstile validation failed: {error_codes}, IP: {remote_ip}")

        return success

    except requests.RequestException as e:
        print(f"Network error validating Turnstile token: {str(e)}")
        return False
    except Exception as e:
        print(f"Error validating Turnstile token: {str(e)}")
        return False
