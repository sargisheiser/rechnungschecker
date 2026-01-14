"""Billing API endpoints for subscription management."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.config import get_settings
from app.core.exceptions import PaymentError
from app.models.user import PlanType, User
from app.schemas.billing import (
    BillingPortalRequest,
    BillingPortalResponse,
    CheckoutRequest,
    CheckoutResponse,
    InvoicesResponse,
    PlanInfo,
    PlansResponse,
    SubscriptionInfo,
    SubscriptionStatus,
    WebhookResponse,
    get_all_plans,
    get_plan_info,
    PlanTier,
)
from app.services.billing.stripe import StripeService, WebhookHandler
from app.services.email import email_service

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()
stripe_service = StripeService()
webhook_handler = WebhookHandler(stripe_service)


@router.get(
    "/plans",
    response_model=PlansResponse,
    summary="Get available plans",
    description="Retrieve all available subscription plans with features and pricing.",
)
async def get_plans() -> PlansResponse:
    """Get all available subscription plans."""
    return PlansResponse(plans=get_all_plans())


@router.get(
    "/plans/{plan_id}",
    response_model=PlanInfo,
    summary="Get plan details",
    description="Get detailed information about a specific plan.",
)
async def get_plan(plan_id: PlanTier) -> PlanInfo:
    """Get details for a specific plan."""
    return get_plan_info(plan_id)


@router.get(
    "/subscription",
    response_model=SubscriptionInfo,
    summary="Get current subscription",
    description="Get the current user's subscription information.",
)
async def get_subscription(
    current_user: CurrentUser,
) -> SubscriptionInfo:
    """Get current user's subscription information."""
    # Get subscription details from Stripe if available
    subscription_data = None
    if current_user.stripe_subscription_id:
        subscription_data = await stripe_service.get_subscription(
            current_user.stripe_subscription_id
        )

    # Determine status
    if subscription_data:
        status = SubscriptionStatus(subscription_data.get("status", "active"))
        current_period_end = datetime.fromtimestamp(
            subscription_data.get("current_period_end", 0)
        )
        cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)
    else:
        status = SubscriptionStatus.ACTIVE if current_user.plan != PlanType.FREE else SubscriptionStatus.ACTIVE
        current_period_end = current_user.plan_valid_until
        cancel_at_period_end = False

    return SubscriptionInfo(
        plan=PlanTier(current_user.plan.value),
        status=status,
        current_period_start=None,  # Would need to store or fetch from Stripe
        current_period_end=current_period_end,
        cancel_at_period_end=cancel_at_period_end,
        stripe_subscription_id=current_user.stripe_subscription_id,
        stripe_customer_id=current_user.stripe_customer_id,
    )


@router.get(
    "/usage",
    summary="Get usage statistics",
    description="Get the current user's usage statistics and limits.",
)
async def get_usage(
    current_user: CurrentUser,
) -> dict:
    """Get current user's usage statistics."""
    return {
        "plan": current_user.plan.value,
        "validations_used": current_user.validations_this_month,
        "validations_limit": current_user.get_validation_limit(),
        "conversions_used": current_user.conversions_this_month,
        "conversions_limit": current_user.get_conversion_limit(),
        "usage_reset_date": datetime.combine(
            current_user.usage_reset_date,
            datetime.min.time(),
        ).isoformat(),
    }


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Create checkout session",
    description="Create a Stripe Checkout session to subscribe to a plan.",
)
async def create_checkout(
    data: CheckoutRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> CheckoutResponse:
    """Create a checkout session for subscription."""
    if data.plan == PlanTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Der kostenlose Plan erfordert keine Zahlung",
        )

    # Check if user already has a paid subscription
    if current_user.plan != PlanType.FREE and current_user.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sie haben bereits ein aktives Abonnement. Nutzen Sie das Kundenportal zum Ändern.",
        )

    # Demo mode - redirect to demo checkout page
    if settings.demo_mode:
        from urllib.parse import urlencode
        params = urlencode({
            "plan": data.plan.value,
            "annual": str(data.annual).lower(),
            "success_url": str(data.success_url),
            "cancel_url": str(data.cancel_url),
        })
        demo_url = f"/demo-checkout?{params}"
        return CheckoutResponse(checkout_url=demo_url)

    try:
        # Map PlanTier to PlanType
        plan_type = PlanType(data.plan.value)

        checkout_url = await stripe_service.create_checkout_session(
            user=current_user,
            plan=plan_type,
            success_url=str(data.success_url),
            cancel_url=str(data.cancel_url),
            annual=data.annual,
        )

        return CheckoutResponse(checkout_url=checkout_url)

    except PaymentError as e:
        logger.error(f"Checkout error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/demo-confirm",
    summary="Confirm demo checkout",
    description="Confirm a demo checkout and upgrade the user's plan (demo mode only).",
)
async def confirm_demo_checkout(
    plan: PlanTier,
    annual: bool,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """Confirm demo checkout and upgrade user plan.

    This endpoint only works in demo mode and immediately upgrades the user.
    """
    if not settings.demo_mode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Demo mode is not enabled",
        )

    if plan == PlanTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot checkout for free plan",
        )

    # Upgrade the user's plan
    plan_type = PlanType(plan.value)
    current_user.plan = plan_type
    current_user.stripe_customer_id = f"demo_cus_{current_user.id}"
    current_user.stripe_subscription_id = f"demo_sub_{current_user.id}"

    # Set plan validity (1 year for annual, 1 month for monthly)
    from datetime import timedelta
    if annual:
        current_user.plan_valid_until = datetime.utcnow() + timedelta(days=365)
    else:
        current_user.plan_valid_until = datetime.utcnow() + timedelta(days=30)

    await db.commit()

    logger.info(f"Demo checkout completed: user={current_user.email}, plan={plan.value}, annual={annual}")

    return {
        "status": "success",
        "message": f"Plan erfolgreich auf {plan.value} aktualisiert (Demo-Modus)",
        "plan": plan.value,
    }


