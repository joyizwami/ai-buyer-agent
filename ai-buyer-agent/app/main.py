"""
AI Buyer Agent - FastAPI Application

Main entry point for the AI Buyer Agent API.
Handles purchase requests, approvals, and health checks.
"""

import json
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import get_settings, validate_test_mode, get_spending_limits
from app.models.product import Product, ProductSearchParams, ProductSearchResult, ProductCategory, ProductAvailability, ProductSearchFilters
from app.models.transaction import (
    Transaction,
    TransactionStatus,
    ApprovalStatus,
    PurchaseRequest,
    PurchaseResponse,
    ApprovalRequest,
    PaymentVerificationRequest,
    ApprovalResponse,
    TransactionHistoryResponse,
    HealthCheckResponse,
    validate_transition,
)
from app.utils.logger import setup_logging, get_logger, audit_log, RequestContext, audit_logger, get_audit_logger, close_audit_logger
from app.integrations.razorpay_client import get_razorpay_client, close_razorpay_client, RazorpayAPIError
from app.utils.llm_parser import parse_intent
from app.utils.spending_limits import check_spending_limits
from app.integrations.flipkart_catalog import load_flipkart_products
from app.utils.notifications import send_receipt_email
from app.utils.image_search import image_to_product_query

logger = get_logger(__name__)

# In-memory storage for demo (replace with database in production)
transactions_db: dict[str, Transaction] = {}
products_db: list[Product] = []

# Database connection pool
db_pool: Optional[asyncpg.Pool] = None


