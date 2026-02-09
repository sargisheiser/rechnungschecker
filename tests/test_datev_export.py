"""Tests for DATEV Buchungsstapel export."""

import json
import uuid
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.models.extracted_invoice import ExtractedInvoiceData
from app.models.user import User
from app.models.validation import FileType, ValidationLog
from app.schemas.datev import (
    DATEVBuchung,
    DATEVConfig,
    Kontenrahmen,
)
from app.services.export.datev import DATEVExportService
from app.services.export.kontenrahmen import (
    SKR03_ACCOUNTS,
    SKR04_ACCOUNTS,
    get_accounts,
    get_bu_schluessel,
    get_debitor_account,
    get_kreditor_account,
    get_revenue_account,
)


class TestKontenrahmenMapping:
    """Tests for SKR03/SKR04 account mapping."""

    def test_skr03_accounts_exist(self) -> None:
        """Test that SKR03 accounts are defined."""
        assert "debitor" in SKR03_ACCOUNTS
        assert "kreditor" in SKR03_ACCOUNTS
        assert "umsatz_19" in SKR03_ACCOUNTS
        assert "umsatz_7" in SKR03_ACCOUNTS
        assert "umsatz_0" in SKR03_ACCOUNTS

    def test_skr04_accounts_exist(self) -> None:
        """Test that SKR04 accounts are defined."""
        assert "debitor" in SKR04_ACCOUNTS
        assert "kreditor" in SKR04_ACCOUNTS
        assert "umsatz_19" in SKR04_ACCOUNTS
        assert "umsatz_7" in SKR04_ACCOUNTS
        assert "umsatz_0" in SKR04_ACCOUNTS

    def test_get_accounts_skr03(self) -> None:
        """Test getting SKR03 accounts."""
        accounts = get_accounts(Kontenrahmen.SKR03)
        assert accounts["debitor"].konto == "1400"
        assert accounts["kreditor"].konto == "1600"
        assert accounts["umsatz_19"].konto == "8400"

    def test_get_accounts_skr04(self) -> None:
        """Test getting SKR04 accounts."""
        accounts = get_accounts(Kontenrahmen.SKR04)
        assert accounts["debitor"].konto == "1200"
        assert accounts["kreditor"].konto == "3300"
        assert accounts["umsatz_19"].konto == "4400"

    def test_bu_schluessel_19_percent(self) -> None:
        """Test BU-Schluessel for 19% VAT."""
        assert get_bu_schluessel(Decimal("19")) == 9

    def test_bu_schluessel_7_percent(self) -> None:
        """Test BU-Schluessel for 7% VAT."""
        assert get_bu_schluessel(Decimal("7")) == 8

    def test_bu_schluessel_0_percent(self) -> None:
        """Test BU-Schluessel for 0% VAT."""
        assert get_bu_schluessel(Decimal("0")) == 0

    def test_bu_schluessel_other_rate(self) -> None:
        """Test BU-Schluessel for other VAT rates defaults to 0."""
        assert get_bu_schluessel(Decimal("5")) == 0
        assert get_bu_schluessel(Decimal("16")) == 0

    def test_revenue_account_19_percent(self) -> None:
        """Test revenue account for 19% VAT."""
        account = get_revenue_account(Kontenrahmen.SKR03, Decimal("19"))
        assert account.konto == "8400"

    def test_revenue_account_7_percent(self) -> None:
        """Test revenue account for 7% VAT."""
        account = get_revenue_account(Kontenrahmen.SKR03, Decimal("7"))
        assert account.konto == "8300"

    def test_revenue_account_0_percent(self) -> None:
        """Test revenue account for 0% VAT."""
        account = get_revenue_account(Kontenrahmen.SKR03, Decimal("0"))
        assert account.konto == "8120"

    def test_revenue_account_eu_delivery(self) -> None:
        """Test revenue account for EU delivery."""
        account = get_revenue_account(
            Kontenrahmen.SKR03, Decimal("0"), is_eu_delivery=True
        )
        assert account.konto == "8125"

    def test_revenue_account_export(self) -> None:
        """Test revenue account for export."""
        account = get_revenue_account(
            Kontenrahmen.SKR03, Decimal("0"), is_export=True
        )
        assert account.konto == "8120"

    def test_debitor_account_default(self) -> None:
        """Test default debtor account."""
        assert get_debitor_account(Kontenrahmen.SKR03) == "1400"
        assert get_debitor_account(Kontenrahmen.SKR04) == "1200"

    def test_debitor_account_custom(self) -> None:
        """Test custom debtor account."""
        assert get_debitor_account(Kontenrahmen.SKR03, "10001") == "10001"

    def test_kreditor_account_default(self) -> None:
        """Test default creditor account."""
        assert get_kreditor_account(Kontenrahmen.SKR03) == "1600"
        assert get_kreditor_account(Kontenrahmen.SKR04) == "3300"

    def test_kreditor_account_custom(self) -> None:
        """Test custom creditor account."""
        assert get_kreditor_account(Kontenrahmen.SKR03, "70001") == "70001"


