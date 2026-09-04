"""Vision-assisted product query extraction."""

import base64
import json

import httpx

from app.config import get_settings


async def image_to_product_query(image_bytes: bytes, content_type: str) -> str:
    """Describe a product image using an OpenAI-compatible vision model."""
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("Image search requires OPENAI_API_KEY with a vision-capable model")

    encoded = base64.b64encode(image_bytes).decode("ascii")
    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        response = await client.post(
            f"{settings.openai_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.llm_model,
                "temperature": 0,
                "max_tokens": 120,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Identify this product for catalog search. Return only JSON: {\"query\": \"brand, product type, distinctive features\"}. Do not claim an exact model unless visible."},
                        {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{encoded}"}},
                    ],
                }],
            },
        )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content)
    parsed = json.loads(content)
    query = parsed.get("query", "").strip()
    if not query:
        raise RuntimeError("Vision model did not return a searchable product description")
    return query