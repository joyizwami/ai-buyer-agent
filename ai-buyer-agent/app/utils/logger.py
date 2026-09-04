"""
Structured logging and audit trail utilities for AI Buyer Agent.

Provides JSON-structured logging for observability and compliance.
All audit entries are written to both console (JSON) and PostgreSQL database.
Uses asyncpg for async database operations.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
import asyncpg
from asyncpg import Pool

from app.config import get_settings


# Context variable for request-scoped logging
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
transaction_id_var: ContextVar[Optional[str]] = ContextVar("transaction_id", default=None)


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Outputs logs as JSON lines for easy parsing by log aggregators.
    Includes request context automatically.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        transaction_id = transaction_id_var.get()
        if transaction_id:
            log_data["transaction_id"] = transaction_id

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "name", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info", "getMessage"
            }:
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class AsyncAuditLogger:
    """
    Dedicated async audit logger for transaction compliance.

    Writes immutable audit entries to PostgreSQL for regulatory compliance.
    Also outputs to structured JSON logs.
    """

    def __init__(self, database_url: str = None):
        url = database_url or get_settings().database_url
        # Convert postgresql+asyncpg:// to postgresql:// for asyncpg
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://")
        self.database_url = url
        self._pool: Optional[Pool] = None

    async def initialize(self) -> None:
        """Initialize the connection pool."""
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=30,
                )
                # Ensure audit_log table exists
                await self._ensure_table()
            except Exception as e:
                # Log warning but don't fail - audit logger can work without DB
                import logging
                logging.getLogger(__name__).warning(f"Audit logger DB unavailable, using JSON only: {e}")
                self._pool = None

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def _ensure_table(self) -> None:
        """Ensure PostgreSQL tables exist for audit and transaction persistence."""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    brand TEXT,
                    price_paise BIGINT NOT NULL DEFAULT 0,
                    original_price_paise BIGINT DEFAULT 0,
                    currency TEXT DEFAULT 'INR',
                    rating DOUBLE PRECISION DEFAULT 0,
                    review_count INTEGER DEFAULT 0,
                    availability TEXT DEFAULT 'in_stock',
                    stock_count INTEGER DEFAULT 0,
                    delivery_days_min INTEGER DEFAULT 1,
                    delivery_days_max INTEGER DEFAULT 3,
                    images JSONB DEFAULT '[]',
                    tags JSONB DEFAULT '[]',
                    attributes JSONB DEFAULT '{}',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            await conn.execute("""
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
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id BIGSERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    request_id UUID,
                    user_id VARCHAR(100),
                    transaction_id UUID,
                    stage VARCHAR(100) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    details JSONB DEFAULT '{}',
                    success BOOLEAN NOT NULL DEFAULT TRUE,
                    error_message TEXT,
                    duration_ms INTEGER
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_transaction
                ON audit_log(transaction_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_user
                ON audit_log(user_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_log(timestamp)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_audit_user_created
                ON transactions_audit(user_id, created_at)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_audit_status
                ON transactions_audit(status)
            """)

    async def log_audit(
        self,
        stage: str,
        action: str,
        details: Dict[str, Any] = None,
        success: bool = True,
        error_message: str = None,
        duration_ms: int = None,
        request_id: str = None,
        user_id: str = None,
        transaction_id: str = None,
    ) -> None:
        """
        Log an audit entry to both PostgreSQL and JSON log file.

        Args:
            stage: Transaction stage (e.g., "intent_parsing", "payment")
            action: Specific action (e.g., "parsed", "payment_failed")
            details: Additional structured data
            success: Whether the action succeeded
            error_message: Error details if failed
            duration_ms: Operation duration in milliseconds
            request_id: Request correlation ID
            user_id: User identifier
            transaction_id: Transaction identifier
        """
        timestamp = datetime.utcnow()

        # Use context variables if not explicitly provided
        request_id = request_id or request_id_var.get()
        user_id = user_id or user_id_var.get()
        transaction_id = transaction_id or transaction_id_var.get()

        # Write to PostgreSQL
        if self._pool:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_log
                    (timestamp, request_id, user_id, transaction_id, stage, action,
                     details, success, error_message, duration_ms)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    timestamp,
                    request_id,
                    user_id,
                    transaction_id,
                    stage,
                    action,
                    json.dumps(details or {}),
                    success,
                    error_message,
                    duration_ms,
                )

        # Also log to structured JSON logger
        audit_logger = logging.getLogger("audit")
        audit_logger.info(
            "audit_entry",
            extra={
                "audit_stage": stage,
                "audit_action": action,
                "audit_success": success,
                "audit_details": details,
                "audit_error": error_message,
                "audit_duration_ms": duration_ms,
            },
        )

    async def get_audit_trail(
        self,
        transaction_id: str = None,
        user_id: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list:
        """
        Retrieve audit trail for a transaction or user.

        Args:
            transaction_id: Filter by transaction
            user_id: Filter by user
            limit: Maximum entries to return
            offset: Pagination offset

        Returns:
            List of audit entries
        """
        if not self._pool:
            return []

        async with self._pool.acquire() as conn:
            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []
            param_idx = 1

            if transaction_id:
                query += f" AND transaction_id = ${param_idx}"
                params.append(transaction_id)
                param_idx += 1

            if user_id:
                query += f" AND user_id = ${param_idx}"
                params.append(user_id)
                param_idx += 1

            query += f" ORDER BY timestamp DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
            params.extend([limit, offset])

            rows = await conn.fetch(query, *params)

            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"].isoformat(),
                    "request_id": str(row["request_id"]) if row["request_id"] else None,
                    "user_id": row["user_id"],
                    "transaction_id": str(row["transaction_id"]) if row["transaction_id"] else None,
                    "stage": row["stage"],
                    "action": row["action"],
                    "details": row["details"],
                    "success": row["success"],
                    "error_message": row["error_message"],
                    "duration_ms": row["duration_ms"],
                }
                for row in rows
            ]

    async def export_audit_trail(
        self,
        transaction_id: str = None,
        user_id: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> list:
        """
        Export full audit trail for compliance reporting.

        Args:
            transaction_id: Filter by transaction
            user_id: Filter by user
            start_date: ISO format start date
            end_date: ISO format end date

        Returns:
            Complete audit trail entries
        """
        if not self._pool:
            return []

        async with self._pool.acquire() as conn:
            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []
            param_idx = 1

            if transaction_id:
                query += f" AND transaction_id = ${param_idx}"
                params.append(transaction_id)
                param_idx += 1

            if user_id:
                query += f" AND user_id = ${param_idx}"
                params.append(user_id)
                param_idx += 1

            if start_date:
                query += f" AND timestamp >= ${param_idx}"
                params.append(start_date)
                param_idx += 1

            if end_date:
                query += f" AND timestamp <= ${param_idx}"
                params.append(end_date)
                param_idx += 1

            query += " ORDER BY timestamp ASC"

            rows = await conn.fetch(query, *params)

            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"].isoformat(),
                    "request_id": str(row["request_id"]) if row["request_id"] else None,
                    "user_id": row["user_id"],
                    "transaction_id": str(row["transaction_id"]) if row["transaction_id"] else None,
                    "stage": row["stage"],
                    "action": row["action"],
                    "details": row["details"],
                    "success": row["success"],
                    "error_message": row["error_message"],
                    "duration_ms": row["duration_ms"],
                }
                for row in rows
            ]


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application-wide structured logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    settings = get_settings()

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


# Global audit logger instance (initialized on startup)
audit_logger: AsyncAuditLogger = None


async def get_audit_logger() -> AsyncAuditLogger:
    """Get or create the global audit logger instance."""
    global audit_logger
    if audit_logger is None:
        audit_logger = AsyncAuditLogger()
        await audit_logger.initialize()
    return audit_logger


async def close_audit_logger() -> None:
    """Close the global audit logger."""
    global audit_logger
    if audit_logger:
        await audit_logger.close()
        audit_logger = None


class RequestContext:
    """
    Context manager for request-scoped logging.

    Usage:
        with RequestContext(request_id="req_123", user_id="user_456", transaction_id="txn_789"):
            logger.info("Processing request")
            # All logs within this block will have the context
    """

    def __init__(
        self,
        request_id: str = None,
        user_id: str = None,
        transaction_id: str = None,
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.transaction_id = transaction_id
        self._tokens = []

    def __enter__(self):
        self._tokens = []
        if self.request_id:
            self._tokens.append((request_id_var, request_id_var.set(self.request_id)))
        if self.user_id:
            self._tokens.append((user_id_var, user_id_var.set(self.user_id)))
        if self.transaction_id:
            self._tokens.append((transaction_id_var, transaction_id_var.set(self.transaction_id)))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for var, token in reversed(self._tokens):
            if token is not None:
                try:
                    var.reset(token)
                except ValueError:
                    pass


# Convenience function for quick audit logging
async def audit_log(
    stage: str,
    action: str,
    details: Dict[str, Any] = None,
    success: bool = True,
    error_message: str = None,
    duration_ms: int = None,
) -> None:
    """Quick audit log using global audit logger."""
    logger = await get_audit_logger()
    await logger.log_audit(
        stage=stage,
        action=action,
        details=details,
        success=success,
        error_message=error_message,
        duration_ms=duration_ms,
    )