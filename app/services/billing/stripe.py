"""Stripe billing service for subscription management."""

import logging
from enum import StrEnum
from typing import Any

import stripe
from stripe import Subscription

from app.config import get_settings
from app.core.exceptions import PaymentError
from app.models.user import PlanType, User

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripePriceId(StrEnum):
    """Stripe Price IDs for each plan."""

    STARTER = "starter"
    PRO = "pro"
    STEUERBERATER = "steuerberater"


# Plan to Stripe price mapping
PLAN_PRICE_MAP: dict[PlanType, str] = {
    PlanType.STARTER: settings.stripe_price_starter,
    PlanType.PRO: settings.stripe_price_pro,
    PlanType.STEUERBERATER: settings.stripe_price_steuerberater,
}

# Stripe price to plan mapping (reverse)
PRICE_PLAN_MAP: dict[str, PlanType] = {
    settings.stripe_price_starter: PlanType.STARTER,
    settings.stripe_price_pro: PlanType.PRO,
    settings.stripe_price_steuerberater: PlanType.STEUERBERATER,
}


class StripeService:
    """Service for Stripe billing operations."""

    def __init__(self) -> None:
        """Initialize Stripe service."""
        if not settings.stripe_secret_key:
            logger.warning("Stripe secret key not configured")

    async def create_customer(self, user: User) -> str:
        """Create a Stripe customer for a user.

        Args:
            user: User to create customer for

        Returns:
            Stripe customer ID

        Raises:
            PaymentError: If customer creation fails
        """
        try:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={
                    "user_id": str(user.id),
                },
            )
            logger.info(f"Created Stripe customer: {customer.id} for user: {user.email}")
            return customer.id
        except stripe.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise PaymentError(
                "Fehler beim Erstellen des Kundenkontos",
                details={"stripe_error": str(e)},
            )

    async def get_or_create_customer(self, user: User) -> str:
        """Get existing or create new Stripe customer.

        Args:
            user: User to get/create customer for

        Returns:
            Stripe customer ID
        """
        if user.stripe_customer_id:
            return user.stripe_customer_id

        return await self.create_customer(user)

    async def create_checkout_session(
        self,
        user: User,
        plan: PlanType,
        success_url: str,
        cancel_url: str,
        annual: bool = False,
    ) -> str:
        """Create a Stripe Checkout session for subscription.

        Args:
            user: User starting checkout
            plan: Plan to subscribe to
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            annual: Whether this is an annual subscription

        Returns:
            Checkout session URL

        Raises:
            PaymentError: If session creation fails
        """
        if plan == PlanType.FREE:
            raise PaymentError("Kostenloser Plan erfordert keine Zahlung")

        price_id = PLAN_PRICE_MAP.get(plan)
        if not price_id:
            raise PaymentError(
                f"Kein Preis für Plan {plan.value} konfiguriert",
                details={"plan": plan.value},
            )

        try:
            # Get or create customer
            customer_id = await self.get_or_create_customer(user)

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card", "sepa_debit"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": str(user.id),
                    "plan": plan.value,
                    "annual": str(annual),
                },
                subscription_data={
                    "metadata": {
                        "user_id": str(user.id),
                        "plan": plan.value,
                    },
                },
                locale="de",
                allow_promotion_codes=True,
                billing_address_collection="required",
                tax_id_collection={"enabled": True},
            )

            logger.info(
                f"Created checkout session: {session.id} for user: {user.email}, plan: {plan.value}"
            )
            return session.url

        except stripe.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise PaymentError(
                "Fehler beim Erstellen der Checkout-Sitzung",
                details={"stripe_error": str(e)},
            )

    async def create_billing_portal_session(
        self,
        user: User,
        return_url: str,
    ) -> str:
        """Create a Stripe Billing Portal session.

        Args:
            user: User accessing portal
            return_url: URL to return to after portal

        Returns:
            Billing portal URL

        Raises:
            PaymentError: If portal creation fails
        """
        if not user.stripe_customer_id:
            raise PaymentError("Kein Stripe-Konto vorhanden")

        try:
            session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=return_url,
            )

            logger.info(f"Created billing portal session for user: {user.email}")
            return session.url

        except stripe.StripeError as e:
            logger.error(f"Failed to create billing portal session: {e}")
            raise PaymentError(
                "Fehler beim Öffnen des Kundenportals",
                details={"stripe_error": str(e)},
            )

    async def get_subscription(self, subscription_id: str) -> dict[str, Any] | None:
        """Get subscription details from Stripe.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Subscription data or None if not found
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "plan": self._get_plan_from_subscription(subscription),
            }
        except stripe.StripeError as e:
            logger.error(f"Failed to retrieve subscription: {e}")
            return None

    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> bool:
        """Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of billing period

        Returns:
            True if successful
        """
        try:
            if at_period_end:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
            else:
                stripe.Subscription.cancel(subscription_id)

            logger.info(f"Cancelled subscription: {subscription_id}")
            return True

        except stripe.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False

    def _get_plan_from_subscription(self, subscription: Subscription) -> PlanType:
        """Extract plan type from Stripe subscription."""
        if subscription.items.data:
            price_id = subscription.items.data[0].price.id
            return PRICE_PLAN_MAP.get(price_id, PlanType.FREE)
        return PlanType.FREE

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
    ) -> dict[str, Any] | None:
        """Verify Stripe webhook signature.

        Args:
            payload: Raw request body
            signature: Stripe-Signature header

        Returns:
            Event data if valid, None otherwise
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.stripe_webhook_secret,
            )
            return event
        except stripe.SignatureVerificationError as e:
            logger.warning(f"Invalid webhook signature: {e}")
            return None
        except Exception as e:
            logger.error(f"Webhook verification error: {e}")
            return None