class TestDATEVSchemas:
    """Tests for DATEV Pydantic schemas."""

    def test_datev_config_defaults(self) -> None:
        """Test DATEVConfig default values."""
        config = DATEVConfig()
        assert config.kontenrahmen == Kontenrahmen.SKR03
        assert config.debitor_konto == "1400"
        assert config.kreditor_konto == "1600"
        assert config.berater_nummer == ""
        assert config.mandanten_nummer == ""
        assert config.buchungstyp == "Einnahme"

    def test_datev_config_custom_values(self) -> None:
        """Test DATEVConfig with custom values."""
        config = DATEVConfig(
            kontenrahmen=Kontenrahmen.SKR04,
            debitor_konto="1200",
            kreditor_konto="3300",
            berater_nummer="12345",
            mandanten_nummer="67890",
        )
        assert config.kontenrahmen == Kontenrahmen.SKR04
        assert config.debitor_konto == "1200"
        assert config.berater_nummer == "12345"

    def test_datev_buchung_creation(self) -> None:
        """Test DATEVBuchung creation."""
        buchung = DATEVBuchung(
            umsatz=Decimal("1190.00"),
            soll_haben="S",
            konto="1400",
            gegenkonto="8400",
            bu_schluessel=9,
            belegdatum=date(2024, 1, 15),
            belegnummer="RE-2024-001",
            buchungstext="Beratungsleistung",
        )
        assert buchung.umsatz == Decimal("1190.00")
        assert buchung.soll_haben == "S"
        assert buchung.waehrung == "EUR"
        assert buchung.bu_schluessel == 9

    def test_datev_buchung_belegnummer_max_length(self) -> None:
        """Test that belegnummer is limited to 36 characters."""
        buchung = DATEVBuchung(
            umsatz=Decimal("100.00"),
            soll_haben="S",
            konto="1400",
            gegenkonto="8400",
            belegdatum=date.today(),
            belegnummer="A" * 36,
            buchungstext="Test",
        )
        assert len(buchung.belegnummer) == 36

    def test_datev_buchung_buchungstext_max_length(self) -> None:
        """Test that buchungstext is limited to 60 characters."""
        buchung = DATEVBuchung(
            umsatz=Decimal("100.00"),
            soll_haben="S",
            konto="1400",
            gegenkonto="8400",
            belegdatum=date.today(),
            belegnummer="RE-001",
            buchungstext="B" * 60,
        )
        assert len(buchung.buchungstext) == 60

    def test_kontenrahmen_enum(self) -> None:
        """Test Kontenrahmen enum values."""
        assert Kontenrahmen.SKR03.value == "SKR03"
        assert Kontenrahmen.SKR04.value == "SKR04"


