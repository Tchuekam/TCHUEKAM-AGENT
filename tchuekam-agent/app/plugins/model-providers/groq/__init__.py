"""Groq provider profile."""

from providers import register_provider
from providers.base import ProviderProfile

groq = ProviderProfile(
    name="groq",
    aliases=("groq-ai", "groqai"),
    display_name="Groq",
    description="Groq — Fast inference provider",
    signup_url="https://console.groq.com/",
    env_vars=("GROQ_API_KEY",),
    base_url="https://api.groq.com/openai/v1",
    auth_type="api_key",
    default_aux_model="llama-3.3-70b-versatile",
    fallback_models=(
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "deepseek-r1-distill-llama-70b",
    ),
)

register_provider(groq)
