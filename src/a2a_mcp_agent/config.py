"""Configuration management for A2A MCP Agent."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # OpenRouter (preferred — one key for all frontier models)
    openrouter_api_key: Optional[str] = Field(default=None, alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )

    # Direct DeepSeek API (optional fallback if you have a Moonshot/DeepSeek key)
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1", alias="DEEPSEEK_BASE_URL"
    )
    deepseek_model: str = Field(default="deepseek-v4-flash", alias="DEEPSEEK_MODEL")

    # A2A Server Configuration
    a2a_host: str = Field(default="0.0.0.0", alias="A2A_HOST")
    a2a_port: int = Field(default=8000, alias="A2A_PORT")
    a2a_debug: bool = Field(default=False, alias="A2A_DEBUG")

    # Gradio UI Configuration
    gradio_host: str = Field(default="0.0.0.0", alias="GRADIO_HOST")
    gradio_port: int = Field(default=7860, alias="GRADIO_PORT")
    gradio_share: bool = Field(default=False, alias="GRADIO_SHARE")

    # MCP Configuration
    mcp_timeout: int = Field(default=30, alias="MCP_TIMEOUT")
    mcp_max_retries: int = Field(default=3, alias="MCP_MAX_RETRIES")

    # Mock Mode
    mock_mode: bool = Field(default=False, alias="MOCK_MODE")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # Optional API Keys
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")
    serper_api_key: Optional[str] = Field(default=None, alias="SERPER_API_KEY")

    @property
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode.

        Mock mode is on if explicitly enabled, or if no API key is configured
        on either OpenRouter (preferred) or the direct DeepSeek path.
        """
        return self.mock_mode or not (self.openrouter_api_key or self.deepseek_api_key)

    @property
    def effective_api_key(self) -> Optional[str]:
        """The API key to actually send. OpenRouter wins if both are set."""
        return self.openrouter_api_key or self.deepseek_api_key

    @property
    def effective_base_url(self) -> str:
        """The base URL paired with the effective API key."""
        return self.openrouter_base_url if self.openrouter_api_key else self.deepseek_base_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
