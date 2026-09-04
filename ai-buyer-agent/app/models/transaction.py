"""
Transaction models for the AI Buyer Agent.

Defines the complete transaction lifecycle, payment details, and audit trail.
All models use Pydantic for validation and serialization.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
import uuid


class TransactionStatus(str, Enum):
    """Transaction lifecycle states."""

    # Initial states
    PENDING = "pending"                    # Created, awaiting processing
    INTENT_PARSED = "intent_parsed"        # User intent understood
    PRODUCTS_FOUND = "products_found"      # Matching products identified
    PRODUCT_SELECTED = "product_selected"  # Best product chosen

    # Approval states
    APPROVAL_REQUIRED = "approval_required"  # Waiting for human approval
    APPROVED = "approved"                    # Human approved
    REJECTED = "rejected"                    # Human rejected

    # Payment states
    ORDER_CREATED = "order_created"        # Razorpay order created
    PAYMENT_INITIATED = "payment_initiated"  # Payment started
    PAYMENT_PROCESSING = "payment_processing"  # Payment in progress
    PAYMENT_SUCCESS = "payment_success"    # Payment completed
    PAYMENT_FAILED = "payment_failed"      # Payment failed

    # Completion states
    COMPLETED = "completed"                # Fully successful
    FAILED = "failed"                      # Failed at any stage
    CANCELLED = "cancelled"                # User/system cancelled
    REFUNDED = "refunded"                  # Refund processed


class ApprovalStatus(str, Enum):
    """Human approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"  # Approval request timed out


class PaymentMethod(str, Enum):
    """Supported payment methods."""

    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    EMI = "emi"


class RazorpayOrder(BaseModel):
    """Razorpay order details."""

    id: str = Field(..., description="Razorpay order ID (order_xxx)")
    entity: str = Field(default="order")
    amount: int = Field(..., description="Amount in paise")
    amount_paid: int = Field(default=0, description="Amount paid in paise")
    amount_due: int = Field(..., description="Amount due in paise")
    currency: str = Field(default="INR")
    receipt: str = Field(..., description="Merchant receipt ID")
    status: str = Field(..., description="Order status: created, attempted, paid")
    attempts: int = Field(default=0)
    notes: Dict[str, str] = Field(default_factory=dict)
    created_at: int = Field(..., description="Unix timestamp")


class RazorpayPayment(BaseModel):
    """Razorpay payment details."""

    id: str = Field(..., description="Razorpay payment ID (pay_xxx)")
    entity: str = Field(default="payment")
    amount: int = Field(..., description="Amount in paise")
    currency: str = Field(default="INR")
    status: str = Field(..., description="Payment status")
    order_id: str = Field(..., description="Associated order ID")
    method: PaymentMethod = Field(..., description="Payment method")
    captured: bool = Field(default=False)
    description: Optional[str] = None
    email: Optional[str] = None
    contact: Optional[str] = None
    fee: int = Field(default=0, description="Fee in paise")
    tax: int = Field(default=0, description="Tax in paise")
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    created_at: int = Field(..., description="Unix timestamp")