async def persist_transaction_record(transaction: Transaction) -> None:
    """Persist a transaction into PostgreSQL when database is available."""
    global db_pool
    if not db_pool:
        return

    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO transactions_audit (
                id, user_id, original_query, product_id, product_name,
                product_price_paise, amount_paise, currency, status,
                approval_status, order_id, payment_id, created_at,
                updated_at, completed_at, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            ON CONFLICT (id) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                original_query = EXCLUDED.original_query,
                product_id = EXCLUDED.product_id,
                product_name = EXCLUDED.product_name,
                product_price_paise = EXCLUDED.product_price_paise,
                amount_paise = EXCLUDED.amount_paise,
                currency = EXCLUDED.currency,
                status = EXCLUDED.status,
                approval_status = EXCLUDED.approval_status,
                order_id = EXCLUDED.order_id,
                payment_id = EXCLUDED.payment_id,
                updated_at = EXCLUDED.updated_at,
                completed_at = EXCLUDED.completed_at,
                metadata = EXCLUDED.metadata
            """,
            transaction.id,
            transaction.user_id,
            transaction.original_query,
            transaction.product_id,
            transaction.product_name,
            transaction.product_price_paise,
            transaction.amount_paise,
            transaction.currency,
            transaction.status.value,
            transaction.approval_status.value,
            transaction.razorpay_order.id if transaction.razorpay_order else None,
            transaction.razorpay_payment.id if transaction.razorpay_payment else None,
            transaction.created_at,
            transaction.updated_at,
            transaction.completed_at,
            json.dumps(transaction.metadata or {}),
        )


def load_sample_products() -> list[Product]:
    """Load sample product catalog for demo purposes."""
    from datetime import datetime
    import uuid

    sample_products = [
        Product(
            id=f"prod_{uuid.uuid4().hex[:12]}",
            name="Wireless Noise-Canceling Headphones",
            description="Premium over-ear headphones with active noise cancellation, 30hr battery",
            category=ProductCategory.ELECTRONICS,
            brand="Sony",
            price_paise=2499900,  # ₹24,999
            original_price_paise=2999900,
            rating=4.5,
            review_count=1250,
            availability=ProductAvailability.IN_STOCK,
            stock_count=50,
            delivery_days_min=1,
            delivery_days_max=3,
            images=["https://example.com/headphones.jpg"],
            tags=["wireless", "noise-canceling", "bluetooth", "premium"],
            attributes={"color": "black", "connectivity": "bluetooth 5.0", "battery_life": "30 hours"},
            is_active=True,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        ),
        Product(
            id=f"prod_{uuid.uuid4().hex[:12]}",
            name="Budget Wireless Earbuds",
            description="True wireless earbuds with 20hr battery, IPX4 water resistance",
            category=ProductCategory.ELECTRONICS,
            brand="Boat",
            price_paise=199900,  # ₹1,999
            rating=4.2,
            review_count=3400,
            availability=ProductAvailability.IN_STOCK,
            stock_count=200,
            delivery_days_min=1,
            delivery_days_max=2,
            images=["https://example.com/earbuds.jpg"],
            tags=["wireless", "budget", "earbuds", "ipx4"],
            attributes={"color": "white", "connectivity": "bluetooth 5.3", "battery_life": "20 hours"},
            is_active=True,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        ),
        Product(
            id=f"prod_{uuid.uuid4().hex[:12]}",
            name="Smartphone - Mid Range",
            description="6.5\" AMOLED, 8GB RAM, 128GB storage, 50MP camera",
            category=ProductCategory.ELECTRONICS,
            brand="Samsung",
            price_paise=2499900,  # ₹24,999
            original_price_paise=2799900,
            rating=4.3,
            review_count=890,
            availability=ProductAvailability.IN_STOCK,
            stock_count=30,
            delivery_days_min=1,
            delivery_days_max=4,
            images=["https://example.com/phone.jpg"],
            tags=["smartphone", "android", "camera", "5g"],
            attributes={"color": "phantom black", "ram": "8GB", "storage": "128GB", "screen": "6.5 inch AMOLED"},
            is_active=True,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        ),
        Product(
            id=f"prod_{uuid.uuid4().hex[:12]}",
            name="Running Shoes - Lightweight",
            description="Breathable mesh upper, responsive cushioning, 250g weight",
            category=ProductCategory.SPORTS,
            brand="Nike",
            price_paise=699900,  # ₹6,999
            original_price_paise=899900,
            rating=4.6,
            review_count=2100,
            availability=ProductAvailability.IN_STOCK,
            stock_count=75,
            delivery_days_min=1,
            delivery_days_max=3,
            images=["https://example.com/shoes.jpg"],
            tags=["running", "lightweight", "breathable", "cushioned"],
            attributes={"color": "white/black", "size": "UK 9", "weight": "250g", "terrain": "road"},
            is_active=True,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        ),
        Product(
            id=f"prod_{uuid.uuid4().hex[:12]}",
            name="Cotton T-Shirt Pack (3-pack)",
            description="100% organic cotton, regular fit, pre-shrunk",
            category=ProductCategory.CLOTHING,
            brand="Uniqlo",
            price_paise=149900,  # ₹1,499
            rating=4.4,
            review_count=5600,
            availability=ProductAvailability.IN_STOCK,
            stock_count=500,
            delivery_days_min=1,
            delivery_days_max=2,
            images=["https://example.com/tshirt.jpg"],
            tags=["cotton", "basic", "pack", "organic"],
            attributes={"colors": ["white", "black", "navy"], "material": "100% organic cotton", "fit": "regular"},
            is_active=True,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        ),
        Product(
            id=f"prod_{uuid.uuid4().hex[:12]}",
            name="Stainless Steel Water Bottle",
            description="Double-wall vacuum insulated, keeps cold 24hr / hot 12hr, 500ml",
            category=ProductCategory.HOME_KITCHEN,
            brand="Milton",
            price_paise=89900,  # ₹899
            rating=4.7,
            review_count=4200,
            availability=ProductAvailability.IN_STOCK,
            stock_count=150,
            delivery_days_min=1,
            delivery_days_max=2,
            images=["https://example.com/bottle.jpg"],
            tags=["insulated", "stainless steel", "500ml", "eco-friendly"],
            attributes={"color": "matte black", "capacity": "500ml", "material": "304 stainless steel"},
            is_active=True,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        ),
        Product(
            id=f"prod_{uuid.uuid4().hex[:12]}",
            name="Python Programming Book",
            description="Complete guide to Python 3.12, from basics to advanced concepts",
            category=ProductCategory.BOOKS,
            brand="O'Reilly",
            price_paise=129900,  # ₹1,299
            rating=4.8,
            review_count=1800,
            availability=ProductAvailability.IN_STOCK,
            stock_count=80,
            delivery_days_min=2,
            delivery_days_max=5,
            images=["https://example.com/python-book.jpg"],
            tags=["python", "programming", "tutorial", "beginner"],
            attributes={"author": "Eric Matthes", "pages": 544, "edition": "3rd", "format": "paperback"},
            is_active=True,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        ),
        Product(
            id=f"prod_{uuid.uuid4().hex[:12]}",
            name="Yoga Mat - Premium",
            description="Extra thick 6mm, non-slip surface, alignment markers, carrying strap",
            category=ProductCategory.SPORTS,
            brand="Liforme",
            price_paise=399900,  # ₹3,999
            rating=4.9,
            review_count=3200,
            availability=ProductAvailability.LOW_STOCK,
            stock_count=10,
            delivery_days_min=2,
            delivery_days_max=4,
            images=["https://example.com/yoga-mat.jpg"],
            tags=["yoga", "non-slip", "thick", "alignment"],
            attributes={"color": "purple", "thickness": "6mm", "material": "natural rubber", "dimensions": "183x68cm"},
            is_active=True,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        ),
    ]
    return sample_products


async def load_products_from_db() -> list[Product]:
    """Load active products from PostgreSQL database."""
    global db_pool
    if not db_pool:
        return []

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, name, description, category, brand, price_paise, original_price_paise,
                   currency, rating, review_count, availability, stock_count,
                   delivery_days_min, delivery_days_max, images, tags, attributes,
                   is_active, created_at, updated_at
            FROM products
            WHERE is_active = TRUE
            ORDER BY created_at DESC
        """)

        products = []
        for row in rows:
            products.append(Product(
                id=str(row["id"]),
                name=row["name"],
                description=row["description"],
                category=ProductCategory(row["category"]),
                brand=row["brand"],
                price_paise=row["price_paise"],
                original_price_paise=row["original_price_paise"],
                currency=row["currency"],
                rating=float(row["rating"]),
                review_count=row["review_count"],
                availability=ProductAvailability(row["availability"]),
                stock_count=row["stock_count"],
                delivery_days_min=row["delivery_days_min"],
                delivery_days_max=row["delivery_days_max"],
                images=list(row["images"]) if row["images"] else [],
                tags=list(row["tags"]) if row["tags"] else [],
                attributes=dict(row["attributes"]) if row["attributes"] else {},
                is_active=row["is_active"],
                created_at=row["created_at"].isoformat() if row["created_at"] else None,
                updated_at=row["updated_at"].isoformat() if row["updated_at"] else None,
            ))
        return products


