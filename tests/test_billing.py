"""Tests for billing endpoints and schemas."""

import pytest
from httpx import AsyncClient

from app.schemas.billing import (
    PLAN_DEFINITIONS,
    PlanTier,
    get_all_plans,
    get_plan_info,
)


class TestPlanDefinitions:
    """Tests for plan definitions."""

    def test_all_plans_defined(self) -> None:
        """Test that all plan tiers have definitions."""
        for tier in PlanTier:
            assert tier in PLAN_DEFINITIONS
            plan = PLAN_DEFINITIONS[tier]
            assert plan.id == tier
            assert plan.name
            assert plan.description

    def test_get_all_plans(self) -> None:
        """Test getting all plans."""
        plans = get_all_plans()
        assert len(plans) == 4  # Free, Starter, Pro, Steuerberater

        # Check order
        plan_ids = [p.id for p in plans]
        assert PlanTier.FREE in plan_ids
        assert PlanTier.STARTER in plan_ids
        assert PlanTier.PRO in plan_ids
        assert PlanTier.STEUERBERATER in plan_ids

    def test_get_plan_info(self) -> None:
        """Test getting specific plan info."""
        starter = get_plan_info(PlanTier.STARTER)
        assert starter.id == PlanTier.STARTER
        assert starter.name == "Starter"
        assert starter.price_monthly == 29
        assert starter.price_annual == 279

    def test_free_plan_features(self) -> None:
        """Test free plan has expected limitations."""
        free = get_plan_info(PlanTier.FREE)
        assert free.price_monthly == 0
        assert free.price_annual == 0
        assert free.features.validations_per_month == 5
        assert free.features.conversions_per_month == 0
        assert free.features.api_access is False
        assert free.features.batch_upload is False

    def test_starter_plan_features(self) -> None:
        """Test starter plan features."""
        starter = get_plan_info(PlanTier.STARTER)
        assert starter.features.validations_per_month == 100
        assert starter.features.conversions_per_month == 20
        assert starter.features.batch_upload is True
        assert starter.features.api_access is False
        assert starter.popular is True

    def test_pro_plan_features(self) -> None:
        """Test professional plan features."""
        pro = get_plan_info(PlanTier.PRO)
        assert pro.features.validations_per_month is None  # Unlimited
        assert pro.features.conversions_per_month == 100
        assert pro.features.api_access is True
        assert pro.features.api_calls_per_month == 1000

    def test_steuerberater_plan_features(self) -> None:
        """Test Steuerberater plan features."""
        stb = get_plan_info(PlanTier.STEUERBERATER)
        assert stb.features.validations_per_month is None  # Unlimited
        assert stb.features.conversions_per_month == 500
        assert stb.features.multi_client is True
        assert stb.features.max_clients == 100
        assert stb.features.support_level == "phone"

    def test_annual_discount(self) -> None:
        """Test annual pricing includes discount."""
        starter = get_plan_info(PlanTier.STARTER)
        # Annual should be less than 12x monthly
        assert starter.price_annual < starter.price_monthly * 12

        pro = get_plan_info(PlanTier.PRO)
        assert pro.price_annual < pro.price_monthly * 12


class TestBillingEndpoints:
    """Tests for billing API endpoints."""

    @pytest.mark.asyncio
    async def test_get_plans(self, async_client: AsyncClient) -> None:
        """Test getting all plans without authentication."""
        response = await async_client.get("/api/v1/billing/plans")

        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) == 4

    @pytest.mark.asyncio
    async def test_get_specific_plan(self, async_client: AsyncClient) -> None:
        """Test getting a specific plan."""
        response = await async_client.get("/api/v1/billing/plans/starter")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "starter"
        assert data["name"] == "Starter"
        assert "features" in data

    @pytest.mark.asyncio
    async def test_get_invalid_plan(self, async_client: AsyncClient) -> None:
        """Test getting a non-existent plan."""
        response = await async_client.get("/api/v1/billing/plans/invalid")

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_subscription_requires_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Test subscription endpoint requires authentication."""
        response = await async_client.get("/api/v1/billing/subscription")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_checkout_requires_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Test checkout endpoint requires authentication."""
        response = await async_client.post(
            "/api/v1/billing/checkout",
            json={
                "plan": "starter",
                "annual": False,
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_portal_requires_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Test billing portal endpoint requires authentication."""
        response = await async_client.post(
            "/api/v1/billing/portal",
            json={
                "return_url": "https://example.com/dashboard",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_cancel_requires_auth(
        self, async_client: AsyncClient
    ) -> None:
        """Test cancel endpoint requires authentication."""
        response = await async_client.post("/api/v1/billing/cancel")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_webhook_missing_signature(
        self, async_client: AsyncClient
    ) -> None:
        """Test webhook rejects requests without signature."""
        response = await async_client.post(
            "/api/v1/billing/webhook",
            content=b"{}",
        )

        assert response.status_code == 400
        assert "Stripe-Signature" in response.json()["detail"]


class TestPlanTierEnum:
    """Tests for PlanTier enumeration."""

    def test_plan_tier_values(self) -> None:
        """Test plan tier string values."""
        assert PlanTier.FREE.value == "free"
        assert PlanTier.STARTER.value == "starter"
        assert PlanTier.PRO.value == "pro"
        assert PlanTier.STEUERBERATER.value == "steuerberater"

    def test_plan_tier_from_string(self) -> None:
        """Test creating PlanTier from string."""
        assert PlanTier("free") == PlanTier.FREE
        assert PlanTier("starter") == PlanTier.STARTER
        assert PlanTier("pro") == PlanTier.PRO
        assert PlanTier("steuerberater") == PlanTier.STEUERBERATER

    def test_invalid_plan_tier(self) -> None:
        """Test invalid plan tier raises error."""
        with pytest.raises(ValueError):
            PlanTier("invalid")
