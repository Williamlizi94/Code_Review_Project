from app.config import Settings


def test_build_groq_llm_uses_qwen_model(monkeypatch):
    from app.agent import graph

    monkeypatch.setattr(
        graph,
        "settings",
        Settings(
            llm_provider="groq",
            groq_api_key="gsk-test",
            groq_model="qwen/qwen3.6-27b",
        ),
    )

    llm = graph._build_llm()

    assert llm.model_name == "qwen/qwen3.6-27b"


def test_groq_llm_provider_is_configured_with_groq_key():
    settings = Settings(llm_provider="groq", groq_api_key="gsk-test")

    assert settings.llm_is_configured is True


def test_groq_llm_provider_is_not_configured_without_groq_key():
    settings = Settings(llm_provider="groq", groq_api_key="")

    assert settings.llm_is_configured is False


def test_ollama_llm_provider_does_not_require_api_key():
    settings = Settings(
        llm_provider="ollama",
        ollama_base_url="http://localhost:11434",
        ollama_model="qwen3-coder:30b",
    )

    assert settings.llm_is_configured is True
