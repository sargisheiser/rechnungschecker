"""Integration CRUD service."""

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encryption_service
from app.models.integration import IntegrationSettings, IntegrationType

logger = logging.getLogger(__name__)


class IntegrationService:
    """Service for managing integration settings."""

    def __init__(self, db: AsyncSession):
        """Initialize integration service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_integration(
        self,
        user_id: UUID,
        integration_type: IntegrationType,
    ) -> IntegrationSettings | None:
        """Get a specific integration for a user.

        Args:
            user_id: User ID
            integration_type: Type of integration

        Returns:
            IntegrationSettings or None if not found
        """
        result = await self.db.execute(
            select(IntegrationSettings).where(
                IntegrationSettings.user_id == user_id,
                IntegrationSettings.integration_type == integration_type,
            )
        )
        return result.scalar_one_or_none()

    async def list_integrations(self, user_id: UUID) -> list[IntegrationSettings]:
        """Get all integrations for a user.

        Args:
            user_id: User ID

        Returns:
            List of IntegrationSettings
        """
        result = await self.db.execute(
            select(IntegrationSettings)
            .where(IntegrationSettings.user_id == user_id)
            .order_by(IntegrationSettings.integration_type)
        )
        return list(result.scalars().all())

    async def create_or_update_integration(
        self,
        user_id: UUID,
        integration_type: IntegrationType,
        config: dict,
        notify_on_valid: bool = True,
        notify_on_invalid: bool = True,
        notify_on_warning: bool = True,
    ) -> IntegrationSettings:
        """Create or update an integration.

        Args:
            user_id: User ID
            integration_type: Type of integration
            config: Configuration dict (api_key or webhook_url)
            notify_on_valid: Send notification on valid results
            notify_on_invalid: Send notification on invalid results
            notify_on_warning: Send notification on warnings

        Returns:
            Created or updated IntegrationSettings
        """
        existing = await self.get_integration(user_id, integration_type)

        encrypted_config = encryption_service.encrypt(json.dumps(config))

        if existing:
            existing.encrypted_config = encrypted_config
            existing.notify_on_valid = notify_on_valid
            existing.notify_on_invalid = notify_on_invalid
            existing.notify_on_warning = notify_on_warning
            existing.is_enabled = True
            await self.db.flush()
            logger.info(
                f"Integration updated: user={user_id}, type={integration_type.value}"
            )
            return existing

        integration = IntegrationSettings(
            user_id=user_id,
            integration_type=integration_type,
            encrypted_config=encrypted_config,
            notify_on_valid=notify_on_valid,
            notify_on_invalid=notify_on_invalid,
            notify_on_warning=notify_on_warning,
        )
        self.db.add(integration)
        await self.db.flush()

        logger.info(
            f"Integration created: user={user_id}, type={integration_type.value}"
        )
        return integration

    async def toggle_integration(
        self,
        user_id: UUID,
        integration_type: IntegrationType,
        is_enabled: bool,
    ) -> IntegrationSettings | None:
        """Enable or disable an integration.

        Args:
            user_id: User ID
            integration_type: Type of integration
            is_enabled: New enabled state

        Returns:
            Updated IntegrationSettings or None if not found
        """
        integration = await self.get_integration(user_id, integration_type)
        if integration:
            integration.is_enabled = is_enabled
            await self.db.flush()
            logger.info(
                f"Integration toggled: user={user_id}, type={integration_type.value}, "
                f"enabled={is_enabled}"
            )
        return integration

    async def delete_integration(
        self,
        user_id: UUID,
        integration_type: IntegrationType,
    ) -> bool:
        """Delete an integration.

        Args:
            user_id: User ID
            integration_type: Type of integration

        Returns:
            True if deleted, False if not found
        """
        integration = await self.get_integration(user_id, integration_type)
        if integration:
            await self.db.delete(integration)
            await self.db.flush()
            logger.info(
                f"Integration deleted: user={user_id}, type={integration_type.value}"
            )
            return True
        return False

    @staticmethod
    def get_config_hint(integration: IntegrationSettings) -> str | None:
        """Create a masked hint showing what's configured.

        Args:
            integration: The integration settings

        Returns:
            Masked config hint or None
        """
        try:
            config = json.loads(
                encryption_service.decrypt(integration.encrypted_config)
            )
            if "api_key" in config:
                key = config["api_key"]
                if len(key) > 12:
                    return f"api_key: {key[:4]}...{key[-4:]}"
                return "api_key: ***"
            elif "webhook_url" in config:
                url = config["webhook_url"]
                # Show domain only
                from urllib.parse import urlparse

                parsed = urlparse(url)
                return f"webhook_url: ...{parsed.netloc}/..."
        except Exception:
            pass
        return None
