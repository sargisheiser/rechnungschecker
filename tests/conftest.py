"""Pytest configuration and fixtures for the test suite.

Uses per-test database engines to ensure complete isolation and avoid
async connection conflicts between tests.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import date
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.config import get_settings
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.user import PlanType, User


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session with its own engine for each test.

    This ensures complete isolation between tests and avoids async
    connection pool conflicts.
    """
    settings = get_settings()

    # Create a new engine for this test
    engine = create_async_engine(
        str(settings.database_url),
        echo=False,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=3,
    )

    # Create session maker for this engine
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with session_maker() as session:
        yield session

    # Dispose the engine after the test to clean up all connections
    await engine.dispose()


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client with overridden database dependency."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session: AsyncSession) -> tuple[User, str]:
    """Create a real free-tier user in the test database."""
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        email=f"test-free-{unique_id}@example.com",
        password_hash=get_password_hash("testpassword"),
        is_active=True,
        is_verified=True,
        plan=PlanType.FREE,
        usage_reset_date=date.today(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(str(user.id))
    return user, token


@pytest.fixture
async def test_pro_user(db_session: AsyncSession) -> tuple[User, str]:
    """Create a real pro-tier user in the test database."""
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        email=f"test-pro-{unique_id}@example.com",
        password_hash=get_password_hash("testpassword"),
        is_active=True,
        is_verified=True,
        plan=PlanType.PRO,
        usage_reset_date=date.today(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(str(user.id))
    return user, token


@pytest.fixture
async def test_steuerberater_user(db_session: AsyncSession) -> tuple[User, str]:
    """Create a real steuerberater-tier user in the test database."""
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        email=f"test-steuerberater-{unique_id}@example.com",
        password_hash=get_password_hash("testpassword"),
        is_active=True,
        is_verified=True,
        plan=PlanType.STEUERBERATER,
        usage_reset_date=date.today(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(str(user.id))
    return user, token


@pytest.fixture
def fixtures_path() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_xrechnung_valid() -> bytes:
    """Return a valid minimal XRechnung XML for testing."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<ubl:Invoice xmlns:ubl="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
             xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
             xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0</cbc:CustomizationID>
    <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
    <cbc:ID>INV-2024-001</cbc:ID>
    <cbc:IssueDate>2024-01-15</cbc:IssueDate>
    <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
    <cbc:BuyerReference>04011000-12345-67</cbc:BuyerReference>
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyName>
                <cbc:Name>Test Lieferant GmbH</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>Teststrasse 1</cbc:StreetName>
                <cbc:CityName>Berlin</cbc:CityName>
                <cbc:PostalZone>10115</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>DE</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyTaxScheme>
                <cbc:CompanyID>DE123456789</cbc:CompanyID>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
            <cac:Contact>
                <cbc:Telephone>+49 30 12345678</cbc:Telephone>
                <cbc:ElectronicMail>rechnung@test-lieferant.de</cbc:ElectronicMail>
            </cac:Contact>
        </cac:Party>
    </cac:AccountingSupplierParty>
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyName>
                <cbc:Name>Test Kunde GmbH</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>Kundenweg 2</cbc:StreetName>
                <cbc:CityName>Muenchen</cbc:CityName>
                <cbc:PostalZone>80331</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>DE</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
        </cac:Party>
    </cac:AccountingCustomerParty>
    <cac:PaymentMeans>
        <cbc:PaymentMeansCode>58</cbc:PaymentMeansCode>
        <cac:PayeeFinancialAccount>
            <cbc:ID>DE89370400440532013000</cbc:ID>
        </cac:PayeeFinancialAccount>
    </cac:PaymentMeans>
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="EUR">19.00</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="EUR">100.00</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="EUR">19.00</cbc:TaxAmount>
            <cac:TaxCategory>
                <cbc:ID>S</cbc:ID>
                <cbc:Percent>19</cbc:Percent>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
    </cac:TaxTotal>
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="EUR">100.00</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="EUR">100.00</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="EUR">119.00</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="EUR">119.00</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
    <cac:InvoiceLine>
        <cbc:ID>1</cbc:ID>
        <cbc:InvoicedQuantity unitCode="C62">1</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="EUR">100.00</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Name>Testprodukt</cbc:Name>
            <cac:ClassifiedTaxCategory>
                <cbc:ID>S</cbc:ID>
                <cbc:Percent>19</cbc:Percent>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:ClassifiedTaxCategory>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="EUR">100.00</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
</ubl:Invoice>"""


@pytest.fixture
def sample_xrechnung_invalid() -> bytes:
    """Return an invalid XRechnung XML (missing required fields)."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<ubl:Invoice xmlns:ubl="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
             xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:ID>INV-2024-002</cbc:ID>
    <cbc:IssueDate>2024-01-15</cbc:IssueDate>
</ubl:Invoice>"""


@pytest.fixture
def sample_invalid_xml() -> bytes:
    """Return invalid XML content."""
    return b"This is not valid XML <unclosed>"


@pytest.fixture
def sample_non_xml() -> bytes:
    """Return non-XML content."""
    return b"Just plain text, not XML at all."
