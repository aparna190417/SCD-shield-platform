from shield.config.settings import Settings


def test_default_settings() -> None:
    settings = Settings()

    assert settings.app_name == "SCD-SHIELD"
    assert settings.environment == "development"
    assert settings.llm_provider == "fake"
    assert settings.max_repair_attempts == 2


def test_settings_can_be_overridden(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("MAX_REPAIR_ATTEMPTS", "3")

    settings = Settings()

    assert settings.llm_provider == "openai"
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.max_repair_attempts == 3