async def seed_products_to_db(products: list[Product]) -> None:
    """Seed products into PostgreSQL database."""
    global db_pool
    if not db_pool:
        return

    async with db_pool.acquire() as conn:
        for product in products:
            await conn.execute("""
                INSERT INTO products (
                    id, name, description, category, brand, price_paise, original_price_paise,
                    currency, rating, review_count, availability, stock_count,
                    delivery_days_min, delivery_days_max, images, tags, attributes,
                    is_active, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                ON CONFLICT (id) DO NOTHING
            """,
                product.id,
                product.name,
                product.description,
                product.category.value,
                product.brand,
                product.price_paise,
                product.original_price_paise,
                product.currency,
                product.rating,
                product.review_count,
                product.availability.value,
                product.stock_count,
                product.delivery_days_min,
                product.delivery_days_max,
                product.images,
                product.tags,
                product.attributes,
                product.is_active,
                product.created_at,
                product.updated_at,
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    settings = get_settings()
    setup_logging(settings.log_level)
    validate_test_mode()  # Enforce test mode

    global products_db, db_pool

    # Try to initialize database connection pool (optional for demo)
    # Convert postgresql+asyncpg:// to postgresql:// for asyncpg
    db_url = settings.database_url
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    try:
        db_pool = await asyncpg.create_pool(
            db_url,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
        # Load products from database
        products_db = await load_products_from_db()
        if not products_db:
            products_db = load_sample_products()
            await seed_products_to_db(products_db)
        logger.info("Database connected, products loaded from PostgreSQL")
    except Exception as e:
        logger.warning(f"Database unavailable, loading Flipkart catalog: {e}")
        db_pool = None
        try:
            products_db = await load_flipkart_products(settings.flipkart_catalog_url)
            logger.info("Application started with Flipkart catalog", extra={"product_count": len(products_db)})
        except Exception as catalog_error:
            logger.warning(f"Flipkart catalog unavailable, using in-memory demo catalog: {catalog_error}")
            products_db = load_sample_products()
            logger.info("Application started with in-memory product catalog")

    # Initialize audit logger (creates connection pool)
    await get_audit_logger()

    logger.info("Application started", extra={"product_count": len(products_db)})

    yield

    # Shutdown
    if db_pool:
        await db_pool.close()
    await close_razorpay_client()
    await close_audit_logger()
    logger.info("Application shutdown")


app = FastAPI(
    title="AI Buyer Agent",
    description="Autonomous purchasing agent with Razorpay integration",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
import os
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the demo frontend."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found", "docs": "/docs"}


# Dependency for request context
async def get_request_context(request: Request) -> RequestContext:
    """Extract request context for logging."""
    request_id = request.headers.get("X-Request-ID", "")
    user_id = request.headers.get("X-User-ID", "")
    return RequestContext(request_id=request_id, user_id=user_id)


# ==================== HEALTH CHECK ====================

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    settings = get_settings()
    checks = {}

    # Check Razorpay connectivity
    try:
        client = await get_razorpay_client()
        checks["razorpay"] = "connected"
    except Exception as e:
        checks["razorpay"] = f"error: {str(e)}"

    # Check database connectivity
    global db_pool
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            checks["database"] = "connected (PostgreSQL)"
        except Exception as e:
            checks["database"] = f"error: {str(e)}"
    else:
        checks["database"] = "in-memory (demo)"

    # Check LLM connectivity (placeholder)
    checks["llm"] = "not configured (demo)"

    overall_status = "healthy" if all(v == "connected" or "demo" in str(v) for v in checks.values()) else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        version=settings.app_version,
        razorpay_connectivity=checks["razorpay"] == "connected",
        database_connectivity=True,
        llm_connectivity=False,
        checks=checks,
    )


# ==================== PRODUCT SEARCH ====================

def search_products(params: ProductSearchParams) -> ProductSearchResult:
    """Search and score products based on query and filters."""
    import time
    from app.models.product import SCORING_WEIGHTS, ScoredProduct

    start_time = time.time()
    query_tokens = {
        token for token in params.query.lower().replace("-", " ").split()
        if len(token) > 2 and token not in {"buy", "want", "under", "best", "find", "show", "get", "with", "for"}
        and not token.isdigit()
    }

    # Filter products
    filtered = []
    for product in products_db:
        if not product.is_active:
            continue

        searchable_text = " ".join([
            product.name,
            product.description,
            product.brand,
            *product.tags,
            *(str(value) for value in product.attributes.values()),
        ]).lower()
        relevance = len([token for token in query_tokens if token in searchable_text]) / max(1, len(query_tokens))
        if query_tokens and relevance == 0:
            continue

        # Category filter
        if params.filters.category and product.category != params.filters.category:
            continue

        # Price filters
        if params.filters.max_price_paise and product.price_paise > params.filters.max_price_paise:
            continue
        if params.filters.min_price_paise and product.price_paise < params.filters.min_price_paise:
            continue

        # Rating filter
        if params.filters.min_rating and product.rating < params.filters.min_rating:
            continue

        # Brand filter
        if params.filters.brand and product.brand.lower() != params.filters.brand.lower():
            continue

        # Tags filter
        if params.filters.tags:
            if not any(tag.lower() in [t.lower() for t in product.tags] for tag in params.filters.tags):
                continue

        # Availability filter
        if params.filters.availability and product.availability != params.filters.availability:
            continue

        # Delivery filter
        if params.filters.max_delivery_days and product.delivery_days_min > params.filters.max_delivery_days:
            continue

        # Stock filter
        if params.filters.in_stock_only and product.availability == ProductAvailability.OUT_OF_STOCK:
            continue

        filtered.append((product, relevance))

    # Score products
    scored_products = []
    for product, relevance in filtered:
        scores = {}
        reasons = []
        scores["text_relevance"] = relevance
        if relevance:
            reasons.append(f"Matches {round(relevance * 100)}% of the request")

        # Price fit (0-1): how well price matches budget
        max_budget = params.user_preferences.get("max_budget_paise", 5000000)
        if product.price_paise <= max_budget:
            price_fit = 1.0 - (product.price_paise / max_budget) * 0.5  # Prefer cheaper within budget
            reasons.append(f"Within budget (₹{product.price_inr:,.0f})")
        else:
            price_fit = 0.0
            reasons.append(f"Over budget (₹{product.price_inr:,.0f})")

        # Rating (0-1)
        scores["rating"] = product.rating / 5.0

        # Availability (0-1)
        availability_scores = {
            ProductAvailability.IN_STOCK: 1.0,
            ProductAvailability.LOW_STOCK: 0.7,
            ProductAvailability.PRE_ORDER: 0.4,
            ProductAvailability.OUT_OF_STOCK: 0.0,
        }
        scores["availability"] = availability_scores.get(product.availability, 0.5)

        # Delivery speed (0-1): faster is better
        avg_delivery = (product.delivery_days_min + product.delivery_days_max) / 2
        scores["delivery_speed"] = max(0.0, 1.0 - (avg_delivery / 10.0))

        # Preference match (0-1): based on user preferences
        pref_match = 0.5  # Default
        if params.user_preferences.get("preferred_brand") == product.brand.lower():
            pref_match = 1.0
            reasons.append(f"Preferred brand: {product.brand}")
        if any(tag in params.user_preferences.get("preferred_tags", []) for tag in product.tags):
            pref_match = min(1.0, pref_match + 0.2)
            reasons.append("Matches preferred features")

        scores["preference_match"] = pref_match

        # Calculate weighted score
        total_score = sum(
            scores.get(k, 0) * v
            for k, v in SCORING_WEIGHTS.items()
        )

        scored_products.append(ScoredProduct(
            product=product,
            score=round(total_score, 3),
            score_breakdown=scores,
            match_reasons=reasons,
        ))

    # Sort by score descending
    scored_products.sort(key=lambda x: x.score, reverse=True)

    # Limit results
    results = scored_products[:params.max_results]

    return ProductSearchResult(
        query=params.query,
        total_found=len(filtered),
        products=results,
        search_time_ms=int((time.time() - start_time) * 1000),
        filters_applied=params.filters,
    )


@app.post("/search", response_model=ProductSearchResult)
async def search_products_endpoint(params: ProductSearchParams):
    """Search products with natural language query and filters."""
    with RequestContext(user_id=params.user_id):
        audit_log(
            stage="product_search",
            action="search_initiated",
            details={"query": params.query, "user_id": params.user_id, "filters": params.filters.model_dump()},
        )
        result = search_products(params)
        audit_log(
            stage="product_search",
            action="search_completed",
            details={"results_found": result.total_found, "returned": len(result.products)},
        )
        return result


@app.post("/search/image", response_model=ProductSearchResult)
async def search_products_by_image(
    image: UploadFile = File(...),
    user_id: str = Form("flipkart_demo_user"),
):
    """Turn a product image into a catalog search using a vision model."""
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image")
    image_bytes = await image.read()
    if len(image_bytes) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 8 MB or smaller")
    try:
        query = await image_to_product_query(image_bytes, image.content_type)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))
    except Exception as error:
        logger.warning(f"Image search failed: {error}")
        provider_response = getattr(error, "response", None)
        provider_status = getattr(provider_response, "status_code", None)
        if provider_status == 429:
            raise HTTPException(status_code=429, detail="OpenAI rejected the vision request because of quota or rate limit. Check project billing and usage.")
        if provider_status in {401, 403}:
            raise HTTPException(status_code=provider_status, detail="OpenAI rejected the vision key. Check that the key is active and has model access.")
        raise HTTPException(status_code=502, detail="Vision search provider failed. Check the AI agent logs for the provider response.")

    return search_products(ProductSearchParams(query=query, user_id=user_id, max_results=5))


