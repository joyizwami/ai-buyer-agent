"""
LLM-powered intent parsing for AI Buyer Agent.

Supports both OpenAI and Anthropic providers for parsing natural language
purchase queries into structured intent data.
"""

import json
import re
from typing import Optional
from dataclasses import dataclass

from app.config import get_settings
from app.models.product import ProductCategory


@dataclass
class ParsedIntent:
    """Structured intent parsed from natural language query."""
    intent_type: str  # "purchase" or "search"
    detected_category: Optional[str] = None
    detected_brand: Optional[str] = None
    max_price_paise: Optional[int] = None
    original_query: str = ""
    keywords: list = None
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "intent_type": self.intent_type,
            "detected_category": self.detected_category,
            "detected_brand": self.detected_brand,
            "max_price_paise": self.max_price_paise,
            "original_query": self.original_query,
            "keywords": self.keywords or [],
            "confidence": self.confidence,
        }


async def parse_intent_llm(query: str, max_budget_paise: int) -> ParsedIntent:
    """
    Parse user intent using LLM (OpenAI, Nvidia, Anthropic, or Ollama).

    Args:
        query: Natural language query from user
        max_budget_paise: Maximum budget in paise from config

    Returns:
        ParsedIntent with extracted structured data
    """
    settings = get_settings()
    provider = settings.llm_provider.lower()

    # Build the prompt
    categories = [c.value for c in ProductCategory]
    categories_str = ", ".join(categories)

    prompt = f"""Parse the following shopping query into structured JSON.

Query: "{query}"

Available categories: {categories_str}
Default max budget: {max_budget_paise // 100} INR

Extract and return ONLY valid JSON with these fields:
{{
  "intent_type": "purchase" or "search",
  "detected_category": "category from list or null",
  "detected_brand": "brand name or null",
  "max_price_paise": integer paise or null,
  "keywords": ["relevant", "keywords"],
  "confidence": 0.0-1.0
}}

Rules:
- intent_type: "purchase" if user wants to buy/order/get; "search" if browse/find/show
- detected_category: match to available categories only
- max_price_paise: extract price mentions (e.g., "under 5000" = 500000 paise)
- keywords: extract 3-5 key descriptive terms
- confidence: how confident you are in the parsing (0.0-1.0)
"""

    try:
        if provider == "openai":
            return await _parse_with_openai(prompt, query, max_budget_paise)
        elif provider == "nvidia":
            return await _parse_with_nvidia(prompt, query, max_budget_paise)
        elif provider == "anthropic":
            return await _parse_with_anthropic(prompt, query, max_budget_paise)
        elif provider == "ollama":
            return await _parse_with_ollama(prompt, query, max_budget_paise)
        else:
            return await _parse_fallback(query, max_budget_paise)
    except Exception as e:
        # Log error and fall back to keyword matching
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.warning(f"LLM parsing failed, using fallback: {e}")
        return await _parse_fallback(query, max_budget_paise)


async def _parse_with_openai(prompt: str, query: str, max_budget_paise: int) -> ParsedIntent:
    """Parse using OpenAI API."""
    import httpx

    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key not configured")

    base_url = settings.openai_base_url.rstrip('/')
    endpoint = f"{base_url}/chat/completions"

    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        response = await client.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": "You are a shopping intent parser. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": settings.llm_temperature,
                "max_tokens": 300,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

    parsed = json.loads(content)
    return ParsedIntent(
        intent_type=parsed.get("intent_type", "purchase"),
        detected_category=parsed.get("detected_category"),
        detected_brand=parsed.get("detected_brand"),
        max_price_paise=parsed.get("max_price_paise"),
        original_query=query,
        keywords=parsed.get("keywords", []),
        confidence=parsed.get("confidence", 0.8),
    )


