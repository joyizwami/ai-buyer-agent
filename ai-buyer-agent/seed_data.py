#!/usr/bin/env python
"""
Product seeding script for AI Buyer Agent.

Seeds the PostgreSQL database with sample products for demo/testing.
Run this after creating the database schema (schema.sql).
"""

import asyncio
import os
import uuid
from datetime import datetime
from decimal import Decimal

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_buyer_agent")


async def seed_products():
    """Seed the database with sample products."""
    # Convert asyncpg URL format if needed
    if DATABASE_URL.startswith("postgresql+asyncpg://"):
        db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    else:
        db_url = DATABASE_URL

    print(f"Connecting to database...")
    conn = await asyncpg.connect(db_url)
    print("Connected!")

    try:
        # Check existing products
        count = await conn.fetchval("SELECT COUNT(*) FROM products")
        print(f"Existing products: {count}")

        if count > 0:
            print("Products already exist. Skipping seed.")
            return

        # Sample products matching the in-memory catalog
        products = [
            {
                "id": uuid.uuid4(),
                "name": "Wireless Noise-Canceling Headphones",
                "description": "Premium over-ear headphones with active noise cancellation, 30hr battery",
                "category": "electronics",
                "brand": "Sony",
                "price_paise": 2499900,
                "original_price_paise": 2999900,
                "currency": "INR",
                "rating": Decimal("4.5"),
                "review_count": 1250,
                "availability": "in_stock",
                "stock_count": 50,
                "delivery_days_min": 1,
                "delivery_days_max": 3,
                "images": ["https://example.com/headphones.jpg"],
                "tags": ["wireless", "noise-canceling", "bluetooth", "premium"],
                "attributes": {"color": "black", "connectivity": "bluetooth 5.0", "battery_life": "30 hours"},
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "name": "Budget Wireless Earbuds",
                "description": "True wireless earbuds with 20hr battery, IPX4 water resistance",
                "category": "electronics",
                "brand": "Boat",
                "price_paise": 199900,
                "currency": "INR",
                "rating": Decimal("4.2"),
                "review_count": 3400,
                "availability": "in_stock",
                "stock_count": 200,
                "delivery_days_min": 1,
                "delivery_days_max": 2,
                "images": ["https://example.com/earbuds.jpg"],
                "tags": ["wireless", "budget", "earbuds", "ipx4"],
                "attributes": {"color": "white", "connectivity": "bluetooth 5.3", "battery_life": "20 hours"},
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "name": "Smartphone - Mid Range",
                "description": "6.5\" AMOLED, 8GB RAM, 128GB storage, 50MP camera",
                "category": "electronics",
                "brand": "Samsung",
                "price_paise": 2499900,
                "original_price_paise": 2799900,
                "currency": "INR",
                "rating": Decimal("4.3"),
                "review_count": 890,
                "availability": "in_stock",
                "stock_count": 30,
                "delivery_days_min": 1,
                "delivery_days_max": 4,
                "images": ["https://example.com/phone.jpg"],
                "tags": ["smartphone", "android", "camera", "5g"],
                "attributes": {"color": "phantom black", "ram": "8GB", "storage": "128GB", "screen": "6.5 inch AMOLED"},
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "name": "Running Shoes - Lightweight",
                "description": "Breathable mesh upper, responsive cushioning, 250g weight",
                "category": "sports",
                "brand": "Nike",
                "price_paise": 699900,
                "original_price_paise": 899900,
                "currency": "INR",
                "rating": Decimal("4.6"),
                "review_count": 2100,
                "availability": "in_stock",
                "stock_count": 75,
                "delivery_days_min": 1,
                "delivery_days_max": 3,
                "images": ["https://example.com/shoes.jpg"],
                "tags": ["running", "lightweight", "breathable", "cushioned"],
                "attributes": {"color": "white/black", "size": "UK 9", "weight": "250g", "terrain": "road"},
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "name": "Cotton T-Shirt Pack (3-pack)",
                "description": "100% organic cotton, regular fit, pre-shrunk",
                "category": "clothing",
                "brand": "Uniqlo",
                "price_paise": 149900,
                "currency": "INR",
                "rating": Decimal("4.4"),
                "review_count": 5600,
                "availability": "in_stock",
                "stock_count": 500,
                "delivery_days_min": 1,
                "delivery_days_max": 2,
                "images": ["https://example.com/tshirt.jpg"],
                "tags": ["cotton", "basic", "pack", "organic"],
                "attributes": {"colors": ["white", "black", "navy"], "material": "100% organic cotton", "fit": "regular"},
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "name": "Stainless Steel Water Bottle",
                "description": "Double-wall vacuum insulated, keeps cold 24hr / hot 12hr, 500ml",
                "category": "home_kitchen",
                "brand": "Milton",
                "price_paise": 89900,
                "currency": "INR",
                "rating": Decimal("4.7"),
                "review_count": 4200,
                "availability": "in_stock",
                "stock_count": 150,
                "delivery_days_min": 1,
                "delivery_days_max": 2,
                "images": ["https://example.com/bottle.jpg"],
                "tags": ["insulated", "stainless steel", "500ml", "eco-friendly"],
                "attributes": {"color": "matte black", "capacity": "500ml", "material": "304 stainless steel"},
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "name": "Python Programming Book",
                "description": "Complete guide to Python 3.12, from basics to advanced concepts",
                "category": "books",
                "brand": "O'Reilly",
                "price_paise": 129900,
                "currency": "INR",
                "rating": Decimal("4.8"),
                "review_count": 1800,
                "availability": "in_stock",
                "stock_count": 80,
                "delivery_days_min": 2,
                "delivery_days_max": 5,
                "images": ["https://example.com/python-book.jpg"],
                "tags": ["python", "programming", "tutorial", "beginner"],
                "attributes": {"author": "Eric Matthes", "pages": 544, "edition": "3rd", "format": "paperback"},
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "name": "Yoga Mat - Premium",
                "description": "Extra thick 6mm, non-slip surface, alignment markers, carrying strap",
                "category": "sports",
                "brand": "Liforme",
                "price_paise": 399900,
                "currency": "INR",
                "rating": Decimal("4.9"),
                "review_count": 3200,
                "availability": "low_stock",
                "stock_count": 10,
                "delivery_days_min": 2,
                "delivery_days_max": 4,
                "images": ["https://example.com/yoga-mat.jpg"],
                "tags": ["yoga", "non-slip", "thick", "alignment"],
                "attributes": {"color": "purple", "thickness": "6mm", "material": "natural rubber", "dimensions": "183x68cm"},
                "is_active": True,
            },
        ]

        print(f"Inserting {len(products)} products...")
        for p in products:
            await conn.execute("""
                INSERT INTO products (
                    id, name, description, category, brand, price_paise, original_price_paise,
                    currency, rating, review_count, availability, stock_count,
                    delivery_days_min, delivery_days_max, images, tags, attributes,
                    is_active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
            """,
                p["id"], p["name"], p["description"], p["category"], p["brand"],
                p["price_paise"], p.get("original_price_paise"),
                p["currency"], p["rating"], p["review_count"],
                p["availability"], p["stock_count"],
                p["delivery_days_min"], p["delivery_days_max"],
                p["images"], p["tags"], p["attributes"],
                p["is_active"], datetime.utcnow(), datetime.utcnow()
            )
            print(f"  ✅ {p['name']} (₹{p['price_paise']/100:,.0f})")

        # Verify
        final_count = await conn.fetchval("SELECT COUNT(*) FROM products")
        print(f"\n✅ Done! Total products in database: {final_count}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed_products())