class TestDATEVExportEndpoint:
    """Tests for DATEV Buchungsstapel export endpoint."""

    @pytest.mark.asyncio
    async def test_export_unauthorized(self, async_client: AsyncClient) -> None:
        """Test export without authentication fails."""
        response = await async_client.get(
            "/api/v1/export/datev/buchungsstapel",
            params={"validation_ids": str(uuid.uuid4())},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_export_requires_steuerberater_plan(
        self, async_client: AsyncClient, test_user: tuple[User, str]
    ) -> None:
        """Test export requires Steuerberater plan."""
        user, token = test_user
        response = await async_client.get(
            "/api/v1/export/datev/buchungsstapel",
            params={"validation_ids": str(uuid.uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_export_empty_validation_ids(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test export with empty validation IDs fails."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/datev/buchungsstapel",
            headers={"Authorization": f"Bearer {token}"},
        )
        # FastAPI returns 422 for missing required query param
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_export_with_nonexistent_validation(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test export with non-existent validation ID returns empty file."""
        user, token = test_steuerberater_user
        validation_id = uuid.uuid4()
        response = await async_client.get(
            "/api/v1/export/datev/buchungsstapel",
            params={"validation_ids": str(validation_id)},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_export_with_skr03(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test export with SKR03 Kontenrahmen."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/datev/buchungsstapel",
            params={
                "validation_ids": str(uuid.uuid4()),
                "kontenrahmen": "SKR03",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_with_skr04(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test export with SKR04 Kontenrahmen."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/datev/buchungsstapel",
            params={
                "validation_ids": str(uuid.uuid4()),
                "kontenrahmen": "SKR04",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_with_custom_debitor(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test export with custom debitor account."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/datev/buchungsstapel",
            params={
                "validation_ids": str(uuid.uuid4()),
                "debitor_konto": "10001",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_with_berater_nummer(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test export with DATEV consultant number."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/datev/buchungsstapel",
            params={
                "validation_ids": str(uuid.uuid4()),
                "berater_nummer": "12345",
                "mandanten_nummer": "67890",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_csv_format(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test that exported CSV has correct format."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/datev/buchungsstapel",
            params={"validation_ids": str(uuid.uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        content = response.content.decode("utf-8-sig")

        # Check EXTF header
        lines = content.strip().split("\n")
        assert len(lines) >= 2  # Header + column headers
        assert '"EXTF"' in lines[0]
        assert "Buchungsstapel" in lines[0]

        # Check column headers are semicolon separated
        assert ";" in lines[1]

    @pytest.mark.asyncio
    async def test_export_filename(
        self, async_client: AsyncClient, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test that exported file has correct filename."""
        user, token = test_steuerberater_user
        response = await async_client.get(
            "/api/v1/export/datev/buchungsstapel",
            params={"validation_ids": str(uuid.uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        content_disposition = response.headers.get("content-disposition", "")
        assert "EXTF_Buchungsstapel" in content_disposition
        assert ".csv" in content_disposition

    @pytest.mark.asyncio
    async def test_export_multiple_validation_ids(
        self,
        async_client: AsyncClient,
        test_steuerberater_user: tuple[User, str],
        db_session,
    ) -> None:
        """Test export with multiple validation IDs."""
        user, token = test_steuerberater_user

        # Create test validations
        validations = []
        for i in range(3):
            validation = ValidationLog(
                id=uuid.uuid4(),
                user_id=user.id,
                file_name=f"test_invoice_{i}.xml",
                file_type=FileType.XRECHNUNG,
                file_hash=f"hash{i}" * 8,
                file_size_bytes=1000,
                is_valid=True,
                error_count=0,
                warning_count=0,
                info_count=0,
                processing_time_ms=100,
                validator_version="1.0.0",
            )
            db_session.add(validation)
            validations.append(validation)

        await db_session.commit()

        # Export all validations
        validation_ids = [str(v.id) for v in validations]
        response = await async_client.get(
            "/api/v1/export/datev/buchungsstapel",
            params={"validation_ids": validation_ids},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        content = response.content.decode("utf-8-sig")
        lines = content.strip().split("\n")

        # Should have header + column headers + 3 data rows
        assert len(lines) >= 5


class TestDATEVExportService:
    """Tests for DATEV export service."""

    @pytest.mark.asyncio
    async def test_export_buchungsstapel_empty(
        self, db_session, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting empty buchungsstapel."""
        from app.services.export.datev import DATEVExportService

        user, _ = test_steuerberater_user
        service = DATEVExportService(db_session)

        config = DATEVConfig()
        csv_content, count, total = await service.export_buchungsstapel(
            user_id=user.id,
            validation_ids=[uuid.uuid4()],
            config=config,
        )

        assert count == 0
        assert total == Decimal("0")
        assert '"EXTF"' in csv_content

    @pytest.mark.asyncio
    async def test_export_buchungsstapel_with_validations(
        self, db_session, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test exporting buchungsstapel with validations."""
        from app.services.export.datev import DATEVExportService

        user, _ = test_steuerberater_user

        # Create test validation
        validation = ValidationLog(
            id=uuid.uuid4(),
            user_id=user.id,
            file_name="test_invoice.xml",
            file_type=FileType.XRECHNUNG,
            file_hash="a" * 64,
            file_size_bytes=1000,
            is_valid=True,
            error_count=0,
            warning_count=0,
            info_count=0,
            processing_time_ms=100,
            validator_version="1.0.0",
        )
        db_session.add(validation)
        await db_session.commit()

        service = DATEVExportService(db_session)
        config = DATEVConfig()

        csv_content, count, total = await service.export_buchungsstapel(
            user_id=user.id,
            validation_ids=[validation.id],
            config=config,
        )

        assert count == 1
        assert '"EXTF"' in csv_content
        assert "test_invoice" in csv_content

    @pytest.mark.asyncio
    async def test_export_only_valid_validations(
        self, db_session, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test that only valid validations are exported."""
        from app.services.export.datev import DATEVExportService

        user, _ = test_steuerberater_user

        # Create valid validation
        valid_validation = ValidationLog(
            id=uuid.uuid4(),
            user_id=user.id,
            file_name="valid_invoice.xml",
            file_type=FileType.XRECHNUNG,
            file_hash="v" * 64,
            file_size_bytes=1000,
            is_valid=True,
            error_count=0,
            warning_count=0,
            info_count=0,
            processing_time_ms=100,
            validator_version="1.0.0",
        )

        # Create invalid validation
        invalid_validation = ValidationLog(
            id=uuid.uuid4(),
            user_id=user.id,
            file_name="invalid_invoice.xml",
            file_type=FileType.XRECHNUNG,
            file_hash="i" * 64,
            file_size_bytes=1000,
            is_valid=False,
            error_count=5,
            warning_count=0,
            info_count=0,
            processing_time_ms=100,
            validator_version="1.0.0",
        )

        db_session.add(valid_validation)
        db_session.add(invalid_validation)
        await db_session.commit()

        service = DATEVExportService(db_session)
        config = DATEVConfig()

        csv_content, count, _ = await service.export_buchungsstapel(
            user_id=user.id,
            validation_ids=[valid_validation.id, invalid_validation.id],
            config=config,
        )

        # Only valid validation should be exported
        assert count == 1
        assert "valid_invoice" in csv_content
        assert "invalid_invoice" not in csv_content


class TestMultiRateDATEVExport:
    """Tests for multi-VAT rate DATEV export."""

    @pytest.mark.asyncio
    async def test_multi_rate_generates_multiple_bookings(
        self, db_session, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test that multi-rate invoice generates multiple bookings."""
        user, _ = test_steuerberater_user

        # Create test validation
        validation = ValidationLog(
            id=uuid.uuid4(),
            user_id=user.id,
            file_name="multi_rate_invoice.xml",
            file_type=FileType.XRECHNUNG,
            file_hash="m" * 64,
            file_size_bytes=1000,
            is_valid=True,
            error_count=0,
            warning_count=0,
            info_count=0,
            processing_time_ms=100,
            validator_version="1.0.0",
        )
        db_session.add(validation)
        await db_session.flush()

        # Create extracted data with multi-rate breakdown
        vat_breakdown = json.dumps([
            {"rate": "19", "net_amount": "100.00", "vat_amount": "19.00"},
            {"rate": "7", "net_amount": "50.00", "vat_amount": "3.50"},
        ])
        extracted = ExtractedInvoiceData(
            validation_id=validation.id,
            invoice_number="MULTI-2024-001",
            invoice_date=date(2024, 6, 15),
            net_amount=Decimal("150.00"),
            vat_amount=Decimal("22.50"),
            gross_amount=Decimal("172.50"),
            currency="EUR",
            vat_rate=Decimal("19.00"),
            seller_name="Multi-Rate Supplier",
            vat_breakdown=vat_breakdown,
        )
        db_session.add(extracted)
        await db_session.commit()

        # Export to DATEV
        service = DATEVExportService(db_session)
        config = DATEVConfig(kontenrahmen=Kontenrahmen.SKR03)

        csv_content, count, total = await service.export_buchungsstapel(
            user_id=user.id,
            validation_ids=[validation.id],
            config=config,
        )

        # Should have 2 bookings (one per VAT rate)
        assert count == 2
        # Total should be sum of net amounts
        assert total == Decimal("150.00")

    @pytest.mark.asyncio
    async def test_multi_rate_correct_accounts(
        self, db_session, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test that multi-rate bookings use correct revenue accounts."""
        user, _ = test_steuerberater_user

        validation = ValidationLog(
            id=uuid.uuid4(),
            user_id=user.id,
            file_name="multi_rate_invoice.xml",
            file_type=FileType.XRECHNUNG,
            file_hash="n" * 64,
            file_size_bytes=1000,
            is_valid=True,
            error_count=0,
            warning_count=0,
            info_count=0,
            processing_time_ms=100,
            validator_version="1.0.0",
        )
        db_session.add(validation)
        await db_session.flush()

        vat_breakdown = json.dumps([
            {"rate": "19", "net_amount": "100.00", "vat_amount": "19.00"},
            {"rate": "7", "net_amount": "50.00", "vat_amount": "3.50"},
        ])
        extracted = ExtractedInvoiceData(
            validation_id=validation.id,
            invoice_number="MULTI-2024-002",
            invoice_date=date(2024, 6, 20),
            net_amount=Decimal("150.00"),
            vat_amount=Decimal("22.50"),
            gross_amount=Decimal("172.50"),
            currency="EUR",
            vat_rate=Decimal("19.00"),
            seller_name="Multi-Rate Supplier",
            vat_breakdown=vat_breakdown,
        )
        db_session.add(extracted)
        await db_session.commit()

        service = DATEVExportService(db_session)
        config = DATEVConfig(kontenrahmen=Kontenrahmen.SKR03)

        csv_content, count, _ = await service.export_buchungsstapel(
            user_id=user.id,
            validation_ids=[validation.id],
            config=config,
        )

        assert count == 2

        # Check that CSV contains correct accounts
        # SKR03: 8400 for 19%, 8300 for 7%
        assert "8400" in csv_content  # 19% revenue account
        assert "8300" in csv_content  # 7% revenue account

        # Check BU-Schluessel
        assert ";9;" in csv_content  # BU-Schluessel 9 for 19%
        assert ";8;" in csv_content  # BU-Schluessel 8 for 7%

    @pytest.mark.asyncio
    async def test_multi_rate_with_zero_percent(
        self, db_session, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test multi-rate export with 0% VAT rate."""
        user, _ = test_steuerberater_user

        validation = ValidationLog(
            id=uuid.uuid4(),
            user_id=user.id,
            file_name="multi_rate_with_zero.xml",
            file_type=FileType.ZUGFERD,
            file_hash="o" * 64,
            file_size_bytes=1000,
            is_valid=True,
            error_count=0,
            warning_count=0,
            info_count=0,
            processing_time_ms=100,
            validator_version="1.0.0",
        )
        db_session.add(validation)
        await db_session.flush()

        vat_breakdown = json.dumps([
            {"rate": "19", "net_amount": "200.00", "vat_amount": "38.00"},
            {"rate": "7", "net_amount": "100.00", "vat_amount": "7.00"},
            {"rate": "0", "net_amount": "50.00", "vat_amount": "0.00"},
        ])
        extracted = ExtractedInvoiceData(
            validation_id=validation.id,
            invoice_number="MULTI-2024-003",
            invoice_date=date(2024, 7, 15),
            net_amount=Decimal("350.00"),
            vat_amount=Decimal("45.00"),
            gross_amount=Decimal("395.00"),
            currency="EUR",
            vat_rate=Decimal("19.00"),
            seller_name="Multi-Rate ZUGFeRD Supplier",
            vat_breakdown=vat_breakdown,
        )
        db_session.add(extracted)
        await db_session.commit()

        service = DATEVExportService(db_session)
        config = DATEVConfig(kontenrahmen=Kontenrahmen.SKR03)

        csv_content, count, total = await service.export_buchungsstapel(
            user_id=user.id,
            validation_ids=[validation.id],
            config=config,
        )

        # Should have 3 bookings (one per VAT rate)
        assert count == 3
        assert total == Decimal("350.00")

        # Check for 0% account (SKR03: 8120)
        assert "8120" in csv_content

    @pytest.mark.asyncio
    async def test_single_rate_fallback(
        self, db_session, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test that single-rate invoice without breakdown still works."""
        user, _ = test_steuerberater_user

        validation = ValidationLog(
            id=uuid.uuid4(),
            user_id=user.id,
            file_name="single_rate_invoice.xml",
            file_type=FileType.XRECHNUNG,
            file_hash="p" * 64,
            file_size_bytes=1000,
            is_valid=True,
            error_count=0,
            warning_count=0,
            info_count=0,
            processing_time_ms=100,
            validator_version="1.0.0",
        )
        db_session.add(validation)
        await db_session.flush()

        # No vat_breakdown - single rate invoice
        extracted = ExtractedInvoiceData(
            validation_id=validation.id,
            invoice_number="SINGLE-2024-001",
            invoice_date=date(2024, 5, 15),
            net_amount=Decimal("1000.00"),
            vat_amount=Decimal("190.00"),
            gross_amount=Decimal("1190.00"),
            currency="EUR",
            vat_rate=Decimal("19.00"),
            seller_name="Single Rate Supplier",
            vat_breakdown=None,  # No breakdown
        )
        db_session.add(extracted)
        await db_session.commit()

        service = DATEVExportService(db_session)
        config = DATEVConfig(kontenrahmen=Kontenrahmen.SKR03)

        csv_content, count, total = await service.export_buchungsstapel(
            user_id=user.id,
            validation_ids=[validation.id],
            config=config,
        )

        # Should have 1 booking using gross amount
        assert count == 1
        assert total == Decimal("1190.00")
        assert "1190,00" in csv_content

    @pytest.mark.asyncio
    async def test_multi_rate_same_invoice_number(
        self, db_session, test_steuerberater_user: tuple[User, str]
    ) -> None:
        """Test that all bookings from same invoice share the same Belegnummer."""
        user, _ = test_steuerberater_user

        validation = ValidationLog(
            id=uuid.uuid4(),
            user_id=user.id,
            file_name="multi_rate_invoice.xml",
            file_type=FileType.XRECHNUNG,
            file_hash="q" * 64,
            file_size_bytes=1000,
            is_valid=True,
            error_count=0,
            warning_count=0,
            info_count=0,
            processing_time_ms=100,
            validator_version="1.0.0",
        )
        db_session.add(validation)
        await db_session.flush()

        vat_breakdown = json.dumps([
            {"rate": "19", "net_amount": "100.00", "vat_amount": "19.00"},
            {"rate": "7", "net_amount": "50.00", "vat_amount": "3.50"},
        ])
        extracted = ExtractedInvoiceData(
            validation_id=validation.id,
            invoice_number="SHARED-BELEG-001",
            invoice_date=date(2024, 8, 1),
            net_amount=Decimal("150.00"),
            vat_amount=Decimal("22.50"),
            gross_amount=Decimal("172.50"),
            currency="EUR",
            vat_rate=Decimal("19.00"),
            seller_name="Multi-Rate Supplier",
            vat_breakdown=vat_breakdown,
        )
        db_session.add(extracted)
        await db_session.commit()

        service = DATEVExportService(db_session)
        config = DATEVConfig(kontenrahmen=Kontenrahmen.SKR03)

        csv_content, count, _ = await service.export_buchungsstapel(
            user_id=user.id,
            validation_ids=[validation.id],
            config=config,
        )

        assert count == 2

        # Invoice number should appear twice (once per booking)
        assert csv_content.count("SHARED-BELEG-001") == 2