async def _parse_with_nvidia(prompt: str, query: str, max_budget_paise: int) -> ParsedIntent:
    """Parse using Nvidia API (OpenAI-compatible)."""
    import httpx

    settings = get_settings()
    if not settings.nvidia_api_key:
        raise ValueError("Nvidia API key not configured")

    base_url = settings.nvidia_base_url.rstrip('/')
    endpoint = f"{base_url}/chat/completions"

    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        response = await client.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {settings.nvidia_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": "You are a shopping intent parser. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": settings.llm_temperature,
                "max_tokens": 300,
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

    parsed = json.loads(content)
    return ParsedIntent(
        intent_type=parsed.get("intent_type", "purchase"),
        detected_category=parsed.get("detected_category"),
        detected_brand=parsed.get("detected_brand"),
        max_price_paise=parsed.get("max_price_paise"),
        original_query=query,
        keywords=parsed.get("keywords", []),
        confidence=parsed.get("confidence", 0.8),
    )


async def _parse_with_anthropic(prompt: str, query: str, max_budget_paise: int) -> ParsedIntent:
    """Parse using Anthropic API."""
    import httpx

    settings = get_settings()
    if not settings.anthropic_api_key:
        raise ValueError("Anthropic API key not configured")

    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": settings.llm_model,
                "max_tokens": 300,
                "temperature": settings.llm_temperature,
                "messages": [
                    {"role": "user", "content": prompt},
                ],
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["content"][0]["text"]

    parsed = json.loads(content)
    return ParsedIntent(
        intent_type=parsed.get("intent_type", "purchase"),
        detected_category=parsed.get("detected_category"),
        detected_brand=parsed.get("detected_brand"),
        max_price_paise=parsed.get("max_price_paise"),
        original_query=query,
        keywords=parsed.get("keywords", []),
        confidence=parsed.get("confidence", 0.8),
    )


async def _parse_with_ollama(prompt: str, query: str, max_budget_paise: int) -> ParsedIntent:
    """Parse using Ollama API (self-hosted, OpenAI-compatible)."""
    import httpx

    settings = get_settings()
    base_url = settings.ollama_base_url.rstrip('/')
    endpoint = f"{base_url}/v1/chat/completions"
    model = settings.ollama_model

    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        response = await client.post(
            endpoint,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a shopping intent parser. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": settings.llm_temperature,
                "max_tokens": 300,
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

    parsed = json.loads(content)
    return ParsedIntent(
        intent_type=parsed.get("intent_type", "purchase"),
        detected_category=parsed.get("detected_category"),
        detected_brand=parsed.get("detected_brand"),
        max_price_paise=parsed.get("max_price_paise"),
        original_query=query,
        keywords=parsed.get("keywords", []),
        confidence=parsed.get("confidence", 0.8),
    )


async def _parse_fallback(query: str, max_budget_paise: int) -> ParsedIntent:
    """Fallback keyword-based parsing when LLM is not available."""
    query_lower = query.lower()

    # Category keywords mapping
    category_keywords = {
        ProductCategory.ELECTRONICS: [
            "headphone", "earbud", "phone", "laptop", "tablet", "charger", "cable",
            "speaker", "watch", "camera", "monitor", "keyboard", "mouse", "tv", "television"
        ],
        ProductCategory.CLOTHING: [
            "shirt", "pant", "dress", "shoe", "sneaker", "jacket", "tshirt", "t-shirt",
            "jeans", "hoodie", "sweater", "shorts", "sock"
        ],
        ProductCategory.HOME_KITCHEN: [
            "bottle", "mug", "pan", "pot", "knife", "blender", "cooker", "utensil",
            "plate", "bowl", "spoon", "fork", "cup", "glass"
        ],
        ProductCategory.BOOKS: [
            "book", "novel", "guide", "textbook", "manual", "ebook", "kindle"
        ],
        ProductCategory.SPORTS: [
            "shoe", "running", "yoga", "mat", "dumbbell", "fitness", "gym", "ball",
            "racket", "bat", "helmet", "glove"
        ],
        ProductCategory.BEAUTY: [
            "cream", "serum", "shampoo", "soap", "lotion", "perfume", "makeup",
            "lipstick", "foundation", "moisturizer"
        ],
        ProductCategory.TOYS: [
            "toy", "game", "puzzle", "lego", "doll", "action figure", "board game"
        ],
        ProductCategory.HEALTH: [
            "vitamin", "supplement", "medicine", "bandage", "thermometer", "mask"
        ],
        ProductCategory.GROCERY: [
            "rice", "dal", "oil", "spice", "snack", "drink", "water", "milk", "bread"
        ],
        ProductCategory.AUTOMOTIVE: [
            "tire", "oil", "battery", "charger", "cover", "filter", "wiper"
        ],
    }

    detected_category = None
    for cat, keywords in category_keywords.items():
        if any(kw in query_lower for kw in keywords):
            detected_category = cat.value
            break

    # Extract price hints
    price_matches = re.findall(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:rs|inr|rupees?|\$|k)', query_lower)
    max_price_paise = None
    if price_matches:
        try:
            price_str = price_matches[0].replace(',', '')
            price_val = float(price_str)
            # Handle 'k' suffix (e.g., "5k" = 5000)
            if 'k' in price_matches[0].lower():
                price_val *= 1000
            max_price_paise = int(price_val * 100)
        except (ValueError, IndexError):
            pass

    # Extract brand hints
    known_brands = [
        "sony", "samsung", "apple", "nike", "adidas", "boat", "unilqo", "milton",
        "oreilly", "liforme", "unilqo", "hp", "dell", "lenovo", "asus", "msi",
        "lg", "philips", "bose", "jbl", "skullcandy", "oneplus", "xiaomi", "realme",
        "puma", "reebok", "under armour", "new balance", "asics", "mizuno",
        "levis", "zara", "h&m", "uniqlo", "gap", "old navy"
    ]
    detected_brand = None
    for brand in known_brands:
        if brand in query_lower:
            detected_brand = brand.capitalize()
            break

    # Determine intent type
    if any(word in query_lower for word in ["buy", "purchase", "order", "get", "need", "want", "grab"]):
        intent_type = "purchase"
    elif any(word in query_lower for word in ["search", "find", "show", "look", "browse", "explore"]):
        intent_type = "search"
    else:
        intent_type = "purchase"

    # Extract keywords
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "under", "over", "below", "above", "my", "i", "me", "please"}
    keywords = [w for w in query_lower.split() if len(w) > 3 and w not in stopwords][:5]

    return ParsedIntent(
        intent_type=intent_type,
        detected_category=detected_category,
        detected_brand=detected_brand,
        max_price_paise=max_price_paise or max_budget_paise,
        original_query=query,
        keywords=keywords,
        confidence=0.5,  # Lower confidence for fallback
    )


# Convenience function that matches the old interface
async def parse_intent(query: str, max_budget_paise: int) -> dict:
    """
    Parse user intent from natural language query.

    This function tries LLM parsing first, falls back to keyword matching.
    """
    parsed = await parse_intent_llm(query, max_budget_paise)
    return parsed.to_dict()