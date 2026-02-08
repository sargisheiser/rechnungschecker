"""SKR03 and SKR04 Kontenrahmen (chart of accounts) mapping for DATEV export."""

from decimal import Decimal
from typing import NamedTuple

from app.schemas.datev import Kontenrahmen


class AccountMapping(NamedTuple):
    """Account mapping with description."""

    konto: str
    beschreibung: str


# BU-Schluessel (tax codes) for DATEV
# These codes indicate the VAT treatment of the booking
BU_SCHLUESSEL = {
    Decimal("0"): 0,   # No VAT / tax-free
    Decimal("7"): 8,   # 7% reduced VAT rate
    Decimal("19"): 9,  # 19% standard VAT rate
}


# SKR03 Account Mapping
# Standard chart of accounts for small to medium businesses
SKR03_ACCOUNTS = {
    # Debtor accounts (Forderungen aus Lieferungen und Leistungen)
    "debitor": AccountMapping("1400", "Forderungen aus Lieferungen und Leistungen"),
    "debitor_10000": AccountMapping("10000", "Debitor Sammelkonto"),

    # Creditor accounts (Verbindlichkeiten aus Lieferungen und Leistungen)
    "kreditor": AccountMapping("1600", "Verbindlichkeiten aus Lieferungen und Leistungen"),
    "kreditor_70000": AccountMapping("70000", "Kreditor Sammelkonto"),

    # Revenue accounts (Erloese)
    "umsatz_19": AccountMapping("8400", "Erloese 19% USt"),
    "umsatz_7": AccountMapping("8300", "Erloese 7% USt"),
    "umsatz_0": AccountMapping("8120", "Steuerfreie Umsaetze"),
    "umsatz_eu": AccountMapping("8125", "Steuerfreie innergem. Lieferungen"),
    "umsatz_export": AccountMapping("8120", "Steuerfreie Ausfuhrlieferungen"),

    # Expense accounts (for incoming invoices)
    "aufwand_19": AccountMapping("4400", "Bezogene Leistungen 19% VSt"),
    "aufwand_7": AccountMapping("4300", "Wareneingang 7% VSt"),
    "aufwand_0": AccountMapping("4200", "Wareneingang ohne VSt"),

    # Bank accounts
    "bank": AccountMapping("1200", "Bank"),
    "kasse": AccountMapping("1000", "Kasse"),
}


# SKR04 Account Mapping
# Alternative standard chart of accounts
SKR04_ACCOUNTS = {
    # Debtor accounts
    "debitor": AccountMapping("1200", "Forderungen aus Lieferungen und Leistungen"),
    "debitor_10000": AccountMapping("10000", "Debitor Sammelkonto"),

    # Creditor accounts
    "kreditor": AccountMapping("3300", "Verbindlichkeiten aus Lieferungen und Leistungen"),
    "kreditor_70000": AccountMapping("70000", "Kreditor Sammelkonto"),

    # Revenue accounts
    "umsatz_19": AccountMapping("4400", "Erloese 19% USt"),
    "umsatz_7": AccountMapping("4300", "Erloese 7% USt"),
    "umsatz_0": AccountMapping("4120", "Steuerfreie Umsaetze"),
    "umsatz_eu": AccountMapping("4125", "Steuerfreie innergem. Lieferungen"),
    "umsatz_export": AccountMapping("4120", "Steuerfreie Ausfuhrlieferungen"),

    # Expense accounts
    "aufwand_19": AccountMapping("5400", "Bezogene Leistungen 19% VSt"),
    "aufwand_7": AccountMapping("5300", "Wareneingang 7% VSt"),
    "aufwand_0": AccountMapping("5200", "Wareneingang ohne VSt"),

    # Bank accounts
    "bank": AccountMapping("1800", "Bank"),
    "kasse": AccountMapping("1600", "Kasse"),
}


def get_accounts(kontenrahmen: Kontenrahmen) -> dict[str, AccountMapping]:
    """Get account mapping for the specified Kontenrahmen."""
    if kontenrahmen == Kontenrahmen.SKR04:
        return SKR04_ACCOUNTS
    return SKR03_ACCOUNTS  # Default to SKR03


def get_bu_schluessel(vat_rate: Decimal) -> int:
    """Get DATEV BU-Schluessel for a VAT rate.

    Args:
        vat_rate: VAT rate as decimal (e.g., Decimal("19") for 19%)

    Returns:
        BU-Schluessel code (0, 8, or 9)
    """
    # Normalize to integer representation
    rate_int = int(vat_rate)

    if rate_int == 19:
        return 9  # Standard rate
    elif rate_int == 7:
        return 8  # Reduced rate
    else:
        return 0  # No tax / other


def get_revenue_account(
    kontenrahmen: Kontenrahmen,
    vat_rate: Decimal,
    is_eu_delivery: bool = False,
    is_export: bool = False,
) -> AccountMapping:
    """Get the appropriate revenue account based on VAT rate and delivery type.

    Args:
        kontenrahmen: Chart of accounts to use
        vat_rate: VAT rate as decimal
        is_eu_delivery: True if intra-EU delivery
        is_export: True if export outside EU

    Returns:
        Account mapping for the revenue account
    """
    accounts = get_accounts(kontenrahmen)
    rate_int = int(vat_rate)

    if is_eu_delivery:
        return accounts["umsatz_eu"]
    elif is_export:
        return accounts["umsatz_export"]
    elif rate_int == 19:
        return accounts["umsatz_19"]
    elif rate_int == 7:
        return accounts["umsatz_7"]
    else:
        return accounts["umsatz_0"]


def get_expense_account(
    kontenrahmen: Kontenrahmen,
    vat_rate: Decimal,
) -> AccountMapping:
    """Get the appropriate expense account based on VAT rate.

    Args:
        kontenrahmen: Chart of accounts to use
        vat_rate: VAT rate as decimal

    Returns:
        Account mapping for the expense account
    """
    accounts = get_accounts(kontenrahmen)
    rate_int = int(vat_rate)

    if rate_int == 19:
        return accounts["aufwand_19"]
    elif rate_int == 7:
        return accounts["aufwand_7"]
    else:
        return accounts["aufwand_0"]


def get_debitor_account(
    kontenrahmen: Kontenrahmen,
    custom_account: str | None = None,
) -> str:
    """Get debtor account number.

    Args:
        kontenrahmen: Chart of accounts to use
        custom_account: Custom account number if provided

    Returns:
        Account number string
    """
    if custom_account:
        return custom_account
    return get_accounts(kontenrahmen)["debitor"].konto


def get_kreditor_account(
    kontenrahmen: Kontenrahmen,
    custom_account: str | None = None,
) -> str:
    """Get creditor account number.

    Args:
        kontenrahmen: Chart of accounts to use
        custom_account: Custom account number if provided

    Returns:
        Account number string
    """
    if custom_account:
        return custom_account
    return get_accounts(kontenrahmen)["kreditor"].konto