class WebhookHandler:
    """Handler for Stripe webhook events."""

    def __init__(self, stripe_service: StripeService) -> None:
        """Initialize webhook handler."""
        self.stripe = stripe_service

    async def handle_event(self, event: dict[str, Any]) -> dict[str, str]:
        """Route webhook event to appropriate handler.

        Args:
            event: Stripe event data

        Returns:
            Handler response
        """
        event_type = event.get("type", "")
        data = event.get("data", {}).get("object", {})

        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.paid": self._handle_invoice_paid,
            "invoice.payment_failed": self._handle_payment_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            return await handler(data)

        logger.debug(f"Unhandled webhook event type: {event_type}")
        return {"status": "ignored", "event_type": event_type}

    async def _handle_checkout_completed(self, data: dict) -> dict[str, str]:
        """Handle successful checkout completion."""
        user_id = data.get("metadata", {}).get("user_id")
        subscription_id = data.get("subscription")
        customer_id = data.get("customer")

        logger.info(
            f"Checkout completed: user={user_id}, subscription={subscription_id}"
        )

        return {
            "status": "success",
            "action": "checkout_completed",
            "user_id": user_id,
            "subscription_id": subscription_id,
            "customer_id": customer_id,
        }

    async def _handle_subscription_created(self, data: dict) -> dict[str, str]:
        """Handle new subscription creation."""
        subscription_id = data.get("id")
        customer_id = data.get("customer")
        status = data.get("status")

        logger.info(
            f"Subscription created: {subscription_id}, status={status}"
        )

        return {
            "status": "success",
            "action": "subscription_created",
            "subscription_id": subscription_id,
            "customer_id": customer_id,
        }

    async def _handle_subscription_updated(self, data: dict) -> dict[str, str]:
        """Handle subscription update (plan change, etc.)."""
        subscription_id = data.get("id")
        status = data.get("status")
        cancel_at_period_end = data.get("cancel_at_period_end", False)

        logger.info(
            f"Subscription updated: {subscription_id}, status={status}, "
            f"cancel_at_period_end={cancel_at_period_end}"
        )

        return {
            "status": "success",
            "action": "subscription_updated",
            "subscription_id": subscription_id,
            "subscription_status": status,
        }

    async def _handle_subscription_deleted(self, data: dict) -> dict[str, str]:
        """Handle subscription cancellation/deletion."""
        subscription_id = data.get("id")
        customer_id = data.get("customer")

        logger.info(f"Subscription deleted: {subscription_id}")

        return {
            "status": "success",
            "action": "subscription_deleted",
            "subscription_id": subscription_id,
            "customer_id": customer_id,
        }

    async def _handle_invoice_paid(self, data: dict) -> dict[str, str]:
        """Handle successful invoice payment."""
        invoice_id = data.get("id")
        subscription_id = data.get("subscription")
        amount_paid = data.get("amount_paid", 0)

        logger.info(
            f"Invoice paid: {invoice_id}, subscription={subscription_id}, "
            f"amount={amount_paid/100:.2f}€"
        )

        return {
            "status": "success",
            "action": "invoice_paid",
            "invoice_id": invoice_id,
            "subscription_id": subscription_id,
        }

    async def _handle_payment_failed(self, data: dict) -> dict[str, str]:
        """Handle failed payment."""
        invoice_id = data.get("id")
        subscription_id = data.get("subscription")
        customer_id = data.get("customer")

        logger.warning(
            f"Payment failed: invoice={invoice_id}, subscription={subscription_id}"
        )

        # Email notification is sent in billing.py _process_webhook_result

        return {
            "status": "success",
            "action": "payment_failed",
            "invoice_id": invoice_id,
            "subscription_id": subscription_id,
            "customer_id": customer_id,
        }
