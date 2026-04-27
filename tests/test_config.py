"""Tests for configuration module."""

import os
from unittest.mock import patch

import pytest

from a2a_mcp_agent.config import Settings, get_settings


class TestSettings:
    """Test settings configuration."""

    def test_default_values(self) -> None:
        """Test default settings values."""
        settings = Settings()

        assert settings.deepseek_model == "deepseek-v4-flash"
        assert settings.deepseek_base_url == "https://api.deepseek.com/v1"
        assert settings.a2a_port == 8000
        assert settings.gradio_port == 7860
        assert settings.mock_mode is False

    def test_mock_mode_detection(self) -> None:
        """Test mock mode detection."""
        # Without API key, should be mock mode (auto-detection)
        settings = Settings(deepseek_api_key=None, mock_mode=False)
        assert settings.is_mock_mode is True

        # With API key and mock_mode=False, is_mock_mode should be False
        settings = Settings(deepseek_api_key="test-key", mock_mode=False)
        assert settings.is_mock_mode is False

        # Explicit mock mode=True overrides API key
        settings = Settings(deepseek_api_key="test-key", mock_mode=True)
        assert settings.is_mock_mode is True

    def test_environment_override(self) -> None:
        """Test environment variable overrides."""
        with patch.dict(os.environ, {
            "DEEPSEEK_MODEL": "custom-model",
            "A2A_PORT": "9000",
            "MOCK_MODE": "true",
        }):
            settings = Settings()
            assert settings.deepseek_model == "custom-model"
            assert settings.a2a_port == 9000
            assert settings.mock_mode is True

    def test_optional_api_keys(self) -> None:
        """Test optional API key settings."""
        settings = Settings()

        # These should be None by default
        assert settings.deepseek_api_key is None
        assert settings.github_token is None
        assert settings.serper_api_key is None

    def test_get_settings_cached(self) -> None:
        """Test that get_settings returns cached instance."""
        # Clear cache first
        get_settings.cache_clear()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestSettingsValidation:
    """Test settings validation."""

    def test_port_validation(self) -> None:
        """Test port number validation via constructor."""
        # Test that Settings accepts custom ports via constructor
        # Note: pydantic-settings allows field values in constructor
        settings = Settings(a2a_port=8080, gradio_port=3000)
        assert settings.a2a_port == 8080
        assert settings.gradio_port == 3000

    def test_log_level_settings(self) -> None:
        """Test log level configuration via constructor."""
        settings = Settings(log_level="DEBUG")
        assert settings.log_level == "DEBUG"

        settings = Settings(log_level="ERROR")
        assert settings.log_level == "ERROR"

        # Test default log level
        settings_default = Settings()
        assert settings_default.log_level == "INFO"
