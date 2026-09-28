from app.core.config import Settings


def test_email_settings_read_the_railway_names_and_stay_off(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", "brevo")
    monkeypatch.setenv("EMAIL_ENABLED", "false")
    monkeypatch.setenv("EMAIL_FROM_ADDRESS", "notifications@example.com")
    monkeypatch.setenv("EMAIL_FROM_NAME", "JobReady")
    monkeypatch.setenv("BREVO_API_KEY", "REPLACE_WITH_REAL_BREVO_API_KEY")

    loaded = Settings()

    assert loaded.email_provider == "brevo"
    assert loaded.email_enabled is False
    assert loaded.email_from_address == "notifications@example.com"
    assert loaded.email_from_name == "JobReady"
    assert loaded.brevo_api_key == "REPLACE_WITH_REAL_BREVO_API_KEY"
    assert loaded.email_can_send is False
    assert loaded.email_block_reason == "email_disabled"


def _load(monkeypatch, **values: str) -> Settings:
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    return Settings()


def test_placeholder_sender_and_key_cannot_send_even_if_enabled(monkeypatch):
    loaded = _load(
        monkeypatch,
        EMAIL_PROVIDER="brevo",
        EMAIL_ENABLED="true",
        EMAIL_FROM_ADDRESS="notifications@example.com",
        EMAIL_FROM_NAME="JobReady",
        BREVO_API_KEY="REPLACE_WITH_REAL_BREVO_API_KEY",
    )
    assert loaded.email_enabled is True
    assert loaded.email_can_send is False
    assert loaded.email_block_reason == "placeholder_configuration"


def test_each_placeholder_blocks_sending_when_enabled(monkeypatch):
    placeholder_sender = _load(
        monkeypatch,
        EMAIL_PROVIDER="brevo",
        EMAIL_ENABLED="true",
        EMAIL_FROM_ADDRESS="notifications@example.com",
        EMAIL_FROM_NAME="JobReady",
        BREVO_API_KEY="not-a-real-key",
    )
    assert placeholder_sender.email_can_send is False
    assert placeholder_sender.email_block_reason == "placeholder_configuration"

    placeholder_key = _load(
        monkeypatch,
        EMAIL_PROVIDER="brevo",
        EMAIL_ENABLED="true",
        EMAIL_FROM_ADDRESS="notifications@jobready.example",
        EMAIL_FROM_NAME="JobReady",
        BREVO_API_KEY="REPLACE_WITH_REAL_BREVO_API_KEY",
    )
    assert placeholder_key.email_can_send is False
    assert placeholder_key.email_block_reason == "placeholder_configuration"


def test_disabled_flag_blocks_sending_with_non_placeholder_values(monkeypatch):
    loaded = _load(
        monkeypatch,
        EMAIL_PROVIDER="brevo",
        EMAIL_ENABLED="false",
        EMAIL_FROM_ADDRESS="notifications@jobready.example",
        EMAIL_FROM_NAME="JobReady",
        BREVO_API_KEY="not-a-real-key",
    )
    assert loaded.email_enabled is False
    assert loaded.email_can_send is False
    assert loaded.email_block_reason == "email_disabled"
