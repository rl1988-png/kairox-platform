import pytest
from pydantic import ValidationError

from kairox_api.config.settings import Settings


def _production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": "production",
        "web_url": "https://app.kairox.example",
        "api_url": "https://api.kairox.example",
        "jwt_secret": "j" * 48,
        "csrf_secret": "c" * 48,
        "cookie_secure": True,
        "cors_origins": "https://app.kairox.example",
        "tron_deposit_address": "T" + "a" * 33,
        "trongrid_api_key": "trongrid-prod-key",
        "log_json": True,
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)


def _assert_invalid(message: str, **overrides: object) -> None:
    with pytest.raises(ValidationError) as exc:
        _production_settings(**overrides)
    assert message in str(exc.value)


def test_valid_production_settings_pass() -> None:
    settings = _production_settings()

    assert settings.app_env == "production"
    assert settings.cors_origin_list == ["https://app.kairox.example"]


def test_production_rejects_short_jwt_secret() -> None:
    _assert_invalid("JWT_SECRET must be at least 32 random characters", jwt_secret="short")


def test_production_rejects_insecure_cookie() -> None:
    _assert_invalid("COOKIE_SECURE must be true in production", cookie_secure=False)


def test_production_rejects_http_urls() -> None:
    _assert_invalid("WEB_URL must use HTTPS in production", web_url="http://app.kairox.example")


def test_production_rejects_cors_without_web_url() -> None:
    _assert_invalid(
        "CORS_ORIGINS must include WEB_URL in production",
        cors_origins="https://other.kairox.example",
    )


def test_production_rejects_missing_tron_deposit_address() -> None:
    _assert_invalid("TRON_DEPOSIT_ADDRESS must be set in production", tron_deposit_address="")


def test_production_rejects_missing_trongrid_key_when_watcher_enabled() -> None:
    _assert_invalid("TRONGRID_API_KEY must be set", trongrid_api_key="")


def test_production_allows_missing_trongrid_key_when_watcher_disabled() -> None:
    settings = _production_settings(trongrid_api_key="", recharge_watcher_enabled=False)

    assert settings.recharge_watcher_enabled is False


def test_rejects_unknown_ai_provider_in_any_environment() -> None:
    with pytest.raises(ValidationError) as exc:
        Settings(ai_default_provider="bad-provider", _env_file=None)

    assert "AI_DEFAULT_PROVIDER must be one of" in str(exc.value)
