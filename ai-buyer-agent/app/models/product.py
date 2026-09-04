"""
Product models for the AI Buyer Agent.

Defines the product catalog structure, search parameters, and scoring models.
All models use Pydantic for validation and serialization.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal


class ProductCategory(str, Enum):
    """Supported product categories."""

    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    HOME_KITCHEN = "home_kitchen"
    BOOKS = "books"
    SPORTS = "sports"
    BEAUTY = "beauty"
    TOYS = "toys"
    AUTOMOTIVE = "automotive"
    HEALTH = "health"
    GROCERY = "grocery"


class ProductAvailability(str, Enum):
    """Product availability status."""

    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    PRE_ORDER = "pre_order"


class Product(BaseModel):
    """
    Core product model representing an item in the catalog.

    All monetary values are stored in paise (1/100 INR) for precision.
    """

    id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    category: ProductCategory = Field(..., description="Product category")
    brand: str = Field(..., description="Brand name")
    price_paise: int = Field(..., ge=0, description="Price in paise (1/100 INR)")
    original_price_paise: Optional[int] = Field(
        default=None, ge=0, description="Original price before discount in paise"
    )
    currency: str = Field(default="INR", description="Currency code")
    rating: float = Field(..., ge=0.0, le=5.0, description="Average rating (0-5)")
    review_count: int = Field(default=0, ge=0, description="Number of reviews")
    availability: ProductAvailability = Field(
        default=ProductAvailability.IN_STOCK, description="Stock status"
    )
    stock_count: int = Field(default=0, ge=0, description="Available stock quantity")
    delivery_days_min: int = Field(default=1, ge=0, description="Minimum delivery days")
    delivery_days_max: int = Field(default=7, ge=0, description="Maximum delivery days")
    images: List[str] = Field(default_factory=list, description="Product image URLs")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Category-specific attributes (color, size, etc.)"
    )
    is_active: bool = Field(default=True, description="Whether product is active")
    created_at: str = Field(..., description="ISO format creation timestamp")
    updated_at: str = Field(..., description="ISO format last update timestamp")

    @property
    def price_inr(self) -> float:
        """Get price in INR (for display)."""
        return self.price_paise / 100.0

    @property
    def discount_percentage(self) -> Optional[float]:
        """Calculate discount percentage if original price exists."""
        if self.original_price_paise and self.original_price_paise > self.price_paise:
            return round(
                (1 - self.price_paise / self.original_price_paise) * 100, 2
            )
        return None

    @property
    def is_affordable(self, max_budget_paise: int) -> bool:
        """Check if product fits within budget."""
        return self.price_paise <= max_budget_paise

    @field_validator("delivery_days_max")
    @classmethod
    def validate_delivery_days(cls, v: int, info) -> int:
        """Ensure max delivery days >= min delivery days."""
        if "delivery_days_min" in info.data and v < info.data["delivery_days_min"]:
            raise ValueError("delivery_days_max must be >= delivery_days_min")
        return v


class ProductSearchFilters(BaseModel):
    """Filters for product search."""

    category: Optional[ProductCategory] = None
    max_price_paise: Optional[int] = Field(default=None, ge=0)
    min_price_paise: Optional[int] = Field(default=None, ge=0)
    min_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    brand: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    availability: Optional[ProductAvailability] = None
    max_delivery_days: Optional[int] = Field(default=None, ge=0)
    in_stock_only: bool = Field(default=True)


class ProductSearchParams(BaseModel):
    """Parameters for product search request."""

    query: str = Field(..., description="Natural language search query")
    filters: ProductSearchFilters = Field(default_factory=ProductSearchFilters)
    user_id: str = Field(..., description="User ID for personalization")
    max_results: int = Field(default=10, ge=1, le=50)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)


class ScoredProduct(BaseModel):
    """Product with scoring details for ranking."""

    product: Product
    score: float = Field(..., ge=0.0, le=1.0, description="Overall score (0-1)")
    score_breakdown: Dict[str, float] = Field(
        default_factory=dict, description="Individual score components"
    )
    match_reasons: List[str] = Field(
        default_factory=list, description="Human-readable reasons for selection"
    )


class ProductSearchResult(BaseModel):
    """Result of a product search with ranked products."""

    query: str
    total_found: int
    products: List[ScoredProduct] = Field(default_factory=list)
    search_time_ms: int
    filters_applied: ProductSearchFilters

    def get_top_n(self, n: int = 3) -> List[ScoredProduct]:
        """Get top N scored products."""
        return self.products[:n]


class ProductRecommendation(BaseModel):
    """Structured recommendation with justification."""

    product: Product
    rank: int
    score: float
    justification: str
    pros: List[str]
    cons: List[str]
    alternative_products: List[Product] = Field(default_factory=list)


# Scoring weights - must sum to 1.0
SCORING_WEIGHTS = {
    "text_relevance": 0.35,
    "price_fit": 0.20,
    "rating": 0.18,
    "availability": 0.12,
    "delivery_speed": 0.08,
    "preference_match": 0.07,
}


def validate_scoring_weights() -> None:
    """Validate that scoring weights sum to 1.0."""
    total = sum(SCORING_WEIGHTS.values())
    if abs(total - 1.0) > 0.001:
        raise ValueError(f"Scoring weights must sum to 1.0, got {total}")