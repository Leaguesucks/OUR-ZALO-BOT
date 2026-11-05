import pytest
from pydantic import ValidationError

from zalo_bot.config import Settings


@pytest.mark.parametrize(
    "overrides",
    [
        {"bot_token": ""},
        {"bot_token": "has spaces"},
        {"bot_token": "invalid/path"},
        {"poll_timeout": 0},
        {"request_timeout": 30},
        {"retry_initial": 0},
        {"retry_max": 0.5},
        {"request_timeout": float("inf")},
        {"log_level": "INVALID"},
    ],
)
def test_invalid_settings(overrides):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **({"bot_token": "123:secret"} | overrides))


def test_environment_overrides_dotenv(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"
    dotenv.write_text("ZALO_BOT_TOKEN=file-token\nZALO_POLL_TIMEOUT=15\n")
    monkeypatch.setenv("ZALO_BOT_TOKEN", "env-token")
    config = Settings(_env_file=dotenv)
    assert config.bot_token.get_secret_value() == "env-token"
    assert config.poll_timeout == 15
    assert "env-token" not in repr(config)
