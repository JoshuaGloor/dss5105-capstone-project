"""Where we build chat models. Set LLM_MODEL in .env to pick one."""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel


def get_model(**kwargs) -> BaseChatModel:
    """Chat model named by LLM_MODEL, e.g. anthropic:claude-sonnet-5 or openai:gpt-4.1.

    We don't set temperature: recent Anthropic models reject it outright (400).
    Pass it yourself if you're on a provider that still accepts it.

    Raises RuntimeError if LLM_MODEL is missing or empty.
    """
    load_dotenv(override=False)
    spec = os.getenv("LLM_MODEL")
    if not spec:
        raise RuntimeError(
            "LLM_MODEL is not set. Copy .env.example to .env and set it, e.g. LLM_MODEL=anthropic:claude-sonnet-5"
        )
    return init_chat_model(spec, **kwargs)


def model_configured() -> bool:
    """Whether LLM_MODEL names a model; says nothing about keys or reachability, and calls nothing."""
    load_dotenv(override=False)
    return bool(os.getenv("LLM_MODEL"))


def model_label() -> str:
    """The configured model name for display, e.g. 'openai:gpt-4.1'; never a key."""
    load_dotenv(override=False)
    return os.getenv("LLM_MODEL") or "not configured"
