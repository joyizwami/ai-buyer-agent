"""
Razorpay API client wrapper with retry logic, circuit breaker, and test mode enforcement.

This module provides a robust async interface to Razorpay APIs with:
- Exponential backoff retry
- Circuit breaker pattern for fault tolerance
- Test mode enforcement (CRITICAL for buildathon)
- Comprehensive error handling and mapping
- Structured audit logging
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

import httpx
from pydantic import BaseModel, Field

from app.config import get_settings, validate_test_mode, RAZORPAY_TEST_CARDS
from app.utils.logger import get_logger, audit_log, RequestContext
from app.models.transaction import RazorpayOrder, RazorpayPayment, PaymentMethod


logger = get_logger(__name__)


class RazorpayErrorCode(str, Enum):
    """Standardized error codes for Razorpay failures."""

    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT = "TIMEOUT"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    INVALID_REQUEST = "INVALID_REQUEST"
    ORDER_CREATION_FAILED = "ORDER_CREATION_FAILED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    PAYMENT_DECLINED = "PAYMENT_DECLINED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    CARD_EXPIRED = "CARD_EXPIRED"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    SERVER_ERROR = "SERVER_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class RazorpayAPIError(Exception):
    """Base exception for Razorpay API errors."""

    def __init__(
        self,
        message: str,
        error_code: RazorpayErrorCode = RazorpayErrorCode.UNKNOWN_ERROR,
        status_code: int = None,
        response_data: Dict[str, Any] = None,
        retryable: bool = False,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.response_data = response_data or {}
        self.retryable = retryable


class PaymentFailedError(RazorpayAPIError):
    """Raised when payment fails (declined, insufficient funds, etc.)."""

    def __init__(self, message: str, error_code: RazorpayErrorCode, **kwargs):
        super().__init__(message, error_code, retryable=False, **kwargs)


class InsufficientFundsError(PaymentFailedError):
    """Raised when payment fails due to insufficient funds."""

    def __init__(self, message: str = "Insufficient funds", **kwargs):
        super().__init__(message, RazorpayErrorCode.INSUFFICIENT_FUNDS, **kwargs)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for fault tolerance.

    Prevents cascade failures by stopping requests to a failing service.
    After threshold failures, opens circuit. After timeout, half-opens to test.
    """

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 30.0  # seconds

    _state: CircuitBreakerState = CircuitBreakerState.CLOSED
    _failure_count: int = 0
    _success_count: int = 0
    _last_failure_time: float = 0

    @property
    def state(self) -> CircuitBreakerState:
        if self._state == CircuitBreakerState.OPEN:
            # Check if timeout has passed to transition to half-open
            if time.time() - self._last_failure_time >= self.timeout:
                self._state = CircuitBreakerState.HALF_OPEN
                self._success_count = 0
                logger.warning("Circuit breaker transitioning to HALF_OPEN")
        return self._state

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == CircuitBreakerState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = CircuitBreakerState.CLOSED
                self._failure_count = 0
                logger.info("Circuit breaker CLOSED after recovery")
        elif self._state == CircuitBreakerState.CLOSED:
            self._failure_count = 0  # Reset on success

    def record_failure(self) -> None:
        """Record a failed call."""
        self._last_failure_time = time.time()
        self._failure_count += 1

        if self._state == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open goes back to open
            self._state = CircuitBreakerState.OPEN
            logger.error("Circuit breaker OPEN after half-open failure")
        elif self._state == CircuitBreakerState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitBreakerState.OPEN
                logger.error(f"Circuit breaker OPEN after {self._failure_count} failures")

    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        return self.state != CircuitBreakerState.OPEN