@router.post(
    "/portal",
    response_model=BillingPortalResponse,
    summary="Open billing portal",
    description="Create a Stripe Billing Portal session for managing subscription.",
)
async def create_portal_session(
    data: BillingPortalRequest,
    current_user: CurrentUser,
) -> BillingPortalResponse:
    """Create a billing portal session."""
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kein Stripe-Konto vorhanden. Bitte schließen Sie zuerst ein Abonnement ab.",
        )

    # Demo mode - redirect to demo portal page
    if settings.demo_mode:
        return BillingPortalResponse(portal_url="/demo-portal")

    try:
        portal_url = await stripe_service.create_billing_portal_session(
            user=current_user,
            return_url=str(data.return_url),
        )

        return BillingPortalResponse(portal_url=portal_url)

    except PaymentError as e:
        logger.error(f"Portal error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/demo-cancel",
    summary="Cancel subscription in demo mode",
    description="Cancel the subscription and downgrade to free plan (demo mode only).",
)
async def demo_cancel_subscription(
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """Cancel subscription in demo mode."""
    if not settings.demo_mode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Demo mode is not enabled",
        )

    if current_user.plan == PlanType.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kein aktives Abonnement vorhanden",
        )

    # Downgrade to free
    current_user.plan = PlanType.FREE
    current_user.stripe_subscription_id = None
    current_user.plan_valid_until = None

    await db.commit()

    logger.info(f"Demo subscription cancelled: user={current_user.email}")

    return {
        "status": "success",
        "message": "Abonnement wurde gekuendigt (Demo-Modus)",
    }


@router.post(
    "/cancel",
    summary="Cancel subscription",
    description="Cancel the current subscription at the end of the billing period.",
)
async def cancel_subscription(
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Cancel the current subscription."""
    if not current_user.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kein aktives Abonnement vorhanden",
        )

    success = await stripe_service.cancel_subscription(
        current_user.stripe_subscription_id,
        at_period_end=True,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Abonnement konnte nicht gekündigt werden",
        )

    logger.info(f"Subscription cancelled for user: {current_user.email}")

    return {
        "message": "Abonnement wird zum Ende des Abrechnungszeitraums gekündigt"
    }


@router.post(
    "/webhook",
    response_model=WebhookResponse,
    summary="Stripe webhook",
    description="Handle Stripe webhook events.",
    include_in_schema=False,  # Hide from public docs
)
async def stripe_webhook(
    request: Request,
    db: DbSession,
) -> WebhookResponse:
    """Handle Stripe webhook events."""
    # Get raw body and signature
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature", "")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header",
        )

    # Verify signature
    event = stripe_service.verify_webhook_signature(payload, signature)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    # Handle the event
    result = await webhook_handler.handle_event(event)

    # Process database updates based on event
    await _process_webhook_result(result, db)

    return WebhookResponse(
        status="success",
        message=f"Processed {event.get('type', 'unknown')} event",
    )


async def _process_webhook_result(result: dict, db: DbSession) -> None:
    """Process webhook result and update database.

    Args:
        result: Result from webhook handler
        db: Database session
    """
    action = result.get("action")

    if action == "checkout_completed":
        # Update user with Stripe IDs
        user_id = result.get("user_id")
        subscription_id = result.get("subscription_id")
        customer_id = result.get("customer_id")

        if user_id:
            query = select(User).where(User.id == UUID(user_id))
            user_result = await db.execute(query)
            user = user_result.scalar_one_or_none()

            if user:
                user.stripe_customer_id = customer_id
                user.stripe_subscription_id = subscription_id
                # Plan will be updated by subscription webhook
                logger.info(f"Updated user {user.email} with Stripe IDs")

    elif action == "subscription_updated":
        subscription_id = result.get("subscription_id")
        subscription_status = result.get("subscription_status")

        # Find user by subscription ID
        query = select(User).where(User.stripe_subscription_id == subscription_id)
        user_result = await db.execute(query)
        user = user_result.scalar_one_or_none()

        if user and subscription_status == "canceled":
            user.plan = PlanType.FREE
            user.stripe_subscription_id = None
            logger.info(f"Downgraded user {user.email} to free plan")

    elif action == "subscription_deleted":
        subscription_id = result.get("subscription_id")

        # Find and downgrade user
        query = select(User).where(User.stripe_subscription_id == subscription_id)
        user_result = await db.execute(query)
        user = user_result.scalar_one_or_none()

        if user:
            user.plan = PlanType.FREE
            user.stripe_subscription_id = None
            logger.info(f"Subscription deleted, downgraded user {user.email}")

    elif action == "payment_failed":
        subscription_id = result.get("subscription_id")
        invoice_id = result.get("invoice_id", "unknown")

        # Find user and send notification
        query = select(User).where(User.stripe_subscription_id == subscription_id)
        user_result = await db.execute(query)
        user = user_result.scalar_one_or_none()

        if user:
            # Send payment failed email notification
            await email_service.send_payment_failed_email(user.email, invoice_id)
            logger.warning(f"Payment failed for user {user.email}, notification sent")