class TransactionAuditEntry(BaseModel):
    """Single audit log entry for a transaction."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stage: str = Field(..., description="Transaction stage")
    action: str = Field(..., description="Action performed")
    details: Dict[str, Any] = Field(default_factory=dict)
    success: bool = Field(default=True)
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Transaction(BaseModel):
    """
    Complete transaction record with full audit trail.

    This is the primary entity stored in the database.
    All monetary values in paise.
    """

    # Core identifiers
    id: str = Field(default_factory=lambda: f"txn_{uuid.uuid4().hex[:12]}")
    user_id: str = Field(..., description="User who initiated the transaction")

    # Request details
    original_query: str = Field(..., description="User's natural language request")
    parsed_intent: Dict[str, Any] = Field(default_factory=dict)
    max_budget_paise: int = Field(..., ge=0, description="User's max budget in paise")

    # Product selection
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    product_price_paise: Optional[int] = None
    product_category: Optional[str] = None
    selection_reasoning: Optional[str] = None
    alternatives_considered: List[Dict[str, Any]] = Field(default_factory=list)

    # Payment details
    razorpay_order: Optional[RazorpayOrder] = None
    razorpay_payment: Optional[RazorpayPayment] = None
    payment_method: Optional[PaymentMethod] = None

    # Status tracking
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    approval_status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    approval_requested_at: Optional[datetime] = None
    approval_responded_at: Optional[datetime] = None
    approved_by: Optional[str] = None

    # Financial
    amount_paise: int = Field(default=0, ge=0, description="Final transaction amount in paise")
    currency: str = Field(default="INR")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Audit trail (CRITICAL for Razorpay compliance)
    audit_trail: List[TransactionAuditEntry] = Field(default_factory=list)

    # Error tracking
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = Field(default=0)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def amount_inr(self) -> float:
        """Get amount in INR for display."""
        return self.amount_paise / 100.0

    @property
    def is_terminal(self) -> bool:
        """Check if transaction is in a terminal state."""
        return self.status in {
            TransactionStatus.COMPLETED,
            TransactionStatus.FAILED,
            TransactionStatus.CANCELLED,
            TransactionStatus.REFUNDED,
        }

    @property
    def requires_approval(self) -> bool:
        """Check if transaction requires human approval."""
        return (
            self.amount_paise > 0
            and self.approval_status == ApprovalStatus.PENDING
        )

    def add_audit_entry(
        self,
        stage: str,
        action: str,
        details: Dict[str, Any] = None,
        success: bool = True,
        error_message: str = None,
        duration_ms: int = None,
    ) -> None:
        """Add an entry to the audit trail."""
        entry = TransactionAuditEntry(
            stage=stage,
            action=action,
            details=details or {},
            success=success,
            error_message=error_message,
            duration_ms=duration_ms,
        )
        self.audit_trail.append(entry)
        self.updated_at = datetime.utcnow()

    def update_status(self, status: TransactionStatus) -> None:
        """Update transaction status with audit entry."""
        old_status = self.status
        self.status = status
        self.updated_at = datetime.utcnow()
        self.add_audit_entry(
            stage="status_change",
            action=f"status_changed: {old_status.value} -> {status.value}",
            details={"old_status": old_status.value, "new_status": status.value},
        )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PurchaseRequest(BaseModel):
    """Request model for purchase endpoint."""

    query: str = Field(
        ..., min_length=3, max_length=500,
        description="Natural language purchase request"
    )
    user_id: str = Field(..., min_length=1, max_length=100)
    max_budget: Optional[int] = Field(
        default=None, ge=1, description="Max budget in INR (not paise)"
    )
    preferences: Dict[str, Any] = Field(default_factory=dict)
    require_approval: bool = Field(
        default=True, description="Whether to enforce approval threshold"
    )
    receipt_email: Optional[EmailStr] = Field(
        default=None, description="Optional email address for the payment receipt"
    )

    @field_validator("max_budget")
    @classmethod
    def convert_budget_to_paise(cls, v: Optional[int]) -> Optional[int]:
        """Convert INR to paise."""
        if v is not None:
            return v * 100
        return v


class ApprovalRequest(BaseModel):
    """Request model for approval endpoint."""

    transaction_id: str = Field(..., description="Transaction ID to approve/reject")
    approved: bool = Field(..., description="Whether to approve the transaction")
    approver_id: str = Field(..., description="ID of the approver")
    reason: Optional[str] = Field(default=None, description="Reason for rejection")


class PaymentVerificationRequest(BaseModel):
    """Razorpay Checkout response for browser-side payment verification."""

    transaction_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class ApprovalResponse(BaseModel):
    """Response model for approval endpoint."""

    transaction_id: str
    approved: bool
    status: TransactionStatus
    message: str
    next_steps: Optional[str] = None


class PurchaseResponse(BaseModel):
    """Response model for purchase endpoint."""

    status: str = Field(..., description="Overall status: completed, pending_approval, failed")
    transaction_id: str
    product: Optional[Dict[str, Any]] = None
    payment: Optional[Dict[str, Any]] = None
    message: str
    requires_approval: bool = False
    approval_url: Optional[str] = None
    ai_explanation: Optional[str] = Field(default=None, description="Human-readable AI rationale for the chosen purchase decision")
    policy_summary: Optional[Dict[str, Any]] = Field(default=None, description="Budget and approval policy summary")
    audit_trail_summary: List[Dict[str, Any]] = Field(default_factory=list)


class TransactionHistoryResponse(BaseModel):
    """Response model for transaction history."""

    user_id: str
    total_transactions: int
    total_spent_paise: int
    transactions: List[Transaction]


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="healthy, degraded, unhealthy")
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    razorpay_connectivity: bool
    database_connectivity: bool
    llm_connectivity: bool
    checks: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# Status transition rules - defines valid state transitions
VALID_TRANSITIONS: Dict[TransactionStatus, List[TransactionStatus]] = {
    TransactionStatus.PENDING: [
        TransactionStatus.INTENT_PARSED,
        TransactionStatus.FAILED,
    ],
    TransactionStatus.INTENT_PARSED: [
        TransactionStatus.PRODUCTS_FOUND,
        TransactionStatus.FAILED,
    ],
    TransactionStatus.PRODUCTS_FOUND: [
        TransactionStatus.PRODUCT_SELECTED,
        TransactionStatus.FAILED,
    ],
    TransactionStatus.PRODUCT_SELECTED: [
        TransactionStatus.APPROVAL_REQUIRED,
        TransactionStatus.ORDER_CREATED,
        TransactionStatus.FAILED,
    ],
    TransactionStatus.APPROVAL_REQUIRED: [
        TransactionStatus.APPROVED,
        TransactionStatus.REJECTED,
        TransactionStatus.CANCELLED,
    ],
    TransactionStatus.APPROVED: [
        TransactionStatus.ORDER_CREATED,
        TransactionStatus.FAILED,
    ],
    TransactionStatus.REJECTED: [
        TransactionStatus.CANCELLED,
    ],
    TransactionStatus.ORDER_CREATED: [
        TransactionStatus.PAYMENT_INITIATED,
        TransactionStatus.FAILED,
    ],
    TransactionStatus.PAYMENT_INITIATED: [
        TransactionStatus.PAYMENT_PROCESSING,
        TransactionStatus.PAYMENT_FAILED,
    ],
    TransactionStatus.PAYMENT_PROCESSING: [
        TransactionStatus.PAYMENT_SUCCESS,
        TransactionStatus.PAYMENT_FAILED,
    ],
    TransactionStatus.PAYMENT_SUCCESS: [
        TransactionStatus.COMPLETED,
        TransactionStatus.FAILED,
    ],
    TransactionStatus.PAYMENT_FAILED: [
        TransactionStatus.FAILED,
        TransactionStatus.ORDER_CREATED,  # Retry
    ],
    TransactionStatus.COMPLETED: [
        TransactionStatus.REFUNDED,
    ],
    TransactionStatus.FAILED: [],
    TransactionStatus.CANCELLED: [],
    TransactionStatus.REFUNDED: [],
}


def validate_transition(
    current: TransactionStatus, next_status: TransactionStatus
) -> bool:
    """Validate if a status transition is allowed."""
    return next_status in VALID_TRANSITIONS.get(current, [])