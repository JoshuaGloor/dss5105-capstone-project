import pytest


def test_get_model_fails_loudly_without_llm_model(monkeypatch):
    """Without this, an unset LLM_MODEL only blows up later inside langchain."""
    from dss5105 import llm

    # Stub out load_dotenv so a local .env can't make this test nondeterministic.
    monkeypatch.setattr(llm, "load_dotenv", lambda **kwargs: None)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    with pytest.raises(RuntimeError, match="LLM_MODEL is not set"):
        llm.get_model()


@pytest.mark.live
def test_real_provider_roundtrip():
    """Run deliberately to verify your API key works with your specified model."""
    from dss5105.llm import get_model

    reply = get_model().invoke("Reply with exactly: ok")
    assert "ok" in reply.text.lower()
