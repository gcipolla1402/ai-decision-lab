from app.core.config import DOTENV_PATH, ROOT_DIR, Settings


def test_root_dotenv_location() -> None:
    assert DOTENV_PATH == ROOT_DIR / ".env"
    assert ROOT_DIR.name == "AI Decision Lab"


def test_provider_flags_are_boolean() -> None:
    config = Settings()
    assert isinstance(config.gemini_enabled, bool)
    assert isinstance(config.jev_enabled, bool)
