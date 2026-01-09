"""
Provider-agnostic LLM client with mock support and database credential storage.

This module provides a unified interface for LLM calls with:
- Mock mode for testing (MOCK_LLM=true)
- Real LLM integration via LangChain (OpenAI, Anthropic, Google)
- Automatic provider detection based on model name
- JSON mode support for structured outputs
- Organization-level API key management via database

Supported Providers:
- OpenAI (gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc.)
- Anthropic (claude-3-opus, claude-3-sonnet, claude-3-haiku, etc.)
- Google (gemini-1.5-pro, gemini-1.5-flash, etc.)

Environment Variables:
    MOCK_LLM: Set to "true" to enable mock mode for testing
"""

import os
import uuid
from typing import Optional

from sqlalchemy.orm import Session


def call_json(
    system: str,
    user: str,
    *,
    model: str,
    temperature: float = 0.0,
    response_format_json: bool = True,
    organization_id: Optional[uuid.UUID] = None,
    db: Optional[Session] = None,
) -> str:
    """
    Call LLM to generate JSON response.

    This function is the single point of integration for all LLM providers.
    Supports mock mode for testing and real LLM integration via LangChain.

    Args:
        system: System prompt defining LLM behavior
        user: User prompt with the task/question
        model: Model identifier (e.g., "gpt-4o-mini", "claude-3-sonnet", "gemini-1.5-pro")
        temperature: Temperature for sampling (0.0 = deterministic)
        response_format_json: Whether to request JSON-formatted output
        organization_id: Organization UUID for fetching API credentials
        db: Database session for credential lookup

    Returns:
        Raw JSON string from LLM

    Raises:
        ValueError: If required API key is missing for the selected provider
        Exception: If LLM API call fails

    Environment Variables:
        MOCK_LLM: Set to "true" to enable mock mode for testing

    Examples:
        >>> os.environ["MOCK_LLM"] = "true"
        >>> result = call_json("You are helpful", "Say hello", model="gpt-4")
        >>> "scores" in result and "coaching" in result
        True
    """
    mock_llm = os.getenv("MOCK_LLM", "false").lower() == "true"

    if mock_llm:
        # Return deterministic mock JSON conforming to SPIN assessment schema
        # This enables testing without actual LLM API calls
        return _get_mock_response()

    # Real LLM integration via LangChain
    provider = _detect_provider(model)

    # Get API key from database if organization_id and db provided
    api_key = None
    if organization_id and db:
        api_key = _get_api_key_from_db(db, organization_id, provider)

    llm = _create_llm_instance(
        provider=provider,
        model=model,
        temperature=temperature,
        response_format_json=response_format_json,
        api_key=api_key,
    )

    response = _invoke_llm(llm, system, user)
    return response


def _detect_provider(model: str) -> str:
    """
    Detect LLM provider based on model name.

    Args:
        model: Model identifier (e.g., "gpt-4o-mini", "claude-3-sonnet", "gemini-1.5-pro")

    Returns:
        Provider name: "openai", "anthropic", or "google"

    Raises:
        ValueError: If provider cannot be determined from model name
    """
    model_lower = model.lower()

    if any(prefix in model_lower for prefix in ["gpt-", "o1-", "text-davinci", "gpt3", "gpt4"]):
        return "openai"
    elif any(prefix in model_lower for prefix in ["claude-", "claude3"]):
        return "anthropic"
    elif any(prefix in model_lower for prefix in ["gemini-", "gemini1", "gemini2"]):
        return "google"
    else:
        raise ValueError(
            f"Cannot determine provider for model '{model}'. "
            "Supported prefixes: gpt-, o1-, claude-, gemini-"
        )


def _get_api_key_from_db(
    db: Session, organization_id: uuid.UUID, provider: str
) -> Optional[str]:
    """
    Get decrypted API key from database for an organization and provider.

    Args:
        db: Database session
        organization_id: Organization UUID
        provider: Provider name ("openai", "anthropic", "google")

    Returns:
        Decrypted API key string if found, None otherwise
    """
    from app.crud import llm_credential as cred_crud
    from app.models.llm_credential import LLMProvider

    provider_map = {
        "openai": LLMProvider.OPENAI,
        "anthropic": LLMProvider.ANTHROPIC,
        "google": LLMProvider.GOOGLE,
    }

    provider_enum = provider_map.get(provider)
    if not provider_enum:
        return None

    return cred_crud.get_decrypted_api_key(db, organization_id, provider_enum)


def _create_llm_instance(
    provider: str,
    model: str,
    temperature: float,
    response_format_json: bool,
    api_key: Optional[str] = None,
):
    """
    Create LLM instance using LangChain based on provider.

    Args:
        provider: Provider name ("openai", "anthropic", or "google")
        model: Model identifier
        temperature: Temperature for sampling
        response_format_json: Whether to request JSON-formatted output
        api_key: API key (from database). Falls back to env var if None.

    Returns:
        Configured LangChain LLM instance

    Raises:
        ValueError: If required API key is missing
        ImportError: If required LangChain package is not installed
    """
    if provider == "openai":
        # Use provided key or fall back to environment variable
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "OpenAI API key not configured. "
                "Please add your OpenAI API key in Settings > Integrations."
            )

        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "langchain-openai package is required for OpenAI models. "
                "Install it with: pip install langchain-openai"
            )

        # Configure model_kwargs for JSON mode if requested
        model_kwargs = {}
        if response_format_json:
            model_kwargs["response_format"] = {"type": "json_object"}

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=key,
            model_kwargs=model_kwargs if model_kwargs else None
        )

    elif provider == "anthropic":
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError(
                "Anthropic API key not configured. "
                "Please add your Anthropic API key in Settings > Integrations."
            )

        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError(
                "langchain-anthropic package is required for Anthropic models. "
                "Install it with: pip install langchain-anthropic"
            )

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            anthropic_api_key=key
        )

    elif provider == "google":
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError(
                "Google API key not configured. "
                "Please add your Google API key in Settings > Integrations."
            )

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError(
                "langchain-google-genai package is required for Google models. "
                "Install it with: pip install langchain-google-genai"
            )

        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=key,
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}")


def _invoke_llm(llm, system: str, user: str) -> str:
    """
    Invoke LLM with system and user prompts using LangChain.

    Args:
        llm: LangChain LLM instance
        system: System prompt defining LLM behavior
        user: User prompt with the task/question

    Returns:
        Raw response content from LLM

    Raises:
        Exception: If LLM API call fails
    """
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
    except ImportError:
        raise ImportError(
            "langchain package is required. "
            "Install it with: pip install langchain"
        )

    # Create messages directly (system and user are already formatted strings)
    # Note: We don't use ChatPromptTemplate.format_messages() because the prompts
    # are already formatted in build_prompt() and contain literal braces in JSON schema

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=user)
    ]

    # Invoke the LLM
    response = llm.invoke(messages)

    # Return the content (works for all providers)
    return response.content


def _get_mock_response() -> str:
    """
    Generate deterministic mock JSON for testing.

    Returns a minimal valid SPIN assessment that conforms to the schema.
    All scores are within valid range [1, 5].
    """
    return """{
  "scores": {
    "situation": 3,
    "problem": 3,
    "implication": 3,
    "need_payoff": 3,
    "flow": 3,
    "tone": 3,
    "engagement": 3
  },
  "coaching": {
    "summary": "Mock assessment for testing purposes.",
    "wins": ["Maintained professional tone", "Asked clarifying questions"],
    "gaps": ["Could explore implications more deeply"],
    "next_actions": ["Practice SPIN framework", "Review recording"]
  }
}"""
