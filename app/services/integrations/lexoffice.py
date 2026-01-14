"""Lexoffice API integration service."""

import json
import logging
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encryption_service
from app.models.integration import IntegrationSettings, IntegrationType
from app.schemas.integration import LexofficeInvoiceList

logger = logging.getLogger(__name__)

# Lexoffice API base URL
LEXOFFICE_API_BASE = "https://api.lexoffice.io/v1"


class LexofficeService:
    """Service for Lexoffice API integration."""

    TIMEOUT_SECONDS = 30

    def __init__(self, db: AsyncSession | None = None):
        """Initialize Lexoffice service.

        Args:
            db: Optional database session
        """
        self.db = db

    def with_db(self, db: AsyncSession) -> "LexofficeService":
        """Return a new instance with database session.

        Args:
            db: Database session

        Returns:
            New LexofficeService instance
        """
        return LexofficeService(db)

    async def get_user_config(self, user_id: UUID) -> dict | None:
        """Get decrypted Lexoffice config for user.

        Args:
            user_id: User ID

        Returns:
            Decrypted config dict or None if not configured
        """
        if self.db is None:
            raise ValueError("Database session required")

        result = await self.db.execute(
            select(IntegrationSettings).where(
                IntegrationSettings.user_id == user_id,
                IntegrationSettings.integration_type == IntegrationType.LEXOFFICE,
                IntegrationSettings.is_enabled == True,  # noqa: E712
            )
        )
        integration = result.scalar_one_or_none()

        if not integration:
            return None

        return json.loads(encryption_service.decrypt(integration.encrypted_config))

    async def list_invoices(
        self,
        user_id: UUID,
        page: int = 0,
        size: int = 25,
        status: str | None = None,
    ) -> LexofficeInvoiceList:
        """Fetch invoices from Lexoffice API.

        Args:
            user_id: User ID
            page: Page number (0-based)
            size: Page size
            status: Optional status filter

        Returns:
            LexofficeInvoiceList with invoice data

        Raises:
            ValueError: If Lexoffice not configured
            httpx.HTTPStatusError: If API request fails
        """
        config = await self.get_user_config(user_id)
        if not config:
            raise ValueError("Lexoffice-Integration nicht konfiguriert")

        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Accept": "application/json",
        }

        params = {
            "page": page,
            "size": size,
            "voucherType": "invoice",
        }
        if status:
            params["voucherStatus"] = status

        async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
            response = await client.get(
                f"{LEXOFFICE_API_BASE}/voucherlist",
                headers=headers,
                params=params,
            )
            response.raise_for_status()

        return LexofficeInvoiceList(**response.json())

    async def get_invoice(self, user_id: UUID, invoice_id: str) -> dict:
        """Fetch a single invoice from Lexoffice.

        Args:
            user_id: User ID
            invoice_id: Lexoffice invoice ID

        Returns:
            Invoice data dict

        Raises:
            ValueError: If Lexoffice not configured
            httpx.HTTPStatusError: If API request fails
        """
        config = await self.get_user_config(user_id)
        if not config:
            raise ValueError("Lexoffice-Integration nicht konfiguriert")

        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
            response = await client.get(
                f"{LEXOFFICE_API_BASE}/invoices/{invoice_id}",
                headers=headers,
            )
            response.raise_for_status()

        return response.json()

    async def get_invoice_document(
        self,
        user_id: UUID,
        invoice_id: str,
    ) -> bytes:
        """Fetch invoice document (PDF or XML) from Lexoffice.

        Note: Lexoffice primarily provides PDF documents. XRechnung XML
        export may require the invoice to be marked as XRechnung-compatible.

        Args:
            user_id: User ID
            invoice_id: Lexoffice invoice ID

        Returns:
            Document content bytes

        Raises:
            ValueError: If Lexoffice not configured
            httpx.HTTPStatusError: If API request fails
        """
        config = await self.get_user_config(user_id)
        if not config:
            raise ValueError("Lexoffice-Integration nicht konfiguriert")

        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Accept": "application/pdf",
        }

        async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
            # Get document file ID first
            response = await client.get(
                f"{LEXOFFICE_API_BASE}/invoices/{invoice_id}/document",
                headers=headers,
            )
            response.raise_for_status()

            document_info = response.json()
            document_file_id = document_info.get("documentFileId")

            if not document_file_id:
                raise ValueError("Kein Dokument fuer diese Rechnung verfuegbar")

            # Download the document
            response = await client.get(
                f"{LEXOFFICE_API_BASE}/files/{document_file_id}",
                headers=headers,
            )
            response.raise_for_status()

        return response.content

    async def test_connection(self, api_key: str) -> bool:
        """Test if the API key is valid.

        Args:
            api_key: Lexoffice API key to test

        Returns:
            True if connection successful
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{LEXOFFICE_API_BASE}/profile",
                    headers=headers,
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Lexoffice connection test failed: {e}")
            return False


# Singleton instance (without DB session)
lexoffice_service = LexofficeService()
