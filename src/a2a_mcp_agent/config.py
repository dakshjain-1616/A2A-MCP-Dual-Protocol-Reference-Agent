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
    )

    # DeepSeek API Configuration
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
        """Check if running in mock mode."""
        return self.mock_mode or not self.deepseek_api_key


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
