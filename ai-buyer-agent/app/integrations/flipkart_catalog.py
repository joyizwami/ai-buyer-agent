"""Load and normalize products from the companion Flipkart application."""

from datetime import datetime

import httpx

from app.models.product import Product, ProductAvailability, ProductCategory


CATEGORY_MAP = {
    "mobile": ProductCategory.ELECTRONICS,
    "smart": ProductCategory.ELECTRONICS,
    "electronic": ProductCategory.ELECTRONICS,
    "sport": ProductCategory.SPORTS,
    "fitness": ProductCategory.SPORTS,
    "skin": ProductCategory.BEAUTY,
    "hair": ProductCategory.BEAUTY,
    "travel": ProductCategory.HOME_KITCHEN,
    "cover": ProductCategory.ELECTRONICS,
    "headphone": ProductCategory.ELECTRONICS,
}


def _category(short_title: str, name: str) -> ProductCategory:
    text = f"{short_title} {name}".lower()
    for keyword, category in CATEGORY_MAP.items():
        if keyword in text:
            return category
    return ProductCategory.HOME_KITCHEN


def _brand(name: str) -> str:
    known_brands = ("Apple", "Samsung", "Redmi", "Realme", "OnePlus", "Vivo", "POCO", "Infinix", "Motorola", "Sony", "Spigen", "Nivea", "Molife", "Safari", "Skybags")
    return next((brand for brand in known_brands if brand.lower() in name.lower()), "Flipkart")


def normalize_product(item: dict) -> Product:
    title = item.get("title") or {}
    price = item.get("price") or {}
    name = title.get("longTitle") or title.get("shortTitle") or "Flipkart product"
    quantity = max(0, int(item.get("quantity") or 0))
    now = datetime.utcnow().isoformat()
    return Product(
        id=str(item.get("id")),
        name=name,
        description=item.get("description") or "",
        category=_category(title.get("shortTitle", ""), name),
        brand=_brand(name),
        price_paise=max(0, int(price.get("cost") or 0) * 100),
        original_price_paise=max(0, int(price.get("mrp") or 0) * 100) or None,
        rating=4.0,
        review_count=0,
        availability=ProductAvailability.IN_STOCK if quantity else ProductAvailability.OUT_OF_STOCK,
        stock_count=quantity,
        delivery_days_min=1,
        delivery_days_max=7,
        images=[url for url in (item.get("url"), item.get("detailUrl")) if url],
        tags=[title.get("shortTitle", ""), item.get("discount", ""), item.get("tagline", "")],
        attributes={"flipkart_id": str(item.get("id"))},
        is_active=True,
        created_at=now,
        updated_at=now,
    )


async def load_flipkart_products(url: str, timeout: float = 5.0) -> list[Product]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("Flipkart catalog response must be an array")
    return [normalize_product(item) for item in payload if item.get("id")]