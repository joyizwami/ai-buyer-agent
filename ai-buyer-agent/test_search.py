import sys
sys.path.insert(0, '.')
from app.main import search_products
from app.models.product import ProductSearchParams, ProductSearchFilters

params = ProductSearchParams(
    query='wireless headphones',
    user_id='test_user_1',
    max_results=5,
    filters=ProductSearchFilters(max_price_paise=3000000, in_stock_only=True)
)

result = search_products(params)
print(f'Found {result.total_found} products')
for p in result.products:
    print(f'  - {p.product.name}: {p.product.price_inr} (score: {p.score})')