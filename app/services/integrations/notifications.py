"""Unified notification service for Slack and Teams."""

import json
import logging
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encryption_service
from app.models.integration import IntegrationSettings, IntegrationType

logger = logging.getLogger(__name__)


class NotificationService:
    """Unified notification service for Slack and Teams."""

    TIMEOUT_SECONDS = 10

    def __init__(self, db: AsyncSession | None = None):
        """Initialize notification service.

        Args:
            db: Optional database session
        """
        self.db = db

    def with_db(self, db: AsyncSession) -> "NotificationService":
        """Return a new instance with database session.

        Args:
            db: Database session

        Returns:
            New NotificationService instance
        """
        return NotificationService(db)

    async def _get_enabled_integrations(
        self,
        user_id: UUID,
        integration_types: list[IntegrationType],
    ) -> list[IntegrationSettings]:
        """Get all enabled notification integrations for a user.

        Args:
            user_id: User ID
            integration_types: Types to fetch

        Returns:
            List of enabled integrations
        """
        if self.db is None:
            raise ValueError("Database session required")

        result = await self.db.execute(
            select(IntegrationSettings).where(
                IntegrationSettings.user_id == user_id,
                IntegrationSettings.integration_type.in_(integration_types),
                IntegrationSettings.is_enabled == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    def _should_notify(
        self,
        integration: IntegrationSettings,
        is_valid: bool,
        warning_count: int,
    ) -> bool:
        """Check if notification should be sent based on settings.

        Args:
            integration: Integration settings
            is_valid: Whether validation passed
            warning_count: Number of warnings

        Returns:
            True if notification should be sent
        """
        if is_valid and warning_count == 0:
            return integration.notify_on_valid
        elif is_valid and warning_count > 0:
            return integration.notify_on_warning
        else:
            return integration.notify_on_invalid

    def _build_slack_message(
        self,
        file_name: str,
        is_valid: bool,
        error_count: int,
        warning_count: int,
        info_count: int,
        validation_id: UUID,
    ) -> dict:
        """Build Slack message payload in German.

        Args:
            file_name: Name of validated file
            is_valid: Whether validation passed
            error_count: Number of errors
            warning_count: Number of warnings
            info_count: Number of info messages
            validation_id: Validation ID

        Returns:
            Slack message payload dict
        """
        if is_valid and warning_count == 0:
            status_emoji = ":white_check_mark:"
            status_text = "Gueltig"
            color = "#36a64f"  # Green
        elif is_valid and warning_count > 0:
            status_emoji = ":warning:"
            status_text = "Gueltig mit Warnungen"
            color = "#f2c744"  # Yellow
        else:
            status_emoji = ":x:"
            status_text = "Ungueltig"
            color = "#dc3545"  # Red

        return {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{status_emoji} Validierungsergebnis",
                            },
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Datei:*\n{file_name}"},
                                {"type": "mrkdwn", "text": f"*Status:*\n{status_text}"},
                                {"type": "mrkdwn", "text": f"*Fehler:*\n{error_count}"},
                                {"type": "mrkdwn", "text": f"*Warnungen:*\n{warning_count}"},
                            ],
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Validierungs-ID: `{validation_id}`",
                                }
                            ],
                        },
                    ],
                }
            ]
        }

    def _build_teams_adaptive_card(
        self,
        file_name: str,
        is_valid: bool,
        error_count: int,
        warning_count: int,
        info_count: int,
        validation_id: UUID,
    ) -> dict:
        """Build Teams MessageCard payload in German.

        Args:
            file_name: Name of validated file
            is_valid: Whether validation passed
            error_count: Number of errors
            warning_count: Number of warnings
            info_count: Number of info messages
            validation_id: Validation ID

        Returns:
            Teams MessageCard payload dict
        """
        if is_valid and warning_count == 0:
            status_text = "Gueltig"
            theme_color = "00FF00"  # Green
        elif is_valid and warning_count > 0:
            status_text = "Gueltig mit Warnungen"
            theme_color = "FFD700"  # Yellow
        else:
            status_text = "Ungueltig"
            theme_color = "FF0000"  # Red

        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": f"Validierungsergebnis: {file_name}",
            "sections": [
                {
                    "activityTitle": "Validierungsergebnis",
                    "facts": [
                        {"name": "Datei", "value": file_name},
                        {"name": "Status", "value": status_text},
                        {"name": "Fehler", "value": str(error_count)},
                        {"name": "Warnungen", "value": str(warning_count)},
                        {"name": "Hinweise", "value": str(info_count)},
                    ],
                    "markdown": True,
                }
            ],
            "potentialAction": [],
        }

    async def send_validation_notification(
        self,
        user_id: UUID,
        validation_id: UUID,
        file_name: str,
        is_valid: bool,
        error_count: int,
        warning_count: int,
        info_count: int,
    ) -> list[tuple[IntegrationType, bool]]:
        """Send notifications to all enabled integrations.

        Args:
            user_id: User ID
            validation_id: Validation ID
            file_name: Name of validated file
            is_valid: Whether validation passed
            error_count: Number of errors
            warning_count: Number of warnings
            info_count: Number of info messages

        Returns:
            List of (integration_type, success) tuples
        """
        if self.db is None:
            raise ValueError("Database session required")

        integrations = await self._get_enabled_integrations(
            user_id,
            [IntegrationType.SLACK, IntegrationType.TEAMS],
        )

        results = []

        for integration in integrations:
            if not self._should_notify(integration, is_valid, warning_count):
                continue

            config = json.loads(
                encryption_service.decrypt(integration.encrypted_config)
            )
            webhook_url = config.get("webhook_url")

            if not webhook_url:
                continue

            try:
                if integration.integration_type == IntegrationType.SLACK:
                    payload = self._build_slack_message(
                        file_name,
                        is_valid,
                        error_count,
                        warning_count,
                        info_count,
                        validation_id,
                    )
                else:  # Teams
                    payload = self._build_teams_adaptive_card(
                        file_name,
                        is_valid,
                        error_count,
                        warning_count,
                        info_count,
                        validation_id,
                    )

                async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                    response = await client.post(webhook_url, json=payload)
                    success = response.status_code in (200, 201, 204)

                # Update statistics
                integration.record_request(success)

                results.append((integration.integration_type, success))

                if success:
                    logger.info(
                        f"Notification sent: user={user_id}, "
                        f"type={integration.integration_type.value}"
                    )
                else:
                    logger.warning(
                        f"Notification failed: user={user_id}, "
                        f"type={integration.integration_type.value}, "
                        f"status={response.status_code}"
                    )

            except Exception as e:
                integration.record_request(success=False)
                results.append((integration.integration_type, False))
                logger.error(
                    f"Notification error: user={user_id}, "
                    f"type={integration.integration_type.value}, error={e}"
                )

        return results

    async def test_webhook(
        self,
        webhook_url: str,
        integration_type: IntegrationType,
    ) -> bool:
        """Send a test notification to verify webhook configuration.

        Args:
            webhook_url: Webhook URL to test
            integration_type: Type of integration (SLACK or TEAMS)

        Returns:
            True if test succeeded
        """
        try:
            if integration_type == IntegrationType.SLACK:
                payload = {
                    "text": "RechnungsChecker Testbenachrichtigung - "
                    "Ihre Integration wurde erfolgreich eingerichtet!"
                }
            else:  # Teams
                payload = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "0076D7",
                    "summary": "RechnungsChecker Test",
                    "sections": [
                        {
                            "activityTitle": "Testbenachrichtigung",
                            "text": "Ihre RechnungsChecker-Integration wurde "
                            "erfolgreich eingerichtet!",
                        }
                    ],
                }

            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.post(webhook_url, json=payload)
                return response.status_code in (200, 201, 204)

        except Exception as e:
            logger.error(f"Webhook test failed: {e}")
            return False


# Singleton instance (without DB session)
notification_service = NotificationService()
