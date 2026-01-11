"""Pydantic schemas for billing endpoints."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class PlanTier(str, Enum):
    """Available subscription plans."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    STEUERBERATER = "steuerberater"


class PlanFeatures(BaseModel):
    """Features included in a plan."""

    validations_per_month: int | None = Field(description="None means unlimited")
    conversions_per_month: int
    batch_upload: bool
    batch_limit: int
    pdf_reports: bool
    pdf_watermark: bool
    validation_history_days: int | None = Field(description="None means unlimited")
    api_access: bool
    api_calls_per_month: int
    multi_client: bool
    max_clients: int
    support_level: str
    custom_branding: bool


class PlanInfo(BaseModel):
    """Information about a subscription plan."""

    id: PlanTier
    name: str
    description: str
    price_monthly: float
    price_annual: float
    currency: str = "EUR"
    features: PlanFeatures
    popular: bool = False


class PlansResponse(BaseModel):
    """Response containing all available plans."""

    plans: list[PlanInfo]


class CheckoutRequest(BaseModel):
    """Request to create a checkout session."""

    plan: PlanTier
    annual: bool = Field(default=False, description="Annual billing (20% discount)")
    success_url: HttpUrl
    cancel_url: HttpUrl


class CheckoutResponse(BaseModel):
    """Response with checkout session URL."""

    checkout_url: str
    session_id: str | None = None


class BillingPortalRequest(BaseModel):
    """Request to create a billing portal session."""

    return_url: HttpUrl


class BillingPortalResponse(BaseModel):
    """Response with billing portal URL."""

    portal_url: str


class SubscriptionStatus(str, Enum):
    """Stripe subscription statuses."""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    PAUSED = "paused"


class SubscriptionInfo(BaseModel):
    """Current subscription information."""

    plan: PlanTier
    status: SubscriptionStatus
    current_period_start: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    stripe_subscription_id: str | None
    stripe_customer_id: str | None


class InvoiceInfo(BaseModel):
    """Invoice information."""

    id: str
    number: str | None
    status: str
    amount_due: float
    amount_paid: float
    currency: str
    created: datetime
    pdf_url: str | None
    hosted_invoice_url: str | None


class InvoicesResponse(BaseModel):
    """Response containing user's invoices."""

    invoices: list[InvoiceInfo]
    has_more: bool


class WebhookResponse(BaseModel):
    """Response from webhook handler."""

    status: str
    message: str | None = None


# Plan definitions with features
PLAN_DEFINITIONS: dict[PlanTier, PlanInfo] = {
    PlanTier.FREE: PlanInfo(
        id=PlanTier.FREE,
        name="Kostenlos",
        description="Für gelegentliche Nutzung",
        price_monthly=0,
        price_annual=0,
        features=PlanFeatures(
            validations_per_month=5,
            conversions_per_month=0,
            batch_upload=False,
            batch_limit=0,
            pdf_reports=True,
            pdf_watermark=True,
            validation_history_days=0,
            api_access=False,
            api_calls_per_month=0,
            multi_client=False,
            max_clients=0,
            support_level="community",
            custom_branding=False,
        ),
    ),
    PlanTier.STARTER: PlanInfo(
        id=PlanTier.STARTER,
        name="Starter",
        description="Für kleine Unternehmen",
        price_monthly=29,
        price_annual=279,
        features=PlanFeatures(
            validations_per_month=100,
            conversions_per_month=20,
            batch_upload=True,
            batch_limit=5,
            pdf_reports=True,
            pdf_watermark=False,
            validation_history_days=30,
            api_access=False,
            api_calls_per_month=0,
            multi_client=False,
            max_clients=0,
            support_level="email",
            custom_branding=False,
        ),
        popular=True,
    ),
    PlanTier.PRO: PlanInfo(
        id=PlanTier.PRO,
        name="Professional",
        description="Für wachsende Unternehmen",
        price_monthly=79,
        price_annual=759,
        features=PlanFeatures(
            validations_per_month=None,  # Unlimited
            conversions_per_month=100,
            batch_upload=True,
            batch_limit=20,
            pdf_reports=True,
            pdf_watermark=False,
            validation_history_days=365,
            api_access=True,
            api_calls_per_month=1000,
            multi_client=False,
            max_clients=0,
            support_level="priority_email",
            custom_branding=True,
        ),
    ),
    PlanTier.STEUERBERATER: PlanInfo(
        id=PlanTier.STEUERBERATER,
        name="Steuerberater",
        description="Für Steuerberater und Kanzleien",
        price_monthly=199,
        price_annual=1899,
        features=PlanFeatures(
            validations_per_month=None,  # Unlimited
            conversions_per_month=500,
            batch_upload=True,
            batch_limit=50,
            pdf_reports=True,
            pdf_watermark=False,
            validation_history_days=None,  # Unlimited
            api_access=True,
            api_calls_per_month=5000,
            multi_client=True,
            max_clients=100,
            support_level="phone",
            custom_branding=True,
        ),
    ),
}


def get_all_plans() -> list[PlanInfo]:
    """Get all available plans."""
    return list(PLAN_DEFINITIONS.values())


def get_plan_info(plan: PlanTier) -> PlanInfo:
    """Get information for a specific plan."""
    return PLAN_DEFINITIONS[plan]
