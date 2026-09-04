"""
Configuration module for AI Buyer Agent.

Centralizes all environment variables, spending limits, and Razorpay configuration.
All secrets MUST come from environment variables - never hardcode.
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI Buyer Agent"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # Razorpay Configuration (TEST MODE ONLY)
    razorpay_key_id: str = Field(
        default="",
        description="Razorpay Key ID from Dashboard (test mode)",
        validation_alias="RAZORPAY_KEY_ID"
    )
    razorpay_key_secret: str = Field(
        default="",
        description="Razorpay Key Secret from Dashboard (test mode)",
        validation_alias="RAZORPAY_KEY_SECRET"
    )
    razorpay_webhook_secret: str = Field(
        default="",
        description="Razorpay webhook secret used to validate payment callbacks",
        validation_alias="RAZORPAY_WEBHOOK_SECRET"
    )
    razorpay_test_mode: bool = Field(
        default=True,
        description="Enforce test mode - MUST be True for buildathon",
        validation_alias="RAZORPAY_TEST_MODE"
    )
    razorpay_base_url: str = Field(
        default="https://api.razorpay.com/v1",
        description="Razorpay API base URL"
    )

    # Email receipts (optional SMTP configuration)
    smtp_host: str = Field(default="", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_username: str = Field(default="", validation_alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", validation_alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="", validation_alias="SMTP_FROM_EMAIL")
    smtp_use_tls: bool = Field(default=True, validation_alias="SMTP_USE_TLS")
    receipt_email: str = Field(default="janmayswami@gmail.com", validation_alias="RECEIPT_EMAIL")

    # LLM Configuration (OpenAI, Anthropic, Nvidia, or Ollama)
    llm_provider: str = Field(
        default="nvidia",
        description="LLM provider: 'openai', 'anthropic', 'nvidia', or 'ollama'",
        validation_alias="LLM_PROVIDER"
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API Key",
        validation_alias="OPENAI_API_KEY"
    )
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI-compatible base URL for providers like KiraAI",
        validation_alias="OPENAI_BASE_URL"
    )
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API Key",
        validation_alias="ANTHROPIC_API_KEY"
    )
    nvidia_api_key: str = Field(
        default="",
        description="Nvidia API Key (free tier from build.nvidia.com)",
        validation_alias="NVIDIA_API_KEY"
    )
    nvidia_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        description="Nvidia API base URL",
        validation_alias="NVIDIA_BASE_URL"
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL (self-hosted)",
        validation_alias="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(
        default="llama2",
        description="Ollama model name",
        validation_alias="OLLAMA_MODEL"
    )
    llm_model: str = Field(
        default="meta-llama-3.1-8b-instruct",
        description="LLM model to use for intent parsing",
        validation_alias="LLM_MODEL"
    )
    llm_temperature: float = Field(
        default=0.1,
        description="LLM temperature for consistent parsing",
        validation_alias="LLM_TEMPERATURE"
    )

    # Spending Limits (CRITICAL for Razorpay compliance)
    max_transaction_amount: int = Field(
        default=25000,
        description="Maximum amount per transaction in INR",
        validation_alias="MAX_TRANSACTION_AMOUNT"
    )
    daily_spending_limit: int = Field(
        default=100000,
        description="Daily spending limit per user in INR",
        validation_alias="DAILY_SPENDING_LIMIT"
    )
    approval_threshold: int = Field(
        default=1000,
        description="Amount above which human approval is required in INR",
        validation_alias="APPROVAL_THRESHOLD"
    )

    @field_validator("max_transaction_amount", "daily_spending_limit", "approval_threshold", mode="before")
    @classmethod
    def convert_inr_to_paise(cls, v: int) -> int:
        """Convert INR to paise (multiply by 100)."""
        if v is None:
            return 0
        return int(v) * 100

    # Retry Configuration
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for external API calls",
        validation_alias="MAX_RETRIES"
    )
    retry_base_delay: float = Field(
        default=1.0,
        description="Base delay for exponential backoff in seconds",
        validation_alias="RETRY_BASE_DELAY"
    )
    request_timeout: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
        validation_alias="REQUEST_TIMEOUT"
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ai_buyer_agent",
        description="PostgreSQL database URL (asyncpg driver)",
        validation_alias="DATABASE_URL"
    )

    # Product Catalog
    catalog_path: str = Field(
        default="./data/products.json",
        description="Path to product catalog JSON file",
        validation_alias="CATALOG_PATH"
    )
    flipkart_catalog_url: str = Field(
        default="http://localhost:8000/products",
        validation_alias="FLIPKART_CATALOG_URL",
    )

    # Frontend
    frontend_enabled: bool = Field(
        default=True,
        description="Serve frontend demo at /",
        validation_alias="FRONTEND_ENABLED"
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Load the project .env file with override=True so the app always honors
    the repository's configuration instead of stale shell environment values.
    """
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    return Settings()


# Convenience function for common limit checks
def get_spending_limits() -> dict:
    """Return spending limits as a dictionary for easy access."""
    settings = get_settings()
    return {
        "max_transaction": settings.max_transaction_amount,
        "daily_limit": settings.daily_spending_limit,
        "approval_threshold": settings.approval_threshold,
    }


# Razorpay test card numbers for reference
RAZORPAY_TEST_CARDS = {
    "success": "5267318187975449",  # Always succeeds
    "decline": "4000000000000002",   # Always declines
    "insufficient_funds": "5105105105105100",  # Simulates insufficient funds
    "expired": "4000000000000069",    # Expired card
    "processing_error": "4000000000000119",  # Processing error
}


def validate_test_mode() -> None:
    """
    Validate that we're running in test mode.

    Raises:
        ValueError: If not in test mode (production safety)
    """
    settings = get_settings()
    if not settings.razorpay_test_mode:
        raise ValueError(
            "CRITICAL: Razorpay test mode is disabled. "
            "This agent MUST run in test mode only for the buildathon. "
            "Set RAZORPAY_TEST_MODE=true in your environment."
        )
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise ValueError(
            "Razorpay credentials not configured. "
            "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env file."
        )