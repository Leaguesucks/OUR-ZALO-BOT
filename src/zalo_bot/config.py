"""Validated environment settings; real environment values override .env."""

from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ZALO_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    bot_token: SecretStr
    poll_timeout: int = Field(default=30, ge=1, le=60)
    request_timeout: float = Field(default=40, gt=0, allow_inf_nan=False)
    retry_initial: float = Field(default=1, gt=0, allow_inf_nan=False)
    retry_max: float = Field(default=30, gt=0, le=300, allow_inf_nan=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        token = self.bot_token.get_secret_value()
        if not token or token != token.strip() or any(c.isspace() for c in token):
            raise ValueError("ZALO_BOT_TOKEN must be nonempty and contain no whitespace")
        if any(c in token for c in "/?#"):
            raise ValueError("ZALO_BOT_TOKEN contains invalid URL path characters")
        if self.request_timeout <= self.poll_timeout:
            raise ValueError("ZALO_REQUEST_TIMEOUT must exceed ZALO_POLL_TIMEOUT")
        if self.retry_max < self.retry_initial:
            raise ValueError("ZALO_RETRY_MAX must be at least ZALO_RETRY_INITIAL")
        return self
