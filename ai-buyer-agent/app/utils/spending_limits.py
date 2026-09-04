"""
Spending limit enforcement utilities for AI Buyer Agent.

Provides functions to check and enforce daily spending limits
and per-transaction limits using PostgreSQL.
"""

from datetime import date
from typing import Optional

import asyncpg
from app.config import get_settings


async def check_daily_spending_limit(
    pool: asyncpg.Pool,
    user_id: str,
    amount_paise: int,
) -> tuple[bool, Optional[str]]:
    """
    Check if the user's daily spending would exceed the configured limit.
    Reads the PostgreSQL transactions_audit table and enforces the daily cap.
    """
    settings = get_settings()
    daily_limit_paise = settings.daily_spending_limit

    async with pool.acquire() as conn:
        today = date.today()
        total_spent = await conn.fetchval(
            """
            SELECT COALESCE(SUM(amount_paise), 0)
            FROM transactions_audit
            WHERE user_id = $1
              AND status = 'completed'
              AND DATE(created_at AT TIME ZONE 'UTC') = $2
            """,
            user_id,
            today,
        )

        total_spent = total_spent or 0
        new_total = total_spent + amount_paise

        if new_total > daily_limit_paise:
            remaining_inr = max(0, (daily_limit_paise - total_spent) / 100)
            return False, (
                f"Daily spending limit exceeded. "
                f"You have spent ₹{total_spent / 100:,.2f} today. "
                f"Limit is ₹{daily_limit_paise / 100:,.2f}. "
                f"Remaining: ₹{remaining_inr:,.2f}"
            )

    return True, None


async def check_transaction_limit(
    amount_paise: int,
) -> tuple[bool, Optional[str]]:
    """
    Check if transaction amount exceeds the per-transaction limit.

    Args:
        amount_paise: Transaction amount in paise

    Returns:
        Tuple of (allowed: bool, error_message: str or None)
    """
    settings = get_settings()
    max_txn_paise = settings.max_transaction_amount

    if amount_paise > max_txn_paise:
        return False, (
            f"Transaction amount ₹{amount_paise / 100:,.2f} exceeds "
            f"maximum limit of ₹{max_txn_paise / 100:,.2f}"
        )

    return True, None


async def check_spending_limits(
    pool: asyncpg.Pool,
    user_id: str,
    amount_paise: int,
) -> tuple[bool, Optional[str]]:
    """
    Check both per-transaction and daily spending limits.

    Args:
        pool: asyncpg connection pool
        user_id: User identifier
        amount_paise: Transaction amount in paise

    Returns:
        Tuple of (allowed: bool, error_message: str or None)
    """
    # Check per-transaction limit
    allowed, error = await check_transaction_limit(amount_paise)
    if not allowed:
        return False, error

    # Check daily limit
    allowed, error = await check_daily_spending_limit(pool, user_id, amount_paise)
    if not allowed:
        return False, error

    return True, None