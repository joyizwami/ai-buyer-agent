-- AI Buyer Agent PostgreSQL Schema
-- Run this against your PostgreSQL database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== PRODUCTS TABLE ====================
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    price_paise BIGINT NOT NULL CHECK (price_paise >= 0),
    original_price_paise BIGINT CHECK (original_price_paise >= 0),
    currency CHAR(3) DEFAULT 'INR',
    rating DECIMAL(3,2) NOT NULL DEFAULT 0.0 CHECK (rating >= 0 AND rating <= 5),
    review_count INTEGER NOT NULL DEFAULT 0 CHECK (review_count >= 0),
    availability VARCHAR(20) NOT NULL DEFAULT 'in_stock',
    stock_count INTEGER NOT NULL DEFAULT 0 CHECK (stock_count >= 0),
    delivery_days_min INTEGER NOT NULL DEFAULT 1 CHECK (delivery_days_min >= 0),
    delivery_days_max INTEGER NOT NULL DEFAULT 7 CHECK (delivery_days_max >= 0),
    images JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    attributes JSONB DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions_audit (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    original_query TEXT NOT NULL,
    product_id TEXT,
    product_name TEXT,
    product_price_paise BIGINT DEFAULT 0,
    amount_paise BIGINT NOT NULL DEFAULT 0,
    currency TEXT DEFAULT 'INR',
    status TEXT NOT NULL DEFAULT 'pending',
    approval_status TEXT NOT NULL DEFAULT 'pending',
    order_id TEXT,
    payment_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_price ON products(price_paise);
CREATE INDEX idx_products_availability ON products(availability);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_products_tags ON products USING GIN(tags);
CREATE INDEX idx_products_search ON products USING GIN(
    to_tsvector('english', name || ' ' || description || ' ' || brand || ' ' || array_to_string(tags, ' '))
);

-- ==================== TRANSACTIONS TABLE ====================
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL,
    original_query TEXT NOT NULL,
    parsed_intent JSONB DEFAULT '{}',
    max_budget_paise BIGINT NOT NULL CHECK (max_budget_paise >= 0),
    product_id UUID REFERENCES products(id),
    product_name VARCHAR(255),
    product_price_paise BIGINT CHECK (product_price_paise >= 0),
    product_category VARCHAR(50),
    selection_reasoning TEXT,
    alternatives_considered JSONB DEFAULT '[]',
    razorpay_order_id VARCHAR(100),
    razorpay_payment_id VARCHAR(100),
    payment_method VARCHAR(20),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    approval_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    approval_requested_at TIMESTAMPTZ,
    approval_responded_at TIMESTAMPTZ,
    approved_by VARCHAR(100),
    amount_paise BIGINT NOT NULL DEFAULT 0 CHECK (amount_paise >= 0),
    currency CHAR(3) DEFAULT 'INR',
    error_code VARCHAR(50),
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_razorpay_order ON transactions(razorpay_order_id);
CREATE INDEX idx_transactions_razorpay_payment ON transactions(razorpay_payment_id);

-- ==================== AUDIT LOG TABLE ====================
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_id UUID,
    user_id VARCHAR(100),
    transaction_id UUID REFERENCES transactions(id),
    stage VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB DEFAULT '{}',
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT,
    duration_ms INTEGER
);

CREATE INDEX idx_audit_transaction ON audit_log(transaction_id);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_stage_action ON audit_log(stage, action);

-- ==================== DAILY SPENDING VIEW ====================
CREATE VIEW daily_user_spending AS
SELECT
    user_id,
    DATE(created_at AT TIME ZONE 'UTC') as spend_date,
    SUM(amount_paise) as total_spent_paise,
    COUNT(*) as transaction_count
FROM transactions
WHERE status = 'completed'
GROUP BY user_id, DATE(created_at AT TIME ZONE 'UTC');

-- ==================== TRIGGER FOR UPDATED_AT ====================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();