class RazorpayClient:
    """
    Async Razorpay API client with resilience patterns.

    Features:
    - Exponential backoff retry (configurable)
    - Circuit breaker for fault tolerance
    - Test mode enforcement
    - Request/response logging for audit
    - Proper error mapping
    """

    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        validate_test_mode()  # Enforce test mode at initialization

        # HTTP client with connection pooling
        self._client: Optional[httpx.AsyncClient] = None
        self._circuit_breaker = CircuitBreaker()

        # Auth header (Basic auth with key_id:key_secret)
        self._auth = (self.settings.razorpay_key_id, self.settings.razorpay_key_secret)
        self._base_url = self.settings.razorpay_base_url.rstrip("/")

    async def __aenter__(self) -> "RazorpayClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                auth=self._auth,
                timeout=httpx.Timeout(self.settings.request_timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _get_headers(self, idempotency_key: str = None) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"AI-Buyer-Agent/{self.settings.app_version}",
        }
        if idempotency_key:
            headers["X-Razorpay-Idempotency-Key"] = idempotency_key
        return headers

    def _map_error(self, response: httpx.Response) -> RazorpayAPIError:
        """Map HTTP response to appropriate error."""
        status = response.status_code
        try:
            error_data = response.json()
            error_desc = error_data.get("error", {}).get("description", "Unknown error")
            error_code_str = error_data.get("error", {}).get("code", "UNKNOWN")
        except Exception:
            error_desc = response.text
            error_code_str = "PARSE_ERROR"

        # Map Razorpay error codes to our standardized codes
        error_mapping = {
            "BAD_REQUEST_ERROR": RazorpayErrorCode.INVALID_REQUEST,
            "AUTHENTICATION_ERROR": RazorpayErrorCode.AUTHENTICATION_FAILED,
            "RATE_LIMIT_ERROR": RazorpayErrorCode.RATE_LIMITED,
            "SERVER_ERROR": RazorpayErrorCode.SERVER_ERROR,
            "GATEWAY_ERROR": RazorpayErrorCode.PROCESSING_ERROR,
        }

        error_code = error_mapping.get(error_code_str, RazorpayErrorCode.UNKNOWN_ERROR)

        # Determine if retryable
        retryable = status in {429, 500, 502, 503, 504} or error_code in {
            RazorpayErrorCode.RATE_LIMITED,
            RazorpayErrorCode.SERVER_ERROR,
            RazorpayErrorCode.NETWORK_ERROR,
            RazorpayErrorCode.TIMEOUT,
        }

        return RazorpayAPIError(
            message=error_desc,
            error_code=error_code,
            status_code=status,
            response_data=error_data if "error_data" in locals() else {},
            retryable=retryable,
        )

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        data: Dict[str, Any] = None,
        idempotency_key: str = None,
    ) -> Dict[str, Any]:
        """
        Execute HTTP request with retry logic and circuit breaker.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/orders")
            data: Request body
            idempotency_key: Key for idempotent requests

        Returns:
            Parsed JSON response

        Raises:
            RazorpayAPIError: On API errors
        """
        if not self._circuit_breaker.can_execute():
            raise RazorpayAPIError(
                "Circuit breaker is OPEN - service unavailable",
                RazorpayErrorCode.SERVER_ERROR,
                retryable=True,
            )

        await self._ensure_client()

        url = f"{self._base_url}{endpoint}"
        headers = self._get_headers(idempotency_key)

        last_error = None
        for attempt in range(self.settings.max_retries + 1):
            start_time = time.time()

            try:
                logger.debug(
                    f"Razorpay API call: {method} {endpoint}",
                    extra={"attempt": attempt + 1, "endpoint": endpoint},
                )

                response = await self._client.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=headers,
                )

                duration_ms = int((time.time() - start_time) * 1000)

                if response.is_success:
                    self._circuit_breaker.record_success()
                    result = response.json()

                    # Audit log successful API call
                    audit_log(
                        stage="razorpay_api",
                        action=f"{method.lower()}_{endpoint.strip('/')}",
                        details={"endpoint": endpoint, "status": response.status_code},
                        success=True,
                        duration_ms=duration_ms,
                    )

                    return result

                # Handle error responses
                error = self._map_error(response)
                last_error = error

                # Audit log failed API call
                audit_log(
                    stage="razorpay_api",
                    action=f"{method.lower()}_{endpoint.strip('/')}_failed",
                    details={
                        "endpoint": endpoint,
                        "status": response.status_code,
                        "error_code": error.error_code.value,
                    },
                    success=False,
                    error_message=error.message,
                    duration_ms=duration_ms,
                )

                # Don't retry non-retryable errors
                if not error.retryable:
                    self._circuit_breaker.record_failure()
                    raise error

                # Retryable error - record failure and continue
                self._circuit_breaker.record_failure()

            except httpx.TimeoutException as e:
                duration_ms = int((time.time() - start_time) * 1000)
                last_error = RazorpayAPIError(
                    f"Request timeout: {str(e)}",
                    RazorpayErrorCode.TIMEOUT,
                    retryable=True,
                )
                self._circuit_breaker.record_failure()

                audit_log(
                    stage="razorpay_api",
                    action=f"{method.lower()}_{endpoint.strip('/')}_timeout",
                    details={"endpoint": endpoint},
                    success=False,
                    error_message=str(e),
                    duration_ms=duration_ms,
                )

            except httpx.NetworkError as e:
                duration_ms = int((time.time() - start_time) * 1000)
                last_error = RazorpayAPIError(
                    f"Network error: {str(e)}",
                    RazorpayErrorCode.NETWORK_ERROR,
                    retryable=True,
                )
                self._circuit_breaker.record_failure()

                audit_log(
                    stage="razorpay_api",
                    action=f"{method.lower()}_{endpoint.strip('/')}_network_error",
                    details={"endpoint": endpoint},
                    success=False,
                    error_message=str(e),
                    duration_ms=duration_ms,
                )

            except RazorpayAPIError:
                # Already logged, re-raise
                raise

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                last_error = RazorpayAPIError(
                    f"Unexpected error: {str(e)}",
                    RazorpayErrorCode.UNKNOWN_ERROR,
                    retryable=False,
                )
                self._circuit_breaker.record_failure()

                audit_log(
                    stage="razorpay_api",
                    action=f"{method.lower()}_{endpoint.strip('/')}_unexpected",
                    details={"endpoint": endpoint},
                    success=False,
                    error_message=str(e),
                    duration_ms=duration_ms,
                )
                raise last_error

            # Exponential backoff before retry
            if attempt < self.settings.max_retries:
                delay = self.settings.retry_base_delay * (2**attempt)
                logger.warning(
                    f"Retrying in {delay}s (attempt {attempt + 2}/{self.settings.max_retries + 1})",
                    extra={"delay": delay, "attempt": attempt + 2},
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        raise last_error or RazorpayAPIError(
            "Max retries exceeded",
            RazorpayErrorCode.UNKNOWN_ERROR,
            retryable=True,
        )

    # ==================== ORDER API ====================

    async def create_order(
        self,
        amount_paise: int,
        currency: str = "INR",
        receipt: str = None,
        notes: Dict[str, str] = None,
        idempotency_key: str = None,
    ) -> RazorpayOrder:
        """
        Create a Razorpay order.

        Args:
            amount_paise: Amount in paise
            currency: Currency code (default INR)
            receipt: Merchant receipt ID
            notes: Additional notes
            idempotency_key: For idempotent requests

        Returns:
            RazorpayOrder object

        Raises:
            RazorpayAPIError: On failure
        """
        data = {
            "amount": amount_paise,
            "currency": currency,
        }

        if receipt:
            data["receipt"] = receipt
        if notes:
            data["notes"] = notes

        # TODO: Replace with UAP agent handshake when available
        # This is where NPCI UAP protocol would initiate order creation

        result = await self._request_with_retry(
            "POST", "/orders", data=data, idempotency_key=idempotency_key
        )

        return RazorpayOrder(**result)

    async def fetch_order(self, order_id: str) -> RazorpayOrder:
        """Fetch order details by ID."""
        result = await self._request_with_retry("GET", f"/orders/{order_id}")
        return RazorpayOrder(**result)

    # ==================== PAYMENT API ====================

    async def fetch_payment(self, payment_id: str) -> RazorpayPayment:
        """Fetch payment details by ID."""
        result = await self._request_with_retry("GET", f"/payments/{payment_id}")
        return RazorpayPayment(**result)

    async def capture_payment(
        self,
        payment_id: str,
        amount_paise: int = None,
        idempotency_key: str = None,
    ) -> RazorpayPayment:
        """
        Capture a payment (for authorized payments).

        Args:
            payment_id: Payment to capture
            amount_paise: Amount to capture (default: full amount)
            idempotency_key: For idempotent requests

        Returns:
            Captured RazorpayPayment
        """
        data = {}
        if amount_paise:
            data["amount"] = amount_paise

        result = await self._request_with_retry(
            "POST", f"/payments/{payment_id}/capture", data=data, idempotency_key=idempotency_key
        )

        return RazorpayPayment(**result)

    async def refund_payment(
        self,
        payment_id: str,
        amount_paise: int = None,
        notes: Dict[str, str] = None,
        idempotency_key: str = None,
    ) -> Dict[str, Any]:
        """
        Refund a payment.

        Args:
            payment_id: Payment to refund
            amount_paise: Amount to refund (default: full amount)
            notes: Refund notes
            idempotency_key: For idempotent requests

        Returns:
            Refund object
        """
        data = {}
        if amount_paise:
            data["amount"] = amount_paise
        if notes:
            data["notes"] = notes

        result = await self._request_with_retry(
            "POST", f"/payments/{payment_id}/refund", data=data, idempotency_key=idempotency_key
        )

        return result

    # ==================== TEST MODE HELPERS ====================

    def get_test_card(self, scenario: str = "success") -> str:
        """
        Get a Razorpay test card number for a scenario.

        Args:
            scenario: One of 'success', 'decline', 'insufficient_funds', 'expired', 'processing_error'

        Returns:
            Test card number (no spaces)
        """
        return RAZORPAY_TEST_CARDS.get(scenario, RAZORPAY_TEST_CARDS["success"])

    def create_test_payment_payload(
        self,
        order_id: str,
        card_scenario: str = "success",
        method: PaymentMethod = PaymentMethod.CARD,
    ) -> Dict[str, Any]:
        """
        Create a test payment payload for Razorpay test mode.

        In test mode, Razorpay accepts special card numbers to simulate outcomes.
        This creates a payload that can be used with Razorpay's test checkout.

        Args:
            order_id: Razorpay order ID
            card_scenario: Test scenario
            method: Payment method

        Returns:
            Payment payload for test checkout
        """
        card_number = self.get_test_card(card_scenario)

        # Format card number for display (groups of 4)
        formatted_card = " ".join([card_number[i:i+4] for i in range(0, len(card_number), 4)])

        return {
            "order_id": order_id,
            "method": method.value,
            "card": {
                "number": card_number,
                "name": "Test User",
                "expiry": "12/30",
                "cvv": "123",
            },
            "test_mode": True,
            # For frontend integration
            "display_card": formatted_card,
            "scenario": card_scenario,
        }


# Global client instance for dependency injection
_razorpay_client: Optional[RazorpayClient] = None


async def get_razorpay_client() -> RazorpayClient:
    """Get or create the global Razorpay client instance."""
    global _razorpay_client
    if _razorpay_client is None:
        _razorpay_client = RazorpayClient()
    return _razorpay_client


async def close_razorpay_client() -> None:
    """Close the global Razorpay client."""
    global _razorpay_client
    if _razorpay_client:
        await _razorpay_client.close()
        _razorpay_client = None