# ==================== PURCHASE FLOW ====================

async def process_purchase(request: PurchaseRequest, background_tasks: BackgroundTasks) -> PurchaseResponse:
    """Process a purchase request through the full flow."""
    settings = get_settings()
    limits = get_spending_limits()

    # Create transaction record
    transaction = Transaction(
        user_id=request.user_id,
        original_query=request.query,
        max_budget_paise=request.max_budget or limits["max_transaction"],
    )
    transaction.metadata["receipt_email"] = str(request.receipt_email or settings.receipt_email)

    # Determine budget
    budget_paise = request.max_budget or limits["max_transaction"]
    if budget_paise > limits["max_transaction"]:
        budget_paise = limits["max_transaction"]

    transaction.max_budget_paise = budget_paise

    # Step 1: Parse intent
    transaction.update_status(TransactionStatus.INTENT_PARSED)
    parsed_intent = await parse_intent(request.query, budget_paise)
    transaction.parsed_intent = parsed_intent

    # Step 2: Search products
    transaction.update_status(TransactionStatus.PRODUCTS_FOUND)
    search_params = ProductSearchParams(
        query=request.query,
        filters=ProductSearchFilters(
            category=ProductCategory(parsed_intent["detected_category"]) if parsed_intent["detected_category"] else None,
            max_price_paise=min(parsed_intent["max_price_paise"], budget_paise) if parsed_intent["max_price_paise"] else budget_paise,
            brand=parsed_intent["detected_brand"],
            in_stock_only=True,
        ),
        user_id=request.user_id,
        max_results=10,
        user_preferences=request.preferences,
    )

    search_result = search_products(search_params)

    if not search_result.products:
        transaction.update_status(TransactionStatus.FAILED)
        transaction.error_code = "NO_PRODUCTS_FOUND"
        transaction.error_message = "No products found matching your criteria"
        transactions_db[transaction.id] = transaction
        return PurchaseResponse(
            status="failed",
            transaction_id=transaction.id,
            message="No products found matching your criteria",
            ai_explanation="AI could not find a product that matched the request, budget, and policy constraints.",
            policy_summary={
                "budget_limit_inr": int(budget_paise / 100),
                "checked_filters": [
                    "category",
                    "brand",
                    "price ceiling",
                    "stock availability",
                    "rating threshold"
                ]
            },
        )

    # Step 3: Select best product
    transaction.update_status(TransactionStatus.PRODUCT_SELECTED)
    best_product = search_result.products[0].product
    top_reasons = "; ".join(search_result.products[0].match_reasons[:3]) if search_result.products[0].match_reasons else "best overall fit"
    transaction.product_id = best_product.id
    transaction.product_name = best_product.name
    transaction.product_price_paise = best_product.price_paise
    transaction.product_category = best_product.category.value
    transaction.selection_reasoning = f"Selected based on relevance, rating ({best_product.rating}/5), price (₹{best_product.price_inr:,.0f}), and availability"
    transaction.alternatives_considered = [
        {"id": p.product.id, "name": p.product.name, "price_inr": p.product.price_inr, "score": p.score}
        for p in search_result.products[1:4]
    ]
    transaction.amount_paise = best_product.price_paise
    ai_explanation = (
        f"AI selected {best_product.name} because it best matches the request, has a rating of {best_product.rating}/5, "
        f"is in stock, and fits the budget. Key reasons: {top_reasons}."
    )

    # Step 4: Enforce daily spending limit before creating a payment order
    if db_pool:
        allowed, error_message = await check_spending_limits(db_pool, request.user_id, best_product.price_paise)
        if not allowed:
            transaction.update_status(TransactionStatus.FAILED)
            transaction.error_code = "SPENDING_LIMIT_EXCEEDED"
            transaction.error_message = error_message
            transactions_db[transaction.id] = transaction
            await persist_transaction_record(transaction)
            return PurchaseResponse(
                status="failed",
                transaction_id=transaction.id,
                message=error_message,
                ai_explanation=ai_explanation,
                policy_summary={
                    "budget_limit_inr": int(budget_paise / 100),
                    "daily_limit_inr": int(limits["daily_limit"] / 100),
                    "approval_threshold_inr": int(limits["approval_threshold"] / 100),
                    "reason": "Daily or per-transaction spending policy blocked this action."
                },
            )

    # Step 5: Check if approval required
    approval_threshold = limits["approval_threshold"]
    if request.require_approval and best_product.price_paise > approval_threshold:
        transaction.update_status(TransactionStatus.APPROVAL_REQUIRED)
        transaction.approval_status = ApprovalStatus.PENDING
        transaction.approval_requested_at = transaction.updated_at
        transactions_db[transaction.id] = transaction
        await persist_transaction_record(transaction)

        return PurchaseResponse(
            status="pending_approval",
            transaction_id=transaction.id,
            product={
                "id": best_product.id,
                "name": best_product.name,
                "price_inr": best_product.price_inr,
                "category": best_product.category.value,
                "brand": best_product.brand,
                "rating": best_product.rating,
            },
            message=f"Purchase requires approval (₹{best_product.price_inr:,.0f} > ₹{approval_threshold/100:,.0f} threshold)",
            requires_approval=True,
            approval_url=f"/approve/{transaction.id}",
            ai_explanation=(
                f"AI recommended {best_product.name} based on the strongest match and budget fit, but this purchase exceeds the "
                f"approval threshold. Human approval is required before payment can be created."
            ),
            policy_summary={
                "budget_limit_inr": int(budget_paise / 100),
                "approval_threshold_inr": int(approval_threshold / 100),
                "selected_product": best_product.name,
                "selected_price_inr": int(best_product.price_inr),
                "reason": "The product is valid and within budget, but the purchase amount needs human approval."
            },
            audit_trail_summary=[
                {"stage": "intent_parsed", "status": "matched"},
                {"stage": "product_ranked", "status": "selected"},
                {"stage": "approval_required", "status": "pending"}
            ],
        )

    # Step 5: Create Razorpay order (if auto-approved or below threshold)
    transaction.update_status(TransactionStatus.ORDER_CREATED)

    try:
        client = await get_razorpay_client()
        receipt = f"txn_{transaction.id}"

        order = await client.create_order(
            amount_paise=best_product.price_paise,
            currency="INR",
            receipt=receipt,
            notes={
                "transaction_id": transaction.id,
                "product_id": best_product.id,
                "user_id": request.user_id,
            },
            idempotency_key=f"order_{transaction.id}",
        )

        transaction.razorpay_order = order
        transaction.update_status(TransactionStatus.PAYMENT_INITIATED)

    except RazorpayAPIError as e:
        transaction.update_status(TransactionStatus.FAILED)
        transaction.error_code = e.error_code.value
        transaction.error_message = e.message
        transactions_db[transaction.id] = transaction

        return PurchaseResponse(
            status="failed",
            transaction_id=transaction.id,
            message=f"Failed to create payment order: {e.message}",
        )

    transactions_db[transaction.id] = transaction
    await persist_transaction_record(transaction)

    # For demo: return order details for frontend to complete payment
    # In production, frontend would use Razorpay checkout with this order
    return PurchaseResponse(
        status="payment_initiated",
        transaction_id=transaction.id,
        product={
            "id": best_product.id,
            "name": best_product.name,
            "price_inr": best_product.price_inr,
            "category": best_product.category.value,
            "brand": best_product.brand,
            "rating": best_product.rating,
        },
        payment={
            "order_id": order.id,
            "amount_inr": best_product.price_inr,
            "currency": "INR",
        },
        message="Order created. Complete payment via Razorpay checkout.",
        requires_approval=False,
        ai_explanation=ai_explanation,
        policy_summary={
            "budget_limit_inr": int(budget_paise / 100),
            "approval_threshold_inr": int(approval_threshold / 100),
            "daily_limit_inr": int(limits["daily_limit"] / 100),
            "status": "approved_under_policy"
        },
        audit_trail_summary=[
            {"stage": "intent_parsed", "status": "matched"},
            {"stage": "product_ranked", "status": "selected"},
            {"stage": "policy_check", "status": "passed"},
            {"stage": "payment_order_created", "status": "success"}
        ],
    )


