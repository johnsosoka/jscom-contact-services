"""
Tests for Cloudflare Turnstile validation
"""

import json
from unittest.mock import patch, MagicMock
import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src" / "contact-listener"
sys.path.insert(0, str(src_path))

from app.turnstile import validate_turnstile, SITE_SECRET_MAP


class TestTurnstileValidation:
    """Test cases for Turnstile token validation"""

    @patch("app.turnstile.requests.post")
    @patch("app.turnstile.ssm.get_parameter")
    def test_valid_token_sosoka_com(self, mock_ssm, mock_post):
        """Test successful validation for sosoka.com"""
        # Mock SSM response
        mock_ssm.return_value = {
            "Parameter": {"Value": "test-secret-key"}
        }

        # Mock Cloudflare API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response

        # Execute validation
        result = validate_turnstile("test-token", "192.168.1.1", "sosoka.com")

        # Assertions
        assert result is True
        mock_ssm.assert_called_once_with(
            Name="/jscom/turnstile/sosoka-com/secret-key",
            WithDecryption=True
        )
        mock_post.assert_called_once_with(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            json={
                "secret": "test-secret-key",
                "response": "test-token",
                "remoteip": "192.168.1.1"
            },
            timeout=5
        )

    @patch("app.turnstile.requests.post")
    @patch("app.turnstile.ssm.get_parameter")
    def test_valid_token_johnsosoka_com(self, mock_ssm, mock_post):
        """Test successful validation for johnsosoka.com"""
        # Mock SSM response
        mock_ssm.return_value = {
            "Parameter": {"Value": "test-secret-key-2"}
        }

        # Mock Cloudflare API response
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response

        # Execute validation
        result = validate_turnstile("test-token", "10.0.0.1", "johnsosoka.com")

        # Assertions
        assert result is True
        mock_ssm.assert_called_once_with(
            Name="/jscom/turnstile/johnsosoka-com/secret-key",
            WithDecryption=True
        )

    @patch("app.turnstile.requests.post")
    @patch("app.turnstile.ssm.get_parameter")
    def test_invalid_token(self, mock_ssm, mock_post):
        """Test failed validation with invalid token"""
        # Mock SSM response
        mock_ssm.return_value = {
            "Parameter": {"Value": "test-secret-key"}
        }

        # Mock Cloudflare API response with failure
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "error-codes": ["invalid-input-response"]
        }
        mock_post.return_value = mock_response

        # Execute validation
        result = validate_turnstile("invalid-token", "192.168.1.1", "sosoka.com")

        # Assertions
        assert result is False

    @patch("app.turnstile.requests.post")
    @patch("app.turnstile.ssm.get_parameter")
    def test_network_error(self, mock_ssm, mock_post):
        """Test handling of network errors"""
        import requests

        # Mock SSM response
        mock_ssm.return_value = {
            "Parameter": {"Value": "test-secret-key"}
        }

        # Mock network error
        mock_post.side_effect = requests.RequestException("Network error")

        # Execute validation
        result = validate_turnstile("test-token", "192.168.1.1", "sosoka.com")

        # Assertions
        assert result is False

    def test_invalid_site(self):
        """Test validation fails for invalid site parameter"""
        result = validate_turnstile("test-token", "192.168.1.1", "invalid.com")
        assert result is False

    def test_empty_site(self):
        """Test validation fails for empty site parameter"""
        result = validate_turnstile("test-token", "192.168.1.1", "")
        assert result is False

    @patch("app.turnstile.requests.post")
    @patch("app.turnstile.ssm.get_parameter")
    def test_ssm_error(self, mock_ssm, mock_post):
        """Test handling of SSM parameter retrieval errors"""
        # Mock SSM error
        mock_ssm.side_effect = Exception("SSM error")

        # Execute validation
        result = validate_turnstile("test-token", "192.168.1.1", "sosoka.com")

        # Assertions
        assert result is False

    @patch("app.turnstile.requests.post")
    @patch("app.turnstile.ssm.get_parameter")
    def test_cloudflare_timeout(self, mock_ssm, mock_post):
        """Test handling of Cloudflare API timeout"""
        import requests

        # Mock SSM response
        mock_ssm.return_value = {
            "Parameter": {"Value": "test-secret-key"}
        }

        # Mock timeout error
        mock_post.side_effect = requests.Timeout("Request timeout")

        # Execute validation
        result = validate_turnstile("test-token", "192.168.1.1", "sosoka.com")

        # Assertions
        assert result is False

    def test_site_secret_map_contains_expected_sites(self):
        """Test that SITE_SECRET_MAP contains expected site configurations"""
        assert "sosoka.com" in SITE_SECRET_MAP
        assert "johnsosoka.com" in SITE_SECRET_MAP
        assert SITE_SECRET_MAP["sosoka.com"] == "/jscom/turnstile/sosoka-com/secret-key"
        assert SITE_SECRET_MAP["johnsosoka.com"] == "/jscom/turnstile/johnsosoka-com/secret-key"

    @patch("app.turnstile.requests.post")
    @patch("app.turnstile.ssm.get_parameter")
    def test_missing_token(self, mock_ssm, mock_post):
        """Test validation with missing token"""
        # Mock SSM response
        mock_ssm.return_value = {
            "Parameter": {"Value": "test-secret-key"}
        }

        # Mock Cloudflare API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "error-codes": ["missing-input-response"]
        }
        mock_post.return_value = mock_response

        # Execute validation
        result = validate_turnstile("", "192.168.1.1", "sosoka.com")

        # Assertions
        assert result is False