@app.post("/purchase", response_model=PurchaseResponse)
async def create_purchase(request: PurchaseRequest, background_tasks: BackgroundTasks):
    """Initiate a purchase from natural language request."""
    with RequestContext(user_id=request.user_id):
        audit_log(
            stage="purchase",
            action="purchase_initiated",
            details={"user_id": request.user_id, "query": request.query, "max_budget": request.max_budget},
        )

        # Validate budget in paise to match the internal money model.
        limits = get_spending_limits()
        max_txn_paise = limits["max_transaction"]
        if request.max_budget and request.max_budget > max_txn_paise:
            raise HTTPException(
                status_code=400,
                detail=f"Budget exceeds maximum transaction limit of ₹{max_txn_paise / 100:,.0f}",
            )

        response = await process_purchase(request, background_tasks)

        audit_log(
            stage="purchase",
            action="purchase_response",
            details={"transaction_id": response.transaction_id, "status": response.status},
        )

        return response


# ==================== APPROVAL WORKFLOW ====================

@app.post("/approve/{transaction_id}", response_model=ApprovalResponse)
async def approve_transaction(transaction_id: str, approval: ApprovalRequest):
    """Approve or reject a pending transaction."""
    with RequestContext(transaction_id=transaction_id):
        transaction = transactions_db.get(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")

        if transaction.approval_status != ApprovalStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Transaction not pending approval (status: {transaction.approval_status})")

        if approval.approved:
            transaction.approval_status = ApprovalStatus.APPROVED
            transaction.approval_responded_at = transaction.updated_at
            transaction.approved_by = approval.approver_id
            transaction.update_status(TransactionStatus.APPROVED)

            # Create Razorpay order after approval
            try:
                client = await get_razorpay_client()
                order = await client.create_order(
                    amount_paise=transaction.amount_paise,
                    currency="INR",
                    receipt=f"txn_{transaction.id}",
                    notes={
                        "transaction_id": transaction.id,
                        "product_id": transaction.product_id,
                        "user_id": transaction.user_id,
                        "approved_by": approval.approver_id,
                    },
                    idempotency_key=f"order_{transaction.id}",
                )

                transaction.razorpay_order = order
                transaction.update_status(TransactionStatus.ORDER_CREATED)

                message = "Transaction approved. Order created for payment."
                next_steps = "Complete payment via Razorpay checkout using the order_id"

            except RazorpayAPIError as e:
                transaction.update_status(TransactionStatus.FAILED)
                transaction.error_code = e.error_code.value
                transaction.error_message = e.message

                message = f"Approval successful but order creation failed: {e.message}"
                next_steps = "Contact support"

        else:
            transaction.approval_status = ApprovalStatus.REJECTED
            transaction.approval_responded_at = transaction.updated_at
            transaction.approved_by = approval.approver_id
            transaction.update_status(TransactionStatus.REJECTED)
            if approval.reason:
                transaction.metadata["rejection_reason"] = approval.reason

            message = "Transaction rejected by approver"
            next_steps = None

        transactions_db[transaction_id] = transaction

        audit_log(
            stage="approval",
            action="approval_processed",
            details={"approved": approval.approved, "approver_id": approval.approver_id, "reason": approval.reason},
        )

        return ApprovalResponse(
            transaction_id=transaction_id,
            approved=approval.approved,
            status=transaction.status,
            message=message,
            next_steps=next_steps,
        )


@app.get("/approve/{transaction_id}", response_model=ApprovalResponse)
async def get_approval_status(transaction_id: str):
    """Get approval status for a transaction."""
    transaction = transactions_db.get(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return ApprovalResponse(
        transaction_id=transaction_id,
        approved=transaction.approval_status == ApprovalStatus.APPROVED,
        status=transaction.status,
        message=f"Approval status: {transaction.approval_status.value}",
        next_steps=None,
    )


# ==================== PAYMENT CALLBACK ====================

def verify_razorpay_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify Razorpay webhook signature.

    Razorpay sends the signature in the 'X-Razorpay-Signature' header.
    The signature is HMAC-SHA256 of the payload using the webhook secret.

    Args:
        payload: Raw request body as bytes
        signature: Signature from X-Razorpay-Signature header
        secret: Webhook secret from Razorpay Dashboard

    Returns:
        True if signature is valid, False otherwise
    """
    import hmac
    import hashlib

    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


@app.post("/payment/callback")
async def payment_callback(request: Request, background_tasks: BackgroundTasks):
    """Handle Razorpay payment webhook callback with signature verification."""
    settings = get_settings()

    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    webhook_secret = settings.razorpay_webhook_secret or settings.razorpay_key_secret
    if not webhook_secret:
        logger.warning("Razorpay webhook secret is not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    # Verify webhook signature
    if not verify_razorpay_webhook_signature(body, signature, webhook_secret):
        logger.warning("Invalid Razorpay webhook signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("event")
    payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})

    payment_id = payment_data.get("id")
    order_id = payment_data.get("order_id")
    status = payment_data.get("status")

    # Find transaction by order_id
    transaction = None
    for txn in transactions_db.values():
        if txn.razorpay_order and txn.razorpay_order.id == order_id:
            transaction = txn
            break

    if not transaction:
        logger.warning(f"Payment callback for unknown order: {order_id}")
        return {"status": "ignored", "reason": "order not found"}

    with RequestContext(transaction_id=transaction.id):
        if event == "payment.captured" or (event == "payment.authorized" and status == "captured"):
            transaction.update_status(TransactionStatus.PAYMENT_SUCCESS)

            # Fetch payment details from Razorpay
            try:
                client = await get_razorpay_client()
                payment = await client.fetch_payment(payment_id)
                transaction.razorpay_payment = payment
                transaction.payment_method = payment.method
            except Exception as e:
                logger.error(f"Failed to fetch payment details: {e}")

            transaction.update_status(TransactionStatus.COMPLETED)
            transaction.completed_at = transaction.updated_at
            background_tasks.add_task(send_receipt_email, transaction)

            await audit_log(
                stage="payment",
                action="payment_completed",
                details={"payment_id": payment_id, "order_id": order_id, "amount": payment_data.get("amount")},
            )

        elif event == "payment.failed" or status == "failed":
            transaction.update_status(TransactionStatus.PAYMENT_FAILED)
            transaction.error_code = payment_data.get("error_code")
            transaction.error_message = payment_data.get("error_description")

            await audit_log(
                stage="payment",
                action="payment_failed",
                details={"payment_id": payment_id, "order_id": order_id, "error": payment_data.get("error_description")},
                success=False,
                error_message=payment_data.get("error_description"),
            )

    transactions_db[transaction.id] = transaction
    return {"status": "processed"}


@app.get("/payment/key")
async def get_payment_key():
    """Return the public Razorpay test key for Checkout."""
    settings = get_settings()
    if not settings.razorpay_key_id:
        raise HTTPException(status_code=503, detail="Razorpay test key is not configured")
    return {"key_id": settings.razorpay_key_id}


@app.post("/payment/verify")
async def verify_checkout_payment(
    verification: PaymentVerificationRequest,
    background_tasks: BackgroundTasks,
):
    """Verify a browser Checkout response and complete the transaction."""
    import hashlib
    import hmac

    transaction = transactions_db.get(verification.transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if not transaction.razorpay_order or transaction.razorpay_order.id != verification.razorpay_order_id:
        raise HTTPException(status_code=400, detail="Payment order does not match transaction")

    settings = get_settings()
    expected_signature = hmac.new(
        settings.razorpay_key_secret.encode("utf-8"),
        f"{verification.razorpay_order_id}|{verification.razorpay_payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, verification.razorpay_signature):
        raise HTTPException(status_code=401, detail="Invalid payment signature")

    transaction.update_status(TransactionStatus.PAYMENT_SUCCESS)
    transaction.update_status(TransactionStatus.COMPLETED)
    transaction.completed_at = transaction.updated_at
    transaction.metadata["payment_id"] = verification.razorpay_payment_id
    transactions_db[transaction.id] = transaction
    await persist_transaction_record(transaction)
    background_tasks.add_task(send_receipt_email, transaction)
    return {"status": "completed", "transaction_id": transaction.id, "message": "Payment verified successfully"}


# ==================== TRANSACTION HISTORY ====================

@app.get("/transactions/{user_id}", response_model=TransactionHistoryResponse)
async def get_transaction_history(user_id: str, limit: int = 20, offset: int = 0):
    """Get transaction history for a user."""
    user_transactions = [
        txn for txn in transactions_db.values()
        if txn.user_id == user_id
    ]
    user_transactions.sort(key=lambda x: x.created_at, reverse=True)

    paginated = user_transactions[offset:offset + limit]
    total_spent = sum(txn.amount_paise for txn in user_transactions if txn.status == TransactionStatus.COMPLETED)

    return TransactionHistoryResponse(
        user_id=user_id,
        total_transactions=len(user_transactions),
        total_spent_paise=total_spent,
        transactions=paginated,
    )


@app.get("/transactions/detail/{transaction_id}", response_model=Transaction)
async def get_transaction_detail(transaction_id: str):
    """Get full transaction details including audit trail."""
    transaction = transactions_db.get(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


# ==================== SPENDING LIMITS INFO ====================

@app.get("/limits")
async def get_limits():
    """Get current spending limits and configuration."""
    settings = get_settings()
    limits = get_spending_limits()

    return {
        "max_transaction_inr": int(limits["max_transaction"] / 100),
        "daily_spending_limit_inr": int(limits["daily_limit"] / 100),
        "approval_threshold_inr": int(limits["approval_threshold"] / 100),
        "razorpay_test_mode": settings.razorpay_test_mode,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "receipt_email_configured": bool(
            settings.smtp_host
            and settings.smtp_username
            and settings.smtp_password
            and settings.smtp_from_email
        ),
    }


# ==================== ERROR HANDLERS ====================

@app.exception_handler(RazorpayAPIError)
async def razorpay_error_handler(request: Request, exc: RazorpayAPIError):
    return JSONResponse(
        status_code=exc.status_code or 500,
        content={
            "error": exc.error_code.value,
            "message": exc.message,
            "retryable": exc.retryable,
        },
    )


@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
    )